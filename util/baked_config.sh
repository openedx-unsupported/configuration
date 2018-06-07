#!/bin/bash

# For instructions on how to use this script see https://openedx.atlassian.net/wiki/spaces/EdxOps/pages/390627556/How+to+run+baked+config+on+your+laptop

pushd ../.. > /dev/null
WORKSPACE="$(pwd)"
popd > /dev/null

ENVIRONMENT="$(echo $1 | cut -d - -f 1 )"
DEPLOY="$(echo $1 | cut -d - -f 2 )"
E_D="${ENVIRONMENT}-${DEPLOY}"

VARS="-e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${DEPLOY}.yml -e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${E_D}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${DEPLOY}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${E_D}.yml"

if [ "${E_D}" == "developer-sandbox" ]; then
    VARS="-e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${E_D}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${E_D}.yml"
fi

if [ ! -e "$WORKSPACE/${DEPLOY}-internal/ansible/vars/${E_D}.yml" ]; then
    echo "Please specify a valid environment-deployment (i.e. stage-edx) as the first and only argument"
    exit 1
fi

mkdir -p $WORKSPACE/baked-config-secure/${E_D}

cd ../playbooks/
ansible-playbook -vvv -c local -i 'localhost,' --tags edxapp_cfg ./edxapp.yml ${VARS} -e edxapp_user=$(whoami) -e common_web_group=$(whoami) -e edxapp_app_dir=$WORKSPACE/baked-config-secure/${E_D} -e edxapp_code_dir=$WORKSPACE/edx-platform -s --ask-sudo-pass --diff
