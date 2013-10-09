#!/usr/bin/env bash

# Ansible provisioning wrapper script that
# assumes the following parameters set
# as environment variables
# 
# - github_username - REQUIRED (will also be the jenkins user)
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

if [[ $github_username == "PUT_YOUR_GITHUB_USERNAME_HERE" ]]; then
  echo "You need to specify a git username to create an ec2 instance"
  exit 1
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

cat << EOF > $extra_vars
---

ansible_ssh_private_key_file: /var/lib/jenkins/${keypair}.pem
dns_name: $dns_name
keypair: $keypair
instance_type: $instance_type
security_group: $security_group
ami: $ami
region: $region
instance_tags: '{"environment": "$environment", "github_username": "$github_username", "Name": "$name_tag", "source": "jenkins"}'
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
ansible-playbook -vvvv edx_provision.yml  -i inventory.ini -e "@${extra_vars}"  --user ubuntu
rm -f "$extra_vars"

