#!/usr/bin/env bash

# A simple wrapper to run ansible from Jenkins.
# This assumes that you will be running on one or more servers
# that are tagged with Name: <environment>-<deployment>-<play>

if [[
        -z $WORKSPACE      ||
        -z $environment    ||
        -z $deployment     ||
        -z $play           ||
        -z $ansible_play   ||
        -z $elb_pre_post   ||
        -z $first_in       ||
        -z $serial_count
    ]]; then
    echo "Environment incorrect for this wrapper script"
    env
    exit 1
fi

cd $WORKSPACE/configuration/playbooks/edx-east

ansible_extra_vars+=" -e serial_count=$serial_count -e elb_pre_post=$elb_pre_post"

if [ ! -z "$extra_vars" ]; then
      ansible_extra_vars+=" -e $extra_vars"
fi

if [[ $first_in == "true" ]]; then
    $ansible_limit+="first_in_"
fi

ansible_limit="tag_Name_${environment}-${deployment}-${play}"
export PYTHONUNBUFFERED=1
env
ansible-playbook -v -u ubuntu $ansible_play -i ./ec2.py --limit $ansible_limit -e@"$WORKSPACE/configuration-secure/ansible/vars/${deployment}.yml" -e@"$WORKSPACE/configuration-secure/ansible/vars/${environment}-${deployment}.yml" $ansible_extra_vars 
