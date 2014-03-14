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
  region="us-east-1"
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
    ami="ami-bd6b6ed4"
  elif [[ $server_type == "ubuntu_12.04" || $server_type == "full_edx_installation_from_scratch" ]]; then
    ami="ami-a73264ce"
  fi
fi

if [[ -z $instance_type ]]; then
  instance_type="m1.medium"
fi

deploy_host="${dns_name}.${dns_zone}"
ssh-keygen -f "/var/lib/jenkins/.ssh/known_hosts" -R "$deploy_host"

cd playbooks/edx-east

cat << EOF > $extra_vars
---
ansible_ssh_private_key_file: /var/lib/jenkins/${keypair}.pem
EDXAPP_PREVIEW_LMS_BASE: preview.${deploy_host}
EDXAPP_LMS_BASE: ${deploy_host}
EDXAPP_CMS_BASE: studio.${deploy_host}
EDXAPP_SITE_NAME: ${deploy_host}
edx_platform_version: $edxapp_version
forum_version: $forum_version
xqueue_version: $xqueue_version
xserver_version: $xserver_version
ora_version: $ora_version
ease_version: $ease_version
certs_version: $certs_version
discern_version: $discern_version
EDXAPP_STATIC_URL_BASE: $static_url_base
EOF

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
instance_tags: 
    environment: $environment
    github_username: $github_username
    Name: $name_tag
    source: jenkins
    owner: $BUILD_USER
root_ebs_size: $root_ebs_size
name_tag: $name_tag
COMMON_USER_INFO:
  - name: ${github_username}
    github: true
    type: admin
dns_zone: $dns_zone
rabbitmq_refresh: True
USER_CMD_PROMPT: '[$name_tag] '
elb: $elb
EOF

    # run the tasks to launch an ec2 instance from AMI
    cat $extra_vars
    ansible-playbook edx_provision.yml  -i inventory.ini -e@${extra_vars} -e@${WORKSPACE}/configuration-secure/ansible/vars/developer-sandbox.yml --user ubuntu  -v

    if [[ $server_type == "full_edx_installation" ]]; then
        # additional tasks that need to be run if the
        # entire edx stack is brought up from an AMI
        ansible-playbook rabbitmq.yml -i "${deploy_host}," -e@${extra_vars} -e@${WORKSPACE}/configuration-secure/ansible/vars/developer-sandbox.yml --user ubuntu
        ansible-playbook restart_supervisor.yml -i "${deploy_host}," -e@${extra_vars} -e@${WORKSPACE}/configuration-secure/ansible/vars/developer-sandbox.yml --user ubuntu
    fi
fi

declare -A deploy
roles="edxapp forum xqueue xserver ora discern certs demo"
for role in $roles; do
    deploy[$role]=${!role}
done

# If reconfigure was selected or if starting from an ubuntu 12.04 AMI
# run non-deploy tasks for all roles
if [[ $reconfigure == "true" || $server_type == "full_edx_installation_from_scratch" ]]; then
    cat $extra_vars
    ansible-playbook edx_continuous_integration.yml -i "${deploy_host}," -e@${extra_vars} -e@${WORKSPACE}/configuration-secure/ansible/vars/developer-sandbox.yml --user ubuntu --skip-tags deploy
fi

if [[ $server_type == "full_edx_installation" || $server_type == "full_edx_installation_from_scratch" ]]; then
    # Run deploy tasks for the roles selected
    for i in $roles; do
        if [[ ${deploy[$i]} == "true" ]]; then
            cat $extra_vars
            ansible-playbook ${i}.yml -i "${deploy_host}," -e@${extra_vars} -e@${WORKSPACE}/configuration-secure/ansible/vars/developer-sandbox.yml --user ubuntu --tags deploy
        fi
    done
fi

# deploy the edx_ansible role
ansible-playbook edx_ansible.yml -i "${deploy_host}," -e@${extra_vars} -e@${WORKSPACE}/configuration-secure/ansible/vars/developer-sandbox.yml --user ubuntu

rm -f "$extra_vars"
