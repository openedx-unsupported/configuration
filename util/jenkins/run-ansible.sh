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
      ansible_extra_vars+=" -e $extra_vars"
fi

if [[ $run_migrations == "true" ]]; then
      ansible_extra_vars+=" -e migrate_db=yes"
fi

if [[ $first_in == "true" ]]; then
    $ansible_limit+="first_in_"
fi
ansible_limit+="tag_Name_${environment_tag}-${deployment_tag}-${play_tag}"
export PYTHONUNBUFFERED=1
env
ansible-playbook -v -u ubuntu $ansible_play -i ./ec2.py --limit $ansible_limit -e@"$WORKSPACE/configuration-secure/ansible/vars/${deployment_tag}.yml" -e@"$WORKSPACE/configuration-secure/ansible/vars/${environment_tag}-${deployment_tag}.yml" $ansible_extra_vars 
