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

export BOTO_CONFIG=/var/lib/jenkins/${aws_account}.boto

function ascii_convert {
  echo $1 | iconv -f utf8 -t ascii//TRANSLIT//IGNORE
}

# remove non-ascii chars from build user vars
BUILD_USER_LAST_NAME=$(ascii_convert $BUILD_USER_LAST_NAME)
BUILD_USER_FIRST_NAME=$(ascii_convert $BUILD_USER_FIRST_NAME)
BUILD_USER_ID=$(ascii_convert $BUILD_USER_ID)
BUILD_USER=$(ascii_convert $BUILD_USER)

if [[ -z $github_username  ]]; then
  github_username=$BUILD_USER_ID
fi

if [[ ! -f $BOTO_CONFIG ]]; then
  echo "AWS credentials not found for $aws_account"
  exit 1
fi

extra_vars="/var/tmp/extra-vars-$$.yml"

if [[ -z $dns_name ]]; then
  dns_name=$github_username
fi

if [[ -z $name_tag ]]; then
  name_tag=${github_username}-${environment}
fi

if [[ -z $ami ]]; then
  if [[ $server_type == "full_edx_installation" ]]; then
    ami="ami-c97727a0"
  elif [[ $server_type == "ubuntu_12.04" ]]; then
    ami="ami-d0f89fb9"
  fi
fi

if [[ -z $instance_type ]]; then
  if [[ $server_type == "full_edx_installation" ]]; then
    instance_type="m1.medium"
  elif [[ $server_type == "ubuntu_12.04" ]]; then
    instance_type="m1.small"
  fi

fi

cat << EOF > $extra_vars
---
EDXAPP_PREVIEW_LMS_BASE: preview.${dns_name}.${dns_zone}
EDXAPP_LMS_BASE: ${dns_name}.${dns_zone}
EDXAPP_LMS_PREVIEW_NGINX_PORT: 80
EDXAPP_CMS_NGINX_PORT: 80
ansible_ssh_private_key_file: /var/lib/jenkins/${keypair}.pem
dns_name: $dns_name
keypair: $keypair
instance_type: $instance_type
security_group: $security_group
ami: $ami
region: $region
instance_tags: '{"environment": "$environment", "github_username": "$github_username", "Name": "$name_tag", "source": "jenkins", "owner": "$BUILD_USER"}'
root_ebs_size: $root_ebs_size
gh_users:
  - user: jarv
    groups:
    - adm
  - user: feanil
    groups:
    - adm
  - user: e0d
    groups:
    - adm
  - user: ${github_username}
    groups:
    - adm
dns_zone: $dns_zone
EOF


cat $extra_vars


cd playbooks/edx-east
# run the tasks to launch an ec2 instance from AMI
ansible-playbook -vvvv edx_provision.yml  -i inventory.ini -e "@${extra_vars}"  --user ubuntu
# run tasks to update application config files that 
# for the hostnames
if [[ $server_type == "full_edx_installation" ]]; then
    ansible-playbook -vvvv edx_continuous_integration.yml  -i "${dns_name}.${dns_zone}," -e "@${extra_vars}" --user ubuntu --tags "lms-env,cms-env,lms-preview-env"
fi
rm -f "$extra_vars"

