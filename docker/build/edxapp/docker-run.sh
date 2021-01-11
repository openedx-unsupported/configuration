#!/bin/bash
set -e

# fix individual packages
monkey_patch () {
  /edx/bin/pip.edxapp install Mako==1.1.3
}

# helper function to start a service (LMS or CMS)
start_service () {
  # start supervisor in foreground and with the current environment loaded
  sudo -Eu www-data \
    /edx/app/supervisor/venvs/supervisor/bin/supervisord \
      --nodaemon \
      --configuration /edx/app/supervisor/supervisord.conf
}

# helper function that waits for the MySQL database to come up
wait_for_mysql () {
  export SERVICE_VARIANT=$1

  /edx/bin/edxapp-shell-lms - <<EOF
import time
from django.db import connections
from django.db.utils import OperationalError

while True:
    try:
        db_conn = connections['default']
        c = db_conn.cursor()
    except OperationalError as e:
        if e[0] == 2003:
            print("Waiting for MySQL to start...")
            time.sleep(2)
            continue
        else:
            raise e
    else:
        print("MySQL is up!")
        break
EOF
}

create_oauth2_client () {
  local name=$1; shift;
  local url_callback=$1; shift;
  local client_id=$1; shift;
  local client_secret=$1; shift;
  local scopes=$1; shift;

  local edxpython="/edx/bin/python.edxapp"
  local manage="/edx/bin/manage.edxapp"

  echo "Creating OAuth2 client for ${name}..."
  source /edx/app/edxapp/edxapp_env
  $edxpython $manage lms --settings=bdu manage_user "${name}_worker" "${name}_worker@skillsnetwork.site" --staff --superuser
  $edxpython $manage lms create_dot_application \
    --redirect-uris="${url_callback}" \
    --grant-type=authorization-code \
    --skip-authorization \
    --settings=bdu \
    --client-id="${client_id}" \
    --client-secret="${client_secret}" \
    --scopes="${scopes}" \
    "${name}" "${name}_worker" > /dev/null
  echo "Done."
}

create_oauth2_client_service_account () {
  local name=$1; shift;
  local client_id=$1; shift;
  local username=$1; shift;

  local edxpython="/edx/bin/python.edxapp"
  local manage="/edx/bin/manage.edxapp"

  echo "Creating OAuth2 client for ${name}..."
  source /edx/app/edxapp/edxapp_env
  $edxpython $manage lms create_dot_application \
    --settings=bdu \
    --grant-type=password \
    --client-id="${client_id}" \
    --public \
    "${name}" "${username}" > /dev/null
  echo "Done."
}

run_command () {
  # extract the first 3 characters to find the appropriate service (lms or cms)
  local service=${1:0:3}
  [[ ${1:3} == "-workers" ]] && local workers=true

  # run edxapp playbook to setup config files
  cd /edx/app/edx_ansible/edx_ansible/docker/plays

  if [[ -z "$RELEASE_NAME" ]]; then
    /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook \
        edxapp-run.yml \
        -i '127.0.0.1,' -c local \
        -e "{\"service_variants_enabled\": [\"${service}\"]}" \
        ${workers:+ -e "celery_worker=true"} \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/edxapp/vars/run.yml \
        -e@/edx/etc/edxapp/ansible_overrides.yml \
        -t "run:prod"
  else
    /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook \
        edxapp-run.yml \
        -i '127.0.0.1,' -c local \
        -e "{\"service_variants_enabled\": [\"${service}\"]}" \
        ${workers:+ -e "celery_worker=true"} \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/edxapp/vars/run.yml \
        -e@/edx/app/edx_ansible/edx_ansible/docker/build/edxapp/vars/k8s.yml \
        -e@/edx/etc/edxapp/ansible_overrides.yml \
        --extra-vars release_name=${RELEASE_NAME} \
        -t "run:prod"
  fi

  case $1 in
    lms|cms|lms-workers|cms-workers)
      echo "Starting ${service}..."
      start_service $service
    ;;

    lms-fake-migrate|cms-fake-migrate)
      echo "Fake migrating ${service}..."
      wait_for_mysql $service
      source /edx/app/edxapp/edxapp_env
      local edxpython="/edx/bin/python.edxapp"
      local manage="/edx/bin/manage.edxapp"
      eval "${edxpython} ${manage} ${service} migrate --fake-initial --settings=bdu ${FAKE_MIGRATION_APP:-thumbnail}"
    ;;

    lms-dark-lang-config)
      echo "Adding dark lang configuration"
      wait_for_mysql $service
      source /edx/app/edxapp/edxapp_env
      local edxpython="/edx/bin/python.edxapp"
      local manage="/edx/bin/manage.edxapp"
      eval "${edxpython} ${manage} ${service} --settings=bdu add_dark_lang_config --langs ${DARK_LANGS:-en,fr,zh-cn,es-419,uk,ru,pt-br,it-it}"
    ;;

    lms-migrate|cms-migrate)
      echo "Migrating ${service}..."
      wait_for_mysql $service
      eval "/edx/bin/edxapp-migrate-${service}"
    ;;

    lms-assets|cms-assets)
      echo "Compiling assets for ${service}..."
      wait_for_mysql $service
      eval "/edx/bin/edxapp-update-assets"
    ;;

    lms-config|cms-config)
      echo "${service} configuration file generated."
    ;;

    lms-init)
      echo "Initiating certificates, admin account and OAuth clients for ${service}..."
      wait_for_mysql $service

      # Enable certificates
      echo "Enabling certificates..."
      /edx/bin/edxapp-shell-lms < /edx/app/edx_ansible/edx_ansible/docker/build/edxapp/enable_certificates.py > /dev/null

      # Create admin user
      echo "Creating Admin user..."
      /edx/bin/edxapp-shell-lms < /edx/app/edx_ansible/edx_ansible/docker/build/edxapp/create_admin.py > /dev/null

      echo "Enabling bulk instructor emails"
      /edx/bin/edxapp-shell-lms < /edx/app/edx_ansible/edx_ansible/docker/build/edxapp/enable_bulk_instructor_email.py > /dev/null

      if [[ "$DISABLE_PERSISTENT_GRADES" != "true" ]]; then
        echo "Enabling persistent course grades"
        /edx/bin/edxapp-shell-lms < /edx/app/edx_ansible/edx_ansible/docker/build/edxapp/enable_persistent_grades.py > /dev/null
      fi

      # Create OAuth clients
      create_oauth2_client "Portal" "https://${BDU_PORTAL_HOSTNAME}/auth/open_edx/callback" "${OPENEDX_CLIENT_ID}" "${OPENEDX_CLIENT_SECRET}" "user_id,profile,email"
      create_oauth2_client "CC Labs" "https://${BDU_LABS_HOSTNAME}/${BDU_LABS_OAUTH2_PROVIDER}/callback" "${OPENEDX_LABS_CLIENT_ID}" "${OPENEDX_LABS_CLIENT_SECRET}" "user_id,profile,email"
      create_oauth2_client "Competitions" "https://${BDU_PORTAL_C3_HOSTNAME}/auth" "${OPENEDX_C3_CLIENT_ID}" "${OPENEDX_C3_CLIENT_SECRET}" "user_id,profile,email"
      if [[ $ANN_HOSTNAME ]]; then
        create_oauth2_client "ANN" "https://${ANN_HOSTNAME}/auth/oauth/callback" "${OPENEDX_ANN_CLIENT_ID}" "${OPENEDX_ANN_CLIENT_SECRET}" "user_id,profile,email"
      fi
      create_oauth2_client_service_account "glados_service" "glados_service" "Portal_worker"
    ;;

    help|*)
      echo ""
      echo "This image can be run in several different scenarios, depending on"
      echo "which command is issue when running it. For example, the command"
      echo "will start the LMS application:"
      echo ""
      echo "  docker run bdu/edxapp:eucalyptus.2 lms"
      echo ""
      echo "The available commands are as follow:"
      echo ""
      echo "Available commands:"
      echo "  cms         - Start the CMS app."
      echo "  cms-assets  - Pre-compile CMS assets."
      echo "  cms-config  - Run Ansible playbook to configure CMS but don't start any process."
      echo "  cms-migrate - Run LMS database migrations."
      echo "  cms-workers - Start CMS workers."
      echo "  lms         - Start the LMS app."
      echo "  lms-assets  - Pre-compile LMS assets."
      echo "  lms-config  - Run Ansible playbook to configure LMS but don't start any process."
      echo "  lms-init    - Create Django Admin account and OAuth2 clients for portal applications."
      echo "  lms-migrate - Run LMS database migrations."
      echo "  lms-workers - Start LMS workers."
      echo ""
    ;;
  esac

}

# make sure rsyslogd is running, otherwise we'll get a Django error
if ! pgrep "rsyslogd" > /dev/null; then
  rm -f /var/run/rsyslogd.pid
  /usr/sbin/rsyslogd
fi

# Fix theme directory ownership
mkdir -p /edx/var/edxapp/themes

# We add '|| true' to the lines below so that the container can start even if these files don't exist yet
ls /edx/var/edxapp | grep -v "staticfiles" | grep -v "themes" | awk '{ print "/edx/var/edxapp/"$1 }' | xargs chown -R www-data:www-data || true
chown -R www-data:www-data /edx/var/log/supervisor/supervisord.log || true
chown -R edxapp:www-data /edx/var/edxapp/themes || true
chown -R edxapp:www-data /edx/var/edx-themes || true
chown -R edxapp:edxapp /edx/var/edxapp/staticfiles || true

monkey_patch

for cmd in "$@"; do
  run_command $cmd
done
