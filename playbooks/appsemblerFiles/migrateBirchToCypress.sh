#!/usr/bin/env bash
#based on: https://raw.githubusercontent.com/edx/configuration/master/util/vagrant/migrate.sh

# defaults
PLATFORM_BRANCH=$1 #edx-platform branch -- REQUIRED
TARGET="named-release/cypress" #for all default repos
OPENEDX_ROOT="/edx"
CONFIGURATION_BRANCH="appsembler/feature/mergeCypress"

read -d '' HELP_TEXT <<- EOM
============================
Attempts to migrate your Open edX installation from Birch to Cypress.
For use on our AWS ang GCloud customers.
For questions, email TJ (tj@appsembler.com)

----------------------------
Usage:
./migrateBirchToCypress.sh EDX_PLATFORM_BRANCH_NAME

EOM

# override defaults with options
if [ -z "$PLATFORM_BRANCH" ]; then
  echo "$HELP_TEXT"
  exit 0
fi

echo "Killing all celery worker processes."
sudo ${OPENEDX_ROOT}/bin/supervisorctl stop edxapp_worker:* &
sleep 3
# Supervisor restarts the process a couple of times so we have to kill it multiple times.
sudo pgrep -lf celery | grep worker | awk '{ print $1}' | sudo xargs -I {} kill -9 {}
sleep 3
sudo pgrep -lf celery | grep worker | awk '{ print $1}' | sudo xargs -I {} kill -9 {}
sleep 3
sudo pgrep -lf celery | grep worker | awk '{ print $1}' | sudo xargs -I {} kill -9 {}
sleep 3
sudo pgrep -lf celery | grep worker | awk '{ print $1}' | sudo xargs -I {} kill -9 {}
sudo -u forum git -C ${OPENEDX_ROOT}/app/forum/.rbenv reset --hard

if [ -f /edx/app/edx_ansible/server-vars.yml ]; then
  SERVER_VARS="--extra-vars=\"@${OPENEDX_ROOT}/app/edx_ansible/server-vars.yml\""
fi

TEMPDIR=`mktemp -d`
chmod 777 $TEMPDIR
cd $TEMPDIR
git clone https://github.com/edx/configuration.git --depth=1 --single-branch --branch=$CONFIGURATION_BRANCH
virtualenv venv
source venv/bin/activate
pip install -r configuration/requirements.txt
echo "edx_platform_version: $PLATFORM_BRANCH" >> vars.yml
echo "ora2_version: $TARGET" >> vars.yml
echo "certs_version: $TARGET" >> vars.yml
echo "forum_version: $TARGET" >> vars.yml
echo "xqueue_version: $TARGET" >> vars.yml
echo "edx_platform_repo: https://github.com/appsembler/edx-platform.git" >> vars.yml
echo "edx_ansible_source_repo: https://github.com/appsembler/configuration.git" >> vars.yml

cd configuration/playbooks
sudo ansible-playbook \
    --inventory-file=localhost, \
    --connection=local \
    --extra-vars=\"@../../vars.yml\" \
    $SERVER_VARS \
#    -e edx_platform_repo=https://github.com/appsembler/edx-platform.git -e edx_platform_version=metalogix/feature/mergeCypress \
    edx_sandbox.yml
# if this failed, bail out early
exitcode=$?
if [ $exitcode != 0 ]; then
  exit $exitcode;
fi
cd /
sudo rm -rf $TEMPDIR
echo "Migration complete. Please reboot your machine."
