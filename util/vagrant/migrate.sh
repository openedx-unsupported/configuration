#!/usr/bin/env bash

# defaults
CONFIGURATION="fullstack"
TARGET="named-release/cypress"
INTERACTIVE=true
OPENEDX_ROOT="/edx"

# Will exit the script if a command fails.
bail_if_fail () {
  exitcode=$?
  if [ $exitcode != 0 ]; then
    exit $exitcode;
  fi
}

read -d '' HELP_TEXT <<- EOM
Attempts to migrate your Open edX installation to a different release.

-c CONFIGURATION
    Use the given configuration. Either \"devstack\" or \"fullstack\".
    Defaults to \"$CONFIGURATION\"
-t TARGET
    Migrate to the given git ref. Defaults to \"$TARGET\"
-y
    Run in non-interactive mode (reply \"yes\" to all questions)
-r OPENEDX_ROOT
    The root directory under which all Open edX applications are installed.
    Defaults to \"$OPENEDX_ROOT\"
-h
    Show this help and exit.
EOM

# override defaults with options
while getopts "hc:t:y" opt; do
  case "$opt" in
    h)
      echo  "$HELP_TEXT"
      exit 0
      ;;
    c)
      CONFIGURATION=$OPTARG
      ;;
    t)
      TARGET=$OPTARG
      ;;
    y)
      INTERACTIVE=false
      ;;
    r)
      OPENEDX_ROOT=$OPTARG
      ;;
  esac
done

if [[ `whoami` != "vagrant" ]]; then
  echo "Run this from the vagrant account in your Open edX machine."
  exit 1
fi

if [[ ! -d /edx/app/edxapp ]]; then
  echo "Run this from the vagrant account in your Open edX machine."
  exit 1
fi

if [[ $TARGET == *birch* && $INTERACTIVE == true ]] ; then
  cat <<"EOM"
          WARNING WARNING WARNING WARNING WARNING
The Birch release of Open edX depends on MySQL 5.6 and MongoDB 2.6.4.
The Aspen release of Open edX depended on MySQL 5.5 and MongoDB 2.4.7.
Please make sure that you have already upgraded MySQL and MongoDB
before continuing.

If MySQL or MongoDB are not at the correct version, this script will
attempt to automatically upgrade them for you. However, this process
can fail, and IT RUNS THE RISK OF CORRUPTING ALL YOUR DATA.
Here there be dragons.

         .>   )\;`a__
        (  _ _)/ /-." ~~
         `( )_ )/
          <_  <_

Once you have verified that your MySQL and MongoDB versions are correct,
or you have decided to risk the automatic upgrade process, type "yes"
followed by enter to continue. Otherwise, press ctrl-c to quit. You can
also run this script with the -y flag to skip this check.

Do you wish to proceed?
EOM
  read input
  if [ "$input" != "yes" -a "$input" != "y" ]; then
    echo "Quitting"
    exit 1
  fi
fi

if [[ $TARGET == *cypress* && $INTERACTIVE == true ]] ; then
  cat <<"EOM"
          WARNING WARNING WARNING WARNING WARNING
Due to the changes introduced between Birch and Cypress, you may encounter
some problems in this migration. If so, check this webpage for solutions:

https://openedx.atlassian.net/wiki/display/OpenOPS/Potential+Problems+Migrating+from+Birch+to+Cypress

Do you wish to proceed?
EOM
  read input
  if [ "$input" != "yes" -a "$input" != "y" ]; then
    echo "Quitting"
    exit 1
  fi
fi

if [[ $TARGET == *cypress* ]] ; then
  # Needed if transitioning to Cypress.
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
fi

if [ -f /edx/app/edx_ansible/server-vars.yml ]; then
  SERVER_VARS="--extra-vars=\"@${OPENEDX_ROOT}/app/edx_ansible/server-vars.yml\""
fi

make_config_venv () {
  virtualenv venv
  source venv/bin/activate
  pip install -r configuration/pre-requirements.txt
  pip install -r configuration/requirements.txt
}

TEMPDIR=`mktemp -d`
echo "Working in $TEMPDIR"
chmod 777 $TEMPDIR
cd $TEMPDIR
# Set the CONFIGURATION_TARGET environment variable to use a different branch
# in the configuration repo, defaults to $TARGET.
git clone https://github.com/edx/configuration.git \
  --depth=1 --single-branch --branch=${CONFIGURATION_TARGET-$TARGET}
make_config_venv

if [[ $TARGET == *dogwood* ]] ; then
  # We are upgrading from 2.7.3 to 2.7.10, so remake the venvs.
  sudo rm -rf /edx/app/*/v*envs/*

  if [[ $CONFIGURATION == devstack ]] ; then
    DEVSTACK_VARS="--extra-vars=devstack=true"
  fi

  echo "Upgrading edx-platform to the end of Django 1.4"
  cd configuration/playbooks/vagrant
  sudo ansible-playbook \
    --inventory-file=localhost, \
    --connection=local \
    $SERVER_VARS \
    $DEVSTACK_VARS \
    --extra-vars="edx_platform_version=release-2015-11-09 migrate_db=yes" \
    --skip-tags="edxapp-sandbox" \
    vagrant-edxapp-delta.yml
  bail_if_fail
  cd ../../..

  # That playbook updated Python from 2.7.3 to 2.7.10, so remake our own venv.
  rm -rf venv
  make_config_venv

  # Need to get rid of South from edx-platform, or things won't work.
  sudo -u edxapp /edx/app/edxapp/venvs/edxapp/bin/pip uninstall -y South
  bail_if_fail

  echo "Upgrading edx-platform to the beginning of Django 1.8"
  cd configuration/playbooks/vagrant
  sudo ansible-playbook \
    --inventory-file=localhost, \
    --connection=local \
    $SERVER_VARS \
    $DEVSTACK_VARS \
    --extra-vars="edx_platform_version=ned/dogwood-first-18 migrate_db=no" \
    --skip-tags="edxapp-sandbox" \
    vagrant-edxapp-delta.yml
  bail_if_fail
  cd ../../..

  echo "Running the first Django 1.8 faked migrations"
  for item in lms cms; do
    sudo -u edxapp \
      /edx/app/edxapp/venvs/edxapp/bin/python \
      /edx/app/edxapp/edx-platform/manage.py $item migrate \
      --settings=aws --noinput --fake-initial
  done
fi

cd configuration/playbooks
echo "edx_platform_version: $TARGET" >> vars.yml
echo "ora2_version: $TARGET" >> vars.yml
echo "certs_version: $TARGET" >> vars.yml
echo "forum_version: $TARGET" >> vars.yml
echo "xqueue_version: $TARGET" >> vars.yml
sudo ansible-playbook \
    --inventory-file=localhost, \
    --connection=local \
    --extra-vars=\"@../../vars.yml\" \
    $SERVER_VARS \
    vagrant-$CONFIGURATION.yml
bail_if_fail

cd /
sudo rm -rf $TEMPDIR
echo "Migration complete. Please reboot your machine."
