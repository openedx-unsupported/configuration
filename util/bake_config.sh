#!/bin/bash

# For instructions on how to use this script see https://openedx.atlassian.net/wiki/spaces/EdxOps/pages/390627556/How+to+run+baked+config+on+your+laptop

# Exit on fail
set -e

# Enforce required envs
: ${WORKSPACE?"Need to set WORKSPACE"}
: ${CONFIG_RENDERING_TARGET?"Need to set CONFIG_RENDERING_TARGET"}

# Optional envs you can override if you wish to render config for different EDPs
# these are expected to be comma separated with no spaces, see defaults.
ENVIRONMENT_DEPLOYMENTS=${ENVIRONMENT_DEPLOYMENTS:=stage-edx,prod-edx,prod-edge,developer-sandbox}
PLAYS=${PLAYS:=edxapp,veda_web_frontend,analyticsapi,credentials,ecommerce,discovery,ecomworker,insights,registrar,notes}

rm -rf $CONFIG_RENDERING_TARGET
cd $WORKSPACE/configuration/playbooks

for ENVIRONMENT_DEPLOYMENT in $(echo $ENVIRONMENT_DEPLOYMENTS | sed "s/,/ /g")
do
    ENVIRONMENT="$(echo $ENVIRONMENT_DEPLOYMENT | cut -d - -f 1 )"
    DEPLOY="$(echo $ENVIRONMENT_DEPLOYMENT | cut -d - -f 2 )"
    VARS="-e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${DEPLOY}.yml -e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${ENVIRONMENT_DEPLOYMENT}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${DEPLOY}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${ENVIRONMENT_DEPLOYMENT}.yml"

    if [ "${ENVIRONMENT_DEPLOYMENT}" == "developer-sandbox" ]; then
        VARS="-e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${ENVIRONMENT_DEPLOYMENT}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${ENVIRONMENT_DEPLOYMENT}.yml -e ansible_ec2_public_ipv4=LINTING"
    fi

    mkdir -p $CONFIG_RENDERING_TARGET/$ENVIRONMENT_DEPLOYMENT

    # PLAYS for Environment/Deployment
    for PLAY in $(echo $PLAYS | sed "s/,/ /g")
    do
        if [ "$PLAY" == "edxapp" ]; then
            # LMS / CMS for Environment/Deployment
            ansible-playbook --become-user=$(whoami) -vvv -c local -i 'localhost,' --tags edxapp_cfg_yaml_only ./edxapp.yml $VARS -e edxapp_user=$(whoami) -e common_web_group=$(whoami) -e COMMON_CFG_DIR=$CONFIG_RENDERING_TARGET/$ENVIRONMENT_DEPLOYMENT
        else
            # All other IDAs
            ansible-playbook --become-user=$(whoami) -vvv -c local -i 'localhost,' --tags install:app-configuration ./$PLAY.yml $VARS -e COMMON_CFG_DIR=$CONFIG_RENDERING_TARGET/$ENVIRONMENT_DEPLOYMENT
        fi
    done
done
