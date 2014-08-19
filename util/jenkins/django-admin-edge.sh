#!/bin/bash

cd configuration
pip install -r requirements.txt
env

ip=$(python playbooks/ec2.py | jq -r '."tag_Name_prod-edge-worker"[0] | strings')
ssh="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
manage="cd /edx/app/edxapp/edx-platform && sudo -u www-data /edx/bin/python.edxapp ./manage.py"

if [ "$service_variant" != "UNSET" ]; then
  manage="$manage $service_variant"
fi

if [ "$help" = "true" ]; then
  manage="$manage help"
fi

$ssh ubuntu@"$ip" "$manage $command $options --settings aws"
