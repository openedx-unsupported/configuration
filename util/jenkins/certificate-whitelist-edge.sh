#!/bin/bash

cd configuration
pip install -r requirements.txt
env

ip=$(python playbooks/ec2.py | jq -r '."tag_Name_prod-edge-worker"[0] | strings')
ssh="ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
manage="cd /edx/app/edxapp/edx-platform && sudo -u www-data /edx/bin/python.edxapp ./manage.py"

echo "$username" > /tmp/username.txt

for x in $(cat /tmp/username.txt); do
  $ssh ubuntu@"$ip" "$manage lms cert_whitelist -a $x -c $course_id --settings aws"
done

rm /tmp/username.txt
