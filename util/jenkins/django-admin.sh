#!/bin/bash

cd configuration
pip install -r requirements.txt
env

ansible="ansible first_in_tag_Name_${environment}-${deployment}-worker -i playbooks/ec2.py -u ubuntu -s -U www-data -m shell -a"
manage="cd /edx/app/edxapp/edx-platform && /edx/app/edxapp/venvs/edxapp/bin/python ./manage.py  chdir=/edx/app/edxapp/edx-platform"

if [ "$service_variant" != "UNSET" ]; then
  manage="$manage $service_variant --settings aws"
fi

if [ "$help" = "true" ]; then
  manage="$manage help"
fi

echo "Running $ansible \"$manage $command $options\""
$ansible "$manage $command $options"
