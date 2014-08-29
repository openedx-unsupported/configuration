#!/bin/bash

cd configuration
pip install -r requirements.txt
env

ip=$(python playbooks/ec2.py | jq -r '."tag_Name_prod-edge-worker"[0] | strings')
ssh="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
manage="cd /edx/app/edxapp/edx-platform && sudo -u www-data /edx/bin/python.edxapp ./manage.py"

if [ "$report" = "true" ]; then
  $ssh ubuntu@"$ip" "$manage lms gen_cert_report -c $course_id --settings aws"
elif [ "$regenerate" = "true" ] ; then
    $ssh ubuntu@"$ip" "$manage lms regenerate_user -c $course_id -u $username --settings aws"
  else
    $ssh ubuntu@"$ip" "$manage lms ungenerated_certs -c $course_id --settings aws"
  if [ "$force_certificate_state" ]; then
    $ssh ubuntu@"$ip" "$manage lms ungenerated_certs -c $course_id -f $force_certificate_state --settings aws"
  fi
fi
