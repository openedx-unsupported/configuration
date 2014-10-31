#!/bin/bash

cd configuration
pip install -r requirements.txt
env

ansible="ansible first_in_tag_Name_${environment}-${deployment}-worker -i playbooks/ec2.py -u ubuntu -s -U www-data -m shell -a"
manage="/edx/bin/python.edxapp /edx/bin/manage.edxapp lms --settings aws"

if [ "$report" = "true" ]; then
  $ansible "$manage gen_cert_report -c $course_id" | grep -A2 "Looking up certificate states for" | sed 's/rm:.*//'
elif [ "$regenerate" = "true" ] ; then
    $ansible "$manage regenerate_user -c $course_id -u $username"
else
    if [ -n "$force_certificate_state" ]; then
        $ansible "$manage ungenerated_certs -c $course_id -f $force_certificate_state && $manage gen_cert_report -c $course_id" | grep -A2 "Looking up certificate states for" | sed 's/rm:.*//'
    else
        $ansible "$manage ungenerated_certs -c $course_id && $manage gen_cert_report -c $course_id" | grep -A2 "Looking up certificate states for" | sed 's/rm:.*//'
    fi
fi
