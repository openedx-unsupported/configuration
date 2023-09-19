#!/usr/bin/env bash

set -ex

function write_app_deployment_script() {
  cat <<EOF > "$1"
#!/usr/bin/env bash

set -ex

# Install yq for yaml processing
wget https://github.com/mikefarah/yq/releases/download/v4.27.5/yq_linux_amd64 -O /usr/bin/yq && chmod +x /usr/bin/yq

chown :www-data /var/tmp/${app_service_name}.yml

if [[ ${app_service_name} == 'lms' ]] ; then
    chown :www-data /var/tmp/cms.yml
fi

if [[ ${app_service_name} != 'cms' && ${app_service_name} != 'lms' ]] ; then
    # Create app staticfiles dir
    mkdir /edx/var/${app_service_name}/staticfiles/ -p && chmod 777 /edx/var/${app_service_name} -R
fi

# if application is lms, download and setup themes
if [[ ${app_service_name} == 'lms' && ! -d /edx/var/edx-themes ]] ; then
    set +x
    echo -e "${app_git_ssh_key}" > /tmp/theme_ssh_key
    set -x
    chmod 0600 /tmp/theme_ssh_key
    useradd -m -d /edx/var/edx-themes edx-themes -G www-data
    GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /tmp/theme_ssh_key" git clone git@github.com:edx/edx-themes.git /edx/var/edx-themes/edx-themes
    cd /edx/var/edx-themes/edx-themes && git checkout ${themes_version}
    chown -R edx-themes:www-data /edx/var/edx-themes
    sudo -u edx-themes git config --global safe.directory '/edx/var/edx-themes/edx-themes'
    rm -rf /tmp/theme_ssh_key
fi

# checkout git repo
if [ ! -d "/edx/app/${app_name}" ]; then
  mkdir /edx/app/${app_name}
fi

if [[ ! -d "/edx/app/${app_name}/${app_repo}" ]] ; then

    # use SSH to clone if repo is private
    if [[ "$app_repo_is_private" = true ]] ; then
        set +x
        echo -e "${app_git_ssh_key}" > /tmp/${app_service_name}_ssh_key
        set -x
        chmod 0600 /tmp/${app_service_name}_ssh_key
        useradd -m -d /edx/var/${app_service_name} ${app_service_name} -G www-data
        GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /tmp/${app_service_name}_ssh_key" git clone git@github.com:edx/${app_repo}.git /edx/app/${app_name}/${app_repo}
    else
        git clone https://github.com/edx/${app_repo}.git /edx/app/${app_name}/${app_repo}
    fi
    cd /edx/app/${app_name}/${app_repo} && git checkout ${app_version}
fi

# Generate container image if it doesn't already exist
if ! $(docker image inspect ${app_image_name} >/dev/null 2>&1 && echo true || echo false) ; then
    cd /edx/app/${app_name}/${app_repo}
    export DOCKER_BUILDKIT=1
    if [[ ${app_service_name} == 'lms' || ${app_service_name} == 'cms' ]]; then
        docker build . -t ${app_repo}:base --target base
        cd /var/tmp/edx-platform-private
        docker build . --build-arg BASE_IMAGE=${app_repo} --build-arg BASE_TAG=base -t ${app_repo}:latest
    else
        docker build . -t ${app_repo}:latest
    fi
fi

# if lms, create image (if it doesn't exist) and generate JWT credentials
if [[ ${app_service_name} == 'lms' ]]; then
    touch /tmp/lms_jwt_signature.yml && chmod 777 /tmp/lms_jwt_signature.yml
    # generate JWT token, ensure JWT file is mounted as volume
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /tmp/lms_jwt_signature.yml:/tmp/lms_jwt_signature.yml -v /var/tmp/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes:/edx/var/edx-themes ${app_repo}:latest python3 manage.py lms generate_jwt_signing_key --output-file /tmp/lms_jwt_signature.yml --strip-key-prefix
fi

# Combine app config with jwt_signature config
cat /var/tmp/${app_service_name}.yml /tmp/lms_jwt_signature.yml > /edx/etc/${app_service_name}.yml

chown :www-data /edx/etc/${app_service_name}.yml

if [[ ${app_service_name} == 'lms' || ${app_service_name} == 'cms' ]]; then
    # run migrations
    docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e ${app_cfg}=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py ${app_service_name} showmigrations --database default
    docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e ${app_cfg}=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py ${app_service_name} migrate --database default --noinput
    docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e ${app_cfg}=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py ${app_service_name} showmigrations --database student_module_history
    docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e ${app_cfg}=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py ${app_service_name} migrate --database student_module_history --noinput
else
    # Run app migrations
    docker run --network=host --rm -u='www-data' -e ${app_cfg}=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.settings.production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/${app_name}:/edx/var/${app_name} -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py migrate
    # Generate static assets
    docker run --network=host --rm -u='root' -e ${app_cfg}=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.settings.production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/${app_service_name}/staticfiles/:/var/tmp/ -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py collectstatic --noinput
fi

# Setup oauth clients for service other than CMS as part of the LMS setup
if [[ ${app_service_name} == 'lms' ]]; then
    service_worker_users=(enterprise veda discovery credentials insights registrar designer license_manager commerce_coordinator enterprise_catalog ecommerce retirement edx_exams subscriptions)
    # Provision IDA User in LMS
    for service_worker in "\${service_worker_users[@]}"; do
      app_hostname=\${service_worker/_/-}
      docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock edx-platform:latest python3 manage.py lms manage_user \${service_worker}_worker \${service_worker}_worker@example.com --staff --superuser

      # Create the DOT applications - one for single sign-on and one for backend service IDA-to-IDA authentication.
      docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock edx-platform:latest python3 manage.py lms create_dot_application --grant-type authorization-code --skip-authorization --redirect-uris "https://\${app_hostname}-${dns_name}.${dns_zone}/complete/edx-oauth2/" --client-id "\${service_worker}-sso-key" --client-secret "\${service_worker}-sso-secret" --scopes 'user_id' \${service_worker}-sso \${service_worker}_worker
      docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock edx-platform:latest python3 manage.py lms create_dot_application --grant-type client-credentials --client-id "\${service_worker}-backend-service-key" --client-secret "\${service_worker}-backend-service-secret" \${service_worker}-backend-service \${service_worker}_worker
    done
fi

# oauth client setup
if [[ ${app_service_name} != 'lms' && ${edxapp_container_enabled} == 'true' ]]; then
    # Provision IDA User in LMS
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock edx-platform:latest python3 manage.py lms manage_user $(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}_; fi)${app_service_name}_worker $(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}_; fi)${app_service_name}_worker@example.com --staff --superuser

    # Create the DOT applications - one for single sign-on and one for backend service IDA-to-IDA authentication.
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock edx-platform:latest python3 manage.py lms create_dot_application --grant-type authorization-code --skip-authorization --redirect-uris 'https://${app_hostname}-${dns_name}.${dns_zone}/complete/edx-oauth2/' --client-id '$(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}-; fi)${app_service_name}-sso-key' --client-secret '$(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}-; fi)${app_service_name}-sso-secret' --scopes 'user_id' $(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}-; fi)${app_service_name}-sso $(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}_; fi)${app_service_name}_worker
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock edx-platform:latest python3 manage.py lms create_dot_application --grant-type client-credentials --client-id '$(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}-; fi)${app_service_name}-backend-service-key' --client-secret '$(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}-; fi)${app_service_name}-backend-service-secret' $(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}-; fi)${app_service_name}-backend-service $(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}_; fi)${app_service_name}_worker
fi

# generate lms/cms static assets
if [[ ${app_service_name} == 'lms' ]]; then
    # temporary hack, create npm-install.log file
    touch /edx/app/edxapp/edx-platform/test_root/log/npm-install.log
    docker run --network=host --rm -u='root' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e LMS_CFG=/edx/etc/${app_service_name}.yml -e CMS_CFG=/edx/etc/cms.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /var/tmp/cms.yml:/edx/etc/cms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/${app_name}:/edx/var/${app_name} -v /edx/app/edxapp/edx-platform/test_root/log/npm-install.log:/edx/app/edxapp/edx-platform/test_root/log/npm-install.log -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest paver update_assets --debug-collect --settings=docker-production
fi

# Generate docker-compose file for app service
cat <<EOT > /home/$github_username/docker-compose-${app_service_name}.yml
version: "3.9"
services:
  ${app_service_name}:
    image: ${app_repo}:latest
    stdin_open: true
    tty: true
    container_name: ${app_service_name}
    command: bash -c "gunicorn --workers=2 --name ${app_service_name} -c /edx/app/$(if [[ ${app_name} == 'edxapp' ]]; then echo ${app_name}/; fi)${app_repo}/${app_service_name}/$(if [[ ${app_name} == 'edxapp' ]]; then echo docker_${app_service_name}_gunicorn.py; else echo docker_gunicorn_configuration.py; fi) --log-file - --max-requests=1000 ${app_service_name}.wsgi:application"
    user: "www-data:www-data"
    network_mode: 'host'
    restart: on-failure
    environment:
      - EDX_REST_API_CLIENT_NAME=sandbox-edx-${app_service_name}
$(
  if [[ ${app_service_name} == 'lms' || ${app_service_name} == 'cms' ]]; then
    echo -e "      - DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production"
    echo -e "      - EDX_PLATFORM_SETTINGS=docker-production"
    echo -e "      - SERVICE_VARIANT=${app_service_name}"
    echo -e "      - ${app_cfg}=/edx/etc/${app_service_name}.yml"
  else
    echo -e "      - DJANGO_SETTINGS_MODULE=${app_service_name}.settings.production"
    echo -e "      - ${app_cfg}=/${app_service_name}.yml"
  fi
)
    volumes:
      - /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock
$(
  if [[ ${app_service_name} == 'lms' || ${app_service_name} == 'cms' ]]; then
    echo -e "      - /edx/var/${app_name}:/edx/var/${app_name}"
    echo -e "      - /edx/var/edx-themes:/edx/var/edx-themes"
    echo -e "      - /var/tmp/tracking_logs.log:/var/tmp/tracking_logs.log"
    echo -e "      - /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml"
  else
    echo -e "      - /edx/var/${app_service_name}/staticfiles/:/var/tmp/"
    echo -e "      - /edx/etc/${app_service_name}.yml:/${app_service_name}.yml"
  fi
)
$(
  if [[ ${app_service_name} == 'cms' ]]; then
    echo -e "      - /edx/app/demo:/edx/app/demo"
  fi
)
EOT

docker-compose -f /home/$github_username/docker-compose-${app_service_name}.yml up -d

EOF







#    # Create app database
#    echo "mysql -uroot -e \"CREATE DATABASE \\\`${app_service_name}\\\`;\""
#
#    # use heredoc to dynamically create docker compose file
#    echo "docker_compose_file=/var/tmp/docker-compose-${app_service_name}.yml"
#    echo "cat << 'EOF' > \$docker_compose_file
#    version: '2.1'
#    services:
#      app:
#        image: ${app_service_name}:latest
#        stdin_open: true
#        tty: true
#        build:
#          context: /edx/app/${app_repo}
#          dockerfile: Dockerfile
#        container_name: ${app_service_name}.app
#        command: bash -c 'while true; do exec gunicorn --workers=2 --name ${app_service_name} -c /edx/app/${app_repo}/${app_service_name}/docker_gunicorn_configuration.py --log-file - --max-requests=1000 ${app_service_name}.wsgi:application; sleep 2; done'
#        network_mode: 'host'
#        environment:
#          DJANGO_SETTINGS_MODULE: ${app_service_name}.settings.production
#          DJANGO_WATCHMAN_TIMEOUT: 30
#          ENABLE_DJANGO_TOOLBAR: 1
#          ${app_cfg}: /${app_service_name}.yml
#        volumes:
#          - /edx/app/${app_repo}:/edx/app/${app_repo}/
#          - /edx/etc/${app_service_name}.yml:/${app_service_name}.yml
#          - /edx/var/${app_service_name}/staticfiles/:/var/tmp/
#EOF"
#
#    # run docker compose to spin up service container
#    echo "docker-compose -f \$docker_compose_file up -d"
#
#    # Wait for app container
#    echo "sleep 5"
#
#    # Run migrations
#    echo "docker exec -t ${app_service_name}.app bash -c \"python3 manage.py migrate\""
#
#    # Run collectstatic
#    echo "docker exec -t ${app_service_name}.app bash -c \"python3 manage.py collectstatic --noinput\""
#     # Create superuser
#    echo "docker exec -t ${app_service_name}.app bash -c \"echo 'from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(\\\"edx\\\", \\\"edx@example.com\\\", \\\"edx\\\") if not User.objects.filter(username=\\\"edx\\\").exists() else None' | python /edx/app/${app_repo}/manage.py shell\""
#
#    # Create Nginx config
#    echo "site_config=/edx/app/nginx/sites-available/${app_service_name}"
#    echo "cat << 'EOF' > \$site_config
#    server {
#       server_name ~^((stage|prod)-)?${app_hostname}.*;
#       listen 80;
#       rewrite ^ https://\$host\$request_uri? permanent;
#     }
#     server {
#       server_name ~^((stage|prod)-)?${app_hostname}.*;
#       listen 443 ssl;
#       ssl_certificate /etc/ssl/certs/wildcard.sandbox.edx.org.pem;
#       ssl_certificate_key /etc/ssl/private/wildcard.sandbox.edx.org.key;
#
#       location / {
#         try_files \$uri @proxy_to_app;
#       }
#       location ~ ^/(api)/ {
#          try_files \$uri @proxy_to_app;
#       }
#       location @proxy_to_app {
#          proxy_set_header X-Forwarded-Proto \$scheme;
#          proxy_set_header X-Forwarded-Port \$server_port;
#          proxy_set_header X-Forwarded-For \$remote_addr;
#          proxy_set_header Host \$http_host;
#          proxy_redirect off;
#          proxy_pass http://127.0.0.1:${app_gunicorn_port};
#       }
#       location ~ ^/static/(?P<file>.*) {
#         root /edx/var/${app_service_name};
#         try_files /staticfiles/\$file =404;
#       }
#     }
#EOF"
#     echo "ln -s  /edx/app/nginx/sites-available/${app_service_name} /etc/nginx/sites-enabled/${app_service_name}"
#     echo "service nginx reload"
}
