#!/bin/bash

cd configuration
pip install -r requirements.txt
env

command="/edx/app/xqwatcher/venvs/supervisor/bin/supervisorctl -c /edx/app/xqwatcher/supervisor/supervisord.conf restart xqwatcher"

ansible tag_Name_${environment}-${deployment}-xqwatcher -i playbooks/ec2.py -u ubuntu -s -a "$command"
