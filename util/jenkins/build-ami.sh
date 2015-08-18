#!/bin/bash -x
# This script is meant to be run from jenkins and expects the
# following variables to be set:
#   - BUILD_ID - set by jenkins, Unique ID of build
#   - BUILD_NUMBER - set by jenkins, Build number
#   - refs - repo revisions to pass to abbey. This is provided in YAML syntax,
#            and we put the contents in a file that abbey reads. Refs are
#            different from 'vars' in that each ref is set as a tag on the
#            output AMI.
#   - vars - other vars to pass to abbey. This is provided in YAML syntax,
#            and we put the contents in a file that abby reads.
#   - deployment - edx, edge, etc
#   - environment - stage,prod, etc
#   - play - forum, edxapp, xqueue, etc
#   - base_ami - Optional AMI to use as base AMI for abby instance
#   - configuration - the version of the configuration repo to use
#   - configuration_secure - the version of the secure repo to use
#   - jenkins_admin_ec2_key - location of the ec2 key to pass to abbey
#   - jenkins_admin_configuration_secure_repo - the git repo to use for secure vars
#   - use_blessed - whether or not to use blessed AMIs

if [[ -z "$BUILD_ID" ]]; then
  echo "BUILD_ID not specified."
  exit -1
fi

if [[ -z "$BUILD_NUMBER" ]]; then
  echo "BUILD_NUMBER not specified."
  exit -1
fi

if [[ -z "$deployment" ]]; then
  echo "deployment not specified."
  exit -1
fi

if [[ -z "$environment" ]]; then
  echo "environment not specified."
  exit -1
fi

if [[ -z "$play" ]]; then
  echo "play not specified."
  exit -1
fi

if [[ -z "$jenkins_admin_ec2_key" ]]; then
  echo "jenkins_admin_ec2_key not specified."
  exit -1
fi

if [[ -z "$jenkins_admin_configuration_secure_repo" ]]; then
  echo "jenkins_admin_configuration_secure_repo not specified."
  exit -1
fi

export PYTHONUNBUFFERED=1

cd $WORKSPACE/configuration
configuration=`git rev-parse --short HEAD`
cd $WORKSPACE

cd $WORKSPACE/configuration-secure
configuration_secure=`git rev-parse --short HEAD`
cd $WORKSPACE

base_params=""
if [[ -n "$base_ami" ]]; then
  base_params="-b $base_ami"
fi

blessed_params=""
if [[ "$use_blessed" == "true" ]]; then
  blessed_params="--blessed"
fi

if [[ -e "configuration/playbooks/edx-east/${play}.yml" ]]; then
  playbookdir_params="--playbook-dir configuration/playbooks/edx-east"
else
  playbookdir_params="--playbook-dir ansible-private"
fi

configurationprivate_params=""
if [[ ! -z "$configurationprivaterepo" ]]; then
  configurationprivate_params="--configuration-private-repo $configurationprivaterepo"
  if [[ ! -z "$configurationprivateversion" ]]; then
    configurationprivate_params="$configurationprivate_params --configuration-private-version $configurationprivateversion"
  fi
fi

hipchat_params=""
if [[ ! -z "$hipchat_room_id" ]] && [[ ! -z "$hipchat_api_token"  ]]; then
  hipchat_params="--hipchat-room-id $hipchat_room_id --hipchat-api-token $hipchat_api_token"
fi

cleanup_params=""
if [[ "$cleanup" == "false" ]]; then
  cleanup_params="--no-cleanup"
fi
notification_params=""
if [[ ! -z "$callback_url" ]]; then
  if [[ ! -z "$jobid" ]]; then
    notification_params="--callback-url $callback_url$jobid"
    curl "$callback_url$jobid/starting%20ansible"
  fi
fi

cd configuration
pip install -r requirements.txt

cd util/vpc-tools/

echo "$vars" > /var/tmp/$BUILD_ID-extra-vars.yml
cat /var/tmp/$BUILD_ID-extra-vars.yml
python -u abbey.py -p $play -t m3.large -d $deployment -e $environment -i /edx/var/jenkins/.ssh/id_rsa $base_params $blessed_params $playbookdir_params --vars /var/tmp/$BUILD_ID-extra-vars.yml -c $BUILD_NUMBER --configuration-version $configuration --configuration-secure-version $configuration_secure -k $jenkins_admin_ec2_key --configuration-secure-repo $jenkins_admin_configuration_secure_repo $configurationprivate_params $hipchat_params $cleanup_params $notification_params
