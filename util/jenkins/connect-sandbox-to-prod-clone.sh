#!/usr/bin/env bash

# Ansible provisioning wrapper script that
# assumes the following parameters set
# as environment variables
#
# - github_username
# - server_type
# - instance_type
# - region
# - aws_account
# - keypair
# - ami
# - root_ebs_size
# - security_group
# - dns_zone
# - dns_name
# - environment
# - name_tag

export PYTHONUNBUFFERED=1
export BOTO_CONFIG=/var/lib/jenkins/${aws_account}.boto

if [[ -z $WORKSPACE ]]; then
    dir=$(dirname $0)
    source "$dir/ascii-convert.sh"
else
    source "$WORKSPACE/configuration/util/jenkins/ascii-convert.sh"
fi

if [[ ! -f $BOTO_CONFIG ]]; then
  echo "AWS credentials not found for $aws_account"
  exit 1
fi

if [[ -z $sandbox_to_update ]]; then
  sandbox_to_update="${BUILD_USER_ID}.sandbox.edx.org"
fi

cd $WORKSPACE/configuration/playbooks/edx-east
ansible-playbook connect_sandbox.yml  -i $sandbox_to_update, -e@${WORKSPACE}/configuration-secure/ansible/vars/clone-db.yml -e EDXAPP_MYSQL_HOST=$EDXAPP_MYSQL_HOST -e edxapp_version=${edxapp_version} --user ubuntu  -v
