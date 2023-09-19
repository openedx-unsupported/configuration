#!/usr/bin/env bash

set -ex

function write_demo_course_script() {
  cat <<EOF > "$1"
#!/usr/bin/env bash

set -ex

demo_hashed_password='pbkdf2_sha256\$20000\$TjE34FJjc3vv\$0B7GUmH8RwrOc/BvMoxjb5j8EgnWTt3sxorDANeF7Qw='
admin_password='${admin_hashed_password}'

# Clone demo course
mkdir /edx/var/edxapp/data
chmod 777 /edx/var/edxapp/data
git clone https://github.com/openedx/openedx-demo-course.git /edx/app/demo/edx-demo-course

# import demo course
docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e CMS_CFG=/edx/etc/cms.yml -e DJANGO_SETTINGS_MODULE=cms.envs.docker-production -e SERVICE_VARIANT=cms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/cms.yml:/edx/etc/cms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/app/demo:/edx/app/demo -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py cms import /edx/var/edxapp/data /edx/app/demo/edx-demo-course

# Create admin and demo users
docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py lms manage_user edx edx@example.com --initial-password-hash \$admin_password --superuser --staff
for user in honor audit verified staff ; do
  email="\$user@example.com"
  # Set staff flag for staff user
  if [[ \$user == "staff" ]] ; then
    docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py lms manage_user \$user \$email --initial-password-hash \$demo_hashed_password --staff
  else
    docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py lms manage_user \$user \$email --initial-password-hash \$demo_hashed_password
  fi
  # Enroll users in the demo course
  docker run --network=host --rm -u='www-data' -e NO_PREREQ_INSTALL="1" -e SKIP_WS_MIGRATIONS="1" -e LMS_CFG=/edx/etc/lms.yml -e DJANGO_SETTINGS_MODULE=lms.envs.docker-production -e SERVICE_VARIANT=lms -e EDX_PLATFORM_SETTINGS=docker-production -v /edx/etc/lms.yml:/edx/etc/lms.yml -v /edx/var/edx-themes:/edx/var/edx-themes -v /edx/var/edxapp:/edx/var/edxapp -v /var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock ${app_repo}:latest python3 manage.py lms enroll_user_in_course -e \$email -c course-v1:edX+DemoX+Demo_Course
done
EOF
}
