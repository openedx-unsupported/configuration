#!/bin/bash

cd configuration
pip install -r requirements.txt
env

ip=`python playbooks/ec2.py | jq -r '."tag_Name_prod-edx-worker"[0] | strings'`

if [ "$report" = "true" ]; then
  ssh ubuntu@$ip "cd /edx/app/edxapp/edx-platform && sudo -u www-data /edx/bin/python.edxapp ./manage.py lms gen_cert_report -c $course_id --settings aws"
else
  ssh ubuntu@$ip "cd /edx/app/edxapp/edx-platform && sudo -u www-data /edx/bin/python.edxapp ./manage.py lms ungenerated_certs -c $course_id --settings aws"
  if [ ! -z "$force_certificate_state" ]; then
    ssh ubuntu@$ip "cd /edx/app/edxapp/edx-platform && sudo -u www-data /edx/bin/python.edxapp ./manage.py lms ungenerated_certs -c $course_id -f $force_certificate_state --settings aws"
  fi
fi
