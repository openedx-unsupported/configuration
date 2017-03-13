#!/usr/bin/env bash

# A simple wrapper to run ansible from Jenkins.
# This assumes that you will be running on one or more servers
# that are tagged with Name: <environment>-<deployment>-<play>

if [[
        -z $WORKSPACE           ||
        -z $environment_tag     ||
        -z $deployment_tag      ||
        -z $play_tag            ||
        -z $ansible_play        ||
        -z $elb_pre_post        ||
        -z $first_in            ||
        -z $serial_count
    ]]; then
    echo "Environment incorrect for this wrapper script"
    env
    exit 1
fi

cd $WORKSPACE/configuration/playbooks/edx-east

ansible_extra_vars+=" -e serial_count=$serial_count -e elb_pre_post=$elb_pre_post"

if [ ! -z "$extra_vars" ]; then
    for arg in $extra_vars; do
        ansible_extra_vars+=" -e $arg"
    done
fi

if [[ $run_migrations == "true" ]]; then
      ansible_extra_vars+=" -e migrate_db=yes"
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
    ansible_limit+="tag_Name_${environment_tag}-${deployment_tag}-${play_tag}"
fi

if [[ ! -z "$task_tags" ]]; then
    ansible_task_tags+="--tags $task_tags"
fi

if [[ -z "$ssh_user" ]]; then
    ansible_ssh_user="ubuntu"
else
    ansible_ssh_user="${ssh_user}"
fi

if [[ -f ${WORKSPACE}/configuration-internal/ansible/vars/${deployment_tag}.yml ]]; then
    extra_var_args+=" -e@${WORKSPACE}/configuration-internal/ansible/vars/${deployment_tag}.yml"
fi

if [[ -f ${WORKSPACE}/configuration-internal/ansible/vars/${environment_tag}-${deployment_tag}.yml ]]; then
    extra_var_args+=" -e@${WORKSPACE}/configuration-internal/ansible/vars/${environment_tag}-${deployment_tag}.yml"
fi

if [[ -f ${WORKSPACE}/configuration-secure/ansible/vars/${deployment_tag}.yml ]]; then
    extra_var_args+=" -e@${WORKSPACE}/configuration-secure/ansible/vars/${deployment_tag}.yml"
fi

if [[ -f ${WORKSPACE}/configuration-secure/ansible/vars/${environment_tag}-${deployment_tag}.yml ]]; then
    extra_var_args+=" -e@${WORKSPACE}/configuration-secure/ansible/vars/${environment_tag}-${deployment_tag}.yml"
fi

export PYTHONUNBUFFERED=1
env
ansible-playbook -v -D -u $ansible_ssh_user $ansible_play -i ./ec2.py $ansible_task_tags --limit $ansible_limit $extra_var_args $ansible_extra_vars
