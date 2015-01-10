#!/bin/bash

cd configuration
pip install -r requirements.txt
env

ansible="ansible -v first_in_tag_Name_${environment}-${deployment}-worker -i playbooks/ec2.py -u ubuntu -s -U www-data -m shell -a"
manage="cd /edx/app/edxapp/edx-platform && /edx/bin/python.edxapp /edx/bin/manage.edxapp lms change_enrollment --settings=aws"
noop_switch=""

if [ "$noop" = true ]; then
  noop_switch="--noop"  
fi

$ansible "$manage $noop_switch --course $course --user $name --to $to --from $from"
