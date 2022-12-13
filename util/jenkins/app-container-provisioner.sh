#!/usr/bin/env bash

set -ex

function write_app_deployment_script() {
  cat <<EOF > "$1"
#!/usr/bin/env bash

set -ex

# Install yq for yaml processing
wget https://github.com/mikefarah/yq/releases/download/v4.27.5/yq_linux_amd64  -O /usr/bin/yq && chmod +x /usr/bin/yq

chown :www-data /var/tmp/${app_service_name}.yml

# Create app staticfiles dir
mkdir /edx/var/${app_name}/staticfiles/ -p && chmod 777 /edx/var/${app_name} -R

git clone https://github.com/edx/${app_repo}.git /edx/app/${app_name}/${app_repo}
cd /edx/app/${app_name}/${app_repo} && git checkout ${app_version}

# Generate container image if it doesn't already exist
if ! $(docker image inspect ${app_image_name} >/dev/null 2>&1 && echo true || echo false) ; then
    cd /edx/app/${app_name}/${app_repo}
    export DOCKER_BUILDKIT=1
    if [[ ${app_service_name} == 'lms' ]]; then
        docker build . -t ${app_repo}:latest --target base
    else
        docker build . -t ${app_repo}:latest
    fi
fi

if [[ ${app_service_name} == 'lms' ]]; then # if lms, create image (if it doesn't exist) and generate JWT credentials
    touch /tmp/lms_jwt_signature.yml && chmod 777 /tmp/lms_jwt_signature.yml
    # generate JWT token, ensure JWT file is mounted as volume
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /tmp/lms_jwt_signature.yml:/tmp/lms_jwt_signature.yml -v /var/tmp/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes/edx-themes/edx-platform:/edx/var/edx-themes/edx-themes/edx-platform ${app_repo}:latest python3 manage.py lms generate_jwt_signing_key --output-file /tmp/lms_jwt_signature.yml --strip-key-prefix
fi

# Combine app config with jwt_signature config
cat /var/tmp/${app_service_name}.yml /tmp/lms_jwt_signature.yml > /edx/etc/${app_service_name}.yml

chown :www-data /edx/etc/${app_service_name}.yml

# create DB
mysql -u root -e "CREATE DATABASE edxapp;"
# create DB users
mysql -u root -e "GRANT ALL PRIVILEGES ON edxapp.* TO 'edxapp001'@'localhost' IDENTIFIED BY 'password';"

if [[ ${app_service_name} == 'lms' ]]; then # if lms, perform extra LMS tasks
    # run lms migrations
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes/edx-themes/edx-platform:/edx/var/edx-themes/edx-themes/edx-platform -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py lms showmigrations --database default
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes/edx-themes/edx-platform:/edx/var/edx-themes/edx-themes/edx-platform -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py lms migrate --database default --noinput
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes/edx-themes/edx-platform:/edx/var/edx-themes/edx-themes/edx-platform -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py lms showmigrations --database student_module_history
    docker run --network=host --rm -u='www-data' -e LMS_CFG=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes/edx-themes/edx-platform:/edx/var/edx-themes/edx-themes/edx-platform -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py lms migrate --database student_module_history --noinput
    # generate static assets
    docker run --network=host --rm -u='root' -e GEN_LOG_DIR=/tmp -e LMS_CFG=/edx/etc/${app_service_name}.yml -e DJANGO_SETTINGS_MODULE=${app_service_name}.envs.docker-production -e SERVICE_VARIANT=${app_service_name} -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/${app_service_name}.yml:/edx/etc/${app_service_name}.yml -v /edx/var/edx-themes/edx-themes/edx-platform:/edx/var/edx-themes/edx-themes/edx-platform -v /edx/var/${app_name}:/edx/var/${app_name}  -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest paver update_assets --debug-collect
fi

if [[ ${app_service_name} != 'lms' ]]; then # if not lms, do these things
    # Provision IDA User in LMS
    source /edx/app/edxapp/edxapp_env && python /edx/app/edxapp/edx-platform/manage.py lms --settings=production manage_user ${app_service_name}_worker ${app_service_name}_worker@example.com --staff --superuser

    # Create the DOT applications - one for single sign-on and one for backend service IDA-to-IDA authentication.
    source /edx/app/edxapp/edxapp_env && python /edx/app/edxapp/edx-platform/manage.py lms --settings=production create_dot_application --grant-type authorization-code --skip-authorization --redirect-uris 'https://${app_hostname}-${dns_name}.${dns_zone}/complete/edx-oauth2/' --client-id '${app_service_name}-sso-key' --client-secret '${app_service_name}-sso-secret' --scopes 'user_id' ${app_service_name}-sso ${app_service_name}_worker
    source /edx/app/edxapp/edxapp_env && python /edx/app/edxapp/edx-platform/manage.py lms --settings=production create_dot_application --grant-type client-credentials --client-id '${app_service_name}-backend-service-key' --client-secret '${app_service_name}-backend-service-secret' ${app_service_name}-backend-service ${app_service_name}_worker
fi

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
