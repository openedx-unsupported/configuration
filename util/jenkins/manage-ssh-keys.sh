#!/usr/bin/env bash

# A simple wrapper to add ssh keys from 
# This assumes that you will be running on one or more servers
# that are tagged with Name: <environment>-<deployment>-<play>

if [[
        -z $WORKSPACE           ||
        -z $environment_tag     ||
        -z $deployment_tag      ||
        -z $play                ||
        -z $first_in            ||
        -z $public_key          ||
        -z $serial_count
    ]]; then
    echo "Environment incorrect for this wrapper script"
    env
    exit 1
fi

cd $WORKSPACE/configuration/playbooks/edx-east
export AWS_PROFILE=$deployment_tag

ansible_extra_vars+=" -e serial_count=$serial_count -e elb_pre_post=$elb_pre_post"

if [[ ! -z "$extra_vars" ]]; then
      ansible_extra_vars+=" -e $extra_vars"
fi

if [[ $check_mode == "true" ]]; then
      ansible_extra_vars+=" --check"
fi

if [[ ! -z "$run_on_single_ip" ]]; then
    ansible_limit+="$run_on_single_ip"
else
    if [[ $first_in == "true" ]]; then
        ansible_limit+="first_in_"
    fi
    ansible_limit+="tag_environment_${environment_tag}:&tag_deployment_${deployment_tag}"
fi

ansible_extra_vars+=" -e public_key=$public_key"

export PYTHONUNBUFFERED=1
env
ansible-playbook -v -D -u ubuntu $play -i ./ec2.py $ansible_task_tags --limit $ansible_limit -e@"$WORKSPACE/configuration-secure/ansible/vars/ubuntu-public-keys.yml" $ansible_extra_vars 
rm -f $extra_vars_file
