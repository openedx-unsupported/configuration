#!/usr/bin/env bash

set -ex

function write_demo_course_script() {
  cat <<EOF > "$1"
#!/usr/bin/env bash

set -ex

# import demo course
docker exec -t cms bash -c "python3 manage.py cms --settings=docker-production import /edx/app/edxapp/data /edx/app/demo/edx-demo-course"

# create staff user and enroll
docker exec -t lms bash -c "python3 manage.py lms --settings=docker-production --service-variant lms manage_user staff staff@example.com --initial-password-hash \\\\"pbkdf2_sha256$20000$TjE34FJjc3vv$0B7GUmH8RwrOc/BvMoxjb5j8EgnWTt3sxorDANeF7Qw=\\\\" --staff && python3 manage.py lms --settings=docker-production --service-variant lms enroll_user_in_course -e staff@example.com -c course-v1:edX+DemoX+Demo_Course"

# create honor user and enroll
docker exec -t lms bash -c "python3 manage.py lms --settings=docker-production --service-variant lms manage_user honor honor@example.com --initial-password-hash \\\\"pbkdf2_sha256$20000$TjE34FJjc3vv$0B7GUmH8RwrOc/BvMoxjb5j8EgnWTt3sxorDANeF7Qw=\\\\" && python3 manage.py lms --settings=docker-production --service-variant lms enroll_user_in_course -e honor@example.com -c course-v1:edX+DemoX+Demo_Course"

# create audit user and enroll
docker exec -t lms bash -c "python3 manage.py lms --settings=docker-production --service-variant lms manage_user audit audit@example.com --initial-password-hash \\\\"pbkdf2_sha256$20000$TjE34FJjc3vv$0B7GUmH8RwrOc/BvMoxjb5j8EgnWTt3sxorDANeF7Qw=\\\\" && python3 manage.py lms --settings=docker-production --service-variant lms enroll_user_in_course -e audit@example.com -c course-v1:edX+DemoX+Demo_Course"

# create verified user and enroll
docker exec -t lms bash -c "python3 manage.py lms --settings=docker-production --service-variant lms manage_user verified verified@example.com --initial-password-hash \\\\"pbkdf2_sha256$20000$TjE34FJjc3vv$0B7GUmH8RwrOc/BvMoxjb5j8EgnWTt3sxorDANeF7Qw=\\\\" && python3 manage.py lms --settings=docker-production --service-variant lms enroll_user_in_course -e verified@example.com -c course-v1:edX+DemoX+Demo_Course"

# create admin user
docker exec -t lms bash -c "python3 manage.py lms --settings=docker-production --service-variant lms manage_user admin admin@example.com --initial-password-hash \\\\"${app_admin_password}\\\\" --staff --superuser"

# seed forums
docker exec -t lms bash -c "python3 manage.py lms --settings=docker-production --service-variant lms seed_permission_roles course-v1:edX+DemoX+Demo_Course"

EOF
}
