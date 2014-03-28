#!/bin/bash -x
# This script is meant to be sourced from elswhere(jenkins) and expects the
# following variables to be set:
#   - refs - repo revisions to pass to abbey
#   - vars - other vars to pass to abbey
#   - deployment
#   - environment
#   - base_ami
#   - BUILD_ID
#   - BUILD_NUMBER
#   - configuration - the version of the configuration repo to use
#   - configuration_secure - the version of the secure repo to use
#   - jenkins_admin_ec2_key - location of the ec2 key to pass to abbey
#   - jenkins_admin_configuration_secure_repo - the git repo to use for secure vars

if [[ "$play" == "" ]]; then
    echo "No Play Specified. Nothing to Do."
    exit 0
fi

export PYTHONUNBUFFERED=1

if [[ -z $configuration ]]; then
  cd configuration
  configuration=`git rev-parse HEAD`
  cd ..
fi

if [[ -z $configuration_secure ]]; then
  cd configuration-secure
  configuration_secure=`git rev-parse HEAD`
  cd ..
fi

cd configuration
pip install -r requirements.txt

cd util/vpc-tools/

echo "$refs" > /var/tmp/$BUILD_ID-refs.yml
cat /var/tmp/$BUILD_ID-refs.yml

echo "$vars" > /var/tmp/$BUILD_ID-extra-vars.yml
cat /var/tmp/$BUILD_ID-extra-vars.yml

python -u abbey.py -p $play -t c1.medium  -d $deployment -e $environment -i /edx/var/jenkins/.ssh/id_rsa -b $base_ami --vars /var/tmp/$BUILD_ID-extra-vars.yml --refs /var/tmp/$BUILD_ID-refs.yml -c $BUILD_NUMBER --configuration-version $configuration --configuration-secure-version $configuration_secure -k $jenkins_admin_ec2_key --configuration-secure-repo $jenkins_admin_configuration_secure_repo
