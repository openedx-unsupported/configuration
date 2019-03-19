#!/bin/bash

# For instructions on how to use this script see https://openedx.atlassian.net/wiki/spaces/EdxOps/pages/390627556/How+to+run+baked+config+on+your+laptop

# Exit on fail
set -e

# Auth and refresh sudo, but dont change users
sudo -v

# Enforce required envs
: ${WORKSPACE?"Need to set WORKSPACE"}
: ${CONFIG_RENDERING_TARGET?"Need to set CONFIG_RENDERING_TARGET"}

rm -rf $CONFIG_RENDERING_TARGET
cd $WORKSPACE/configuration/playbooks

E_Ds=( "stage-edx" "prod-edx" "prod-edge" "developer-sandbox" )
IDAs=( "veda_web_frontend" "analyticsapi" "credentials" "journals" "ecommerce" "discovery" )

for E_D in "${E_Ds[@]}"
do
	ENVIRONMENT="$(echo $E_D | cut -d - -f 1 )"
	DEPLOY="$(echo $E_D | cut -d - -f 2 )"
	VARS="-e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${DEPLOY}.yml -e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${E_D}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${DEPLOY}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${E_D}.yml"

	if [ "${E_D}" == "developer-sandbox" ]; then
	    VARS="-e@$WORKSPACE/${DEPLOY}-internal/ansible/vars/${E_D}.yml -e@$WORKSPACE/${DEPLOY}-secure/ansible/vars/${E_D}.yml -e ansible_ec2_public_ipv4=LINTING"
	fi

	mkdir -p $CONFIG_RENDERING_TARGET/$E_D

	# LMS / CMS for Environment/Deployment
	ansible-playbook -vvv -c local -i 'localhost,' --tags edxapp_cfg ./edxapp.yml $VARS -e edxapp_user=$(whoami) -e common_web_group=$(whoami) -e edxapp_app_dir=$CONFIG_RENDERING_TARGET/$E_D -e edxapp_code_dir=$WORKSPACE/edx-platform -e COMMON_CFG_DIR=$CONFIG_RENDERING_TARGET/$E_D
	
	# IDAs for Environment/Deployment
	for IDA in "${IDAs[@]}"
	do
		ansible-playbook -vvv -c local -i 'localhost,' --tags install:app-configuration ./$IDA.yml $VARS -e COMMON_CFG_DIR=$CONFIG_RENDERING_TARGET/$E_D
	done
done



