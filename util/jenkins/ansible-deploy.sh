#!/usr/bin/env bash

# Ansible deployment wrapper script that
# assumes the following parameters set
# as environment variables
# 
# {edxapp,forum,xqueue,xserver,ora} - true/false
# {edxapp,forum,xqueue,xserver,ora}_version - commit or tag
 
export BOTO_CONFIG=/var/lib/jenkins/${aws_account}.boto
if [[ -z $WORKSPACE ]]; then
    dir=$(dirname $0)
    source "$dir/ascii-convert.sh"
else
    source "$WORKSPACE/util/jenkins/ascii-convert.sh"
fi

if [[ -z $github_username  ]]; then
  github_username=$BUILD_USER_ID
fi

if [[ ! -f $BOTO_CONFIG ]]; then
  echo "AWS credentials not found for $aws_account"
  exit 1
fi

extra_vars="/var/tmp/extra-vars-$$.yml"

if [[ -z $deploy_host ]]; then
  deploy_host="${github_username}.m.sandbox.edx.org"
fi

cat << EOF > $extra_vars
---

EDXAPP_PREVIEW_LMS_BASE: preview.${deploy_host}
EDXAPP_LMS_BASE: ${deploy_host}
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
PYPI_MIRROR_URL: 'https://pypi.edx.org/root/pypi/+simple/'
EOF

cat $extra_vars

echo "Deploying to $deploy_host"

declare -A deploy

deploy[edxapp]=$edxapp
deploy[forum]=$forum
deploy[xqueue]=$xqueue
deploy[xserver]=$xserver
deploy[ora]=$ora

ssh-keygen -f "/var/lib/jenkins/.ssh/known_hosts" -R "$deploy_host"

cd playbooks/edx-east
for i in "${!deploy[@]}"; do
    if [[ ${deploy[$i]} == "true" ]]; then
        ansible-playbook -vvvv deploy_${i}.yml -i "${deploy_host}," -e "@${extra_vars}" --user ubuntu --tags deploy
    fi
done
rm -f "$extra_vars"

