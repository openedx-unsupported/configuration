#!/usr/bin/env bash

# Ansible configuration/deploy wrapper script that
# assumes the following parameters set
# as environment variables
#
# - dns_name - REQUIRED
# - dns_zone 
# - edxapp_version
# - forum_version
# - xqueue_version
# - xserver_version
# - ora_version
# - ease_version
# - deploy
# - keypair


export BOTO_CONFIG=/var/lib/jenkins/${aws_account}.boto
if [[ -z $dns_name ]]; then
  echo "The hostname is required to know what machine to configure"
  exit 1
fi

if [[ ! -f $BOTO_CONFIG ]]; then
  echo "AWS credentials not found for $aws_account"
  exit 1
fi

extra_vars="/var/tmp/extra-vars-$$.yml"

cat << EOF > $extra_vars
---
EDXAPP_PREVIEW_LMS_BASE: preview.${dns_name}.${dns_zone}
EDXAPP_LMS_BASE: ${dns_name}.${dns_zone}
EDXAPP_LMS_PREVIEW_NGINX_PORT: 80
EDXAPP_CMS_NGINX_PORT: 80
XSERVER_GRADER_CHECKOUT: False
c_skip_grader_checkout: True

edx_platform_commit: $edxapp_version
forum_version: $forum_version
xqueue_version: $xqueue_version
xserver_version: $xserver_version
ora_version: $ora_version
ease_version: $ease_version

ansible_ssh_private_key_file: /var/lib/jenkins/${keypair}.pem

EOF


cat $extra_vars


cd playbooks/edx-east
./ec2.py --refresh
ansible-playbook -vvv $playbook  -i ./ec2.py -e "@$extra_vars"  --user ubuntu --tags deploy
