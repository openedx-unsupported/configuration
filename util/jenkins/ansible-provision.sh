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
    source "$WORKSPACE/util/jenkins/ascii-convert.sh"
fi

if [[ -z $static_url_base ]]; then
  static_url_base="/static"
fi

if [[ -z $github_username  ]]; then
  github_username=$BUILD_USER_ID
fi

if [[ ! -f $BOTO_CONFIG ]]; then
  echo "AWS credentials not found for $aws_account"
  exit 1
fi

extra_vars="/var/tmp/extra-vars-$$.yml"

if [[ -z $region ]]; then
  region="us-east1"
fi

if [[ -z $zone ]]; then
  zone="us-east-1b"
fi

if [[ -z $elb ]]; then
  elb="false"
fi

if [[ -z $dns_name ]]; then
  dns_name=$github_username
fi

if [[ -z $name_tag ]]; then
  name_tag=${github_username}-${environment}
fi

if [[ -z $ami ]]; then
  if [[ $server_type == "full_edx_installation" ]]; then
    ami="ami-973d08fe"
  elif [[ $server_type == "ubuntu_12.04" ]]; then
    ami="ami-d0f89fb9"
  fi
fi

if [[ -z $instance_type ]]; then
  if [[ $server_type == "full_edx_installation" ]]; then
    instance_type="m1.small"
  elif [[ $server_type == "ubuntu_12.04" ]]; then
    instance_type="m1.small"
  fi

fi

deploy_host="${dns_name}.${dns_zone}"
ssh-keygen -f "/var/lib/jenkins/.ssh/known_hosts" -R "$deploy_host"

if [[ -z $WORKSPACE ]]; then
    dir=$(dirname $0)
    source "$dir/ascii-convert.sh"
else
    source "$WORKSPACE/util/jenkins/create-var-file.sh"
fi

cd playbooks/edx-east

if [[ $basic_auth == "true" ]]; then
    # vars specific to provisioning added to $extra-vars
    cat << EOF_AUTH >> $extra_vars
NGINX_HTPASSWD_USER: $auth_user
NGINX_HTPASSWD_PASS: $auth_pass
EOF_AUTH
fi


if [[ $recreate == "true" ]]; then
    # vars specific to provisioning added to $extra-vars
    cat << EOF >> $extra_vars
dns_name: $dns_name
keypair: $keypair
instance_type: $instance_type
security_group: $security_group
ami: $ami
region: $region 
zone: $zone
instance_tags: '{"environment": "$environment", "github_username": "$github_username", "Name": "$name_tag", "source": "jenkins", "owner": "$BUILD_USER"}'
root_ebs_size: $root_ebs_size
name_tag: $name_tag
gh_users:
  - ${github_username}
dns_zone: $dns_zone
rabbitmq_refresh: True
GH_USERS_PROMPT: '[$name_tag] '
elb: $elb
EOF

    cat $extra_vars
    # run the tasks to launch an ec2 instance from AMI
    ansible-playbook edx_provision.yml  -i inventory.ini -e "@${extra_vars}"  --user ubuntu

    if [[ $server_type == "full_edx_installation" ]]; then
        # additional tasks that need to be run if the
        # entire edx stack is brought up from an AMI
        ansible-playbook rabbitmq.yml -i "${deploy_host}," -e "@${extra_vars}" --user ubuntu
        ansible-playbook restart_supervisor.yml -i "${deploy_host}," -e "@${extra_vars}" --user ubuntu
    fi
fi

declare -A deploy

deploy[edxapp]=$edxapp
deploy[forum]=$forum
deploy[xqueue]=$xqueue
deploy[xserver]=$xserver
deploy[ora]=$ora
deploy[discern]=$discern
deploy[certs]=$certs


# If reconfigure was selected run non-deploy tasks for all roles
if [[ $reconfigure == "true" ]]; then
    ansible-playbook edx_continuous_integration.yml -i "${deploy_host}," -e "@${extra_vars}" --user ubuntu --skip-tags deploy
fi

# Run deploy tasks for the roles selected
for i in "${!deploy[@]}"; do
    if [[ ${deploy[$i]} == "true" ]]; then
        ansible-playbook ${i}.yml -i "${deploy_host}," -e "@${extra_vars}" --user ubuntu --tags deploy
    fi
done


rm -f "$extra_vars"
