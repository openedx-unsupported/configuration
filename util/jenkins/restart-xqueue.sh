#!/bin/bash

cd configuration
pip install -r requirements.txt
env

command="/edx/bin/supervisorctl restart xqueue"

ansible tag_Name_${environment}-${deployment}-commoncluster -i playbooks/ec2.py -u ubuntu -s -a "$command"
