#!/bin/bash

cd configuration
pip install -r requirements.txt
env

ansible="ansible first_in_tag_Name_${environment}-${deployment}-worker -i playbooks/ec2.py -u ubuntu -s -U www-data -a"
manage="cd /edx/app/edxapp/edx-platform && /edx/bin/python.edxapp /edx/bin/manage.edxapp lms --settings aws cert_whitelist"

echo "$username" > /tmp/username.txt

if [ "$addremove" = "add" ]; then
  for x in $(cat /tmp/username.txt); do
    echo "Adding $x"
    $ansible "$manage --add $x -c $course_id"
  done
elif [ "$addremove" = "remove" ]; then
  for x in $(cat /tmp/username.txt); do
    echo "Removing $x"
    $ansible "$manage --del $x -c $course_id"
  done
fi

rm /tmp/username.txt
