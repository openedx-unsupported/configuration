#!/usr/bin/env bash

# Setting OPENEDX_DEBUG makes this more verbose.
if [[ $OPENEDX_DEBUG ]]; then
    set -x
fi

# Stop if any command fails.
set -e

# Logging: write all the output to a timestamped log file.
sudo mkdir -p /var/log/edx
exec > >(sudo tee /var/log/edx/upgrade-$(date +%Y%m%d-%H%M%S).log) 2>&1

# defaults
CONFIGURATION="none"
TARGET=${OPENEDX_RELEASE-none}
INTERACTIVE=true
OPENEDX_ROOT="/edx"

# Use this function to exit the script: it helps keep the output right with the
# exec-logging we started above.
exit_cleanly () {
  sleep .25
  echo
  exit $@
}

# check_pip succeeds if its first argument is found in the output of pip freeze.
PIP_EDXAPP="sudo -u edxapp -H $OPENEDX_ROOT/bin/pip.edxapp --disable-pip-version-check"
check_pip () {
  how_many=$($PIP_EDXAPP list 2>&- | grep -c "^$1 ")
  if (( $how_many > 0 )); then
    return 0
  else
    return 1
  fi
}

show_help () {
  cat << EOM

Upgrades your Open edX installation to a newer release.

-c CONFIGURATION
    Use the given configuration. Either "devstack" or "fullstack". You
    must specify this.

-t TARGET
    Upgrade to the given git ref. Open edX releases are called
    "open-release/eucalyptus.1", "open-release/eucalyptus.latest", and so on.
    Defaults to \$OPENEDX_RELEASE if it is defined.

-y
    Run in non-interactive mode (reply "yes" to all questions)

-r OPENEDX_ROOT
    The root directory under which all Open edX applications are installed.
    Defaults to "$OPENEDX_ROOT"

-h
    Show this help and exit.

EOM
}

# override defaults with options
while getopts "hc:t:y" opt; do
  case "$opt" in
    h)
      show_help
      exit_cleanly 0
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

# Helper to ask to proceed.
confirm_proceed () {
  echo "Do you wish to proceed?"
  read input
  if [[ "$input" != "yes" && "$input" != "y" ]]; then
    echo "Quitting"
    exit_cleanly 1
  fi
}

# Check we are in the right place, and have the info we need.
if [[ ! -d ${OPENEDX_ROOT}/app/edxapp ]]; then
  echo "Run this on your Open edX machine."
  exit_cleanly 1
fi

if [[ $TARGET == none ]]; then
  cat <<"EOM"
You must specify a target. This should be the next Open edX release after the
one you are currently running.  This script can only move forward one release
at a time.
EOM
  show_help
  exit_cleanly 1
fi

if [[ $CONFIGURATION == none ]]; then
  echo "You must specify a configuration, either fullstack or devstack."
  exit_cleanly 1
fi

APPUSER=edxapp
if [[ $CONFIGURATION == fullstack ]] ; then
  APPUSER=www-data
fi

# Birch details

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

EOM
  confirm_proceed
fi

# Cypress details

if [[ $TARGET == *cypress* && $INTERACTIVE == true ]] ; then
  cat <<"EOM"
          WARNING WARNING WARNING WARNING WARNING
Due to the changes introduced between Birch and Cypress, you may encounter
some problems in this migration. If so, check this webpage for solutions:

https://openedx.atlassian.net/wiki/display/OpenOPS/Potential+Problems+Migrating+from+Birch+to+Cypress

EOM
  confirm_proceed
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

if [[ -f ${OPENEDX_ROOT}/app/edx_ansible/server-vars.yml ]]; then
  SERVER_VARS="--extra-vars=\"@${OPENEDX_ROOT}/app/edx_ansible/server-vars.yml\""
fi

# When tee'ing to a log, ansible (like many programs) buffers its output. This
# makes it hard to tell what is actually happening during the upgrade.
# "stdbuf -oL" will run ansible with line-buffered stdout, which makes the
# messages scroll in the way people expect.
ANSIBLE_PLAYBOOK="sudo stdbuf -oL ansible-playbook --inventory-file=localhost, --connection=local "

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

# Dogwood details

if [[ $TARGET == *dogwood* ]] ; then
  # Run the forum migrations.
  cat > migrate-008-context.js <<"EOF"
    // from: https://github.com/edx/cs_comments_service/blob/master/scripts/db/migrate-008-context.js
    print ("Add the new indexes for the context field");
    db.contents.ensureIndex({ _type: 1, course_id: 1, context: 1, pinned: -1, created_at: -1 }, {background: true})
    db.contents.ensureIndex({ _type: 1, commentable_id: 1, context: 1, pinned: -1, created_at: -1 }, {background: true})

    print ("Adding context to all comment threads where it does not yet exist\n");
    var bulk = db.contents.initializeUnorderedBulkOp();
    bulk.find( {_type: "CommentThread", context: {$exists: false}} ).update(  {$set: {context: "course"}} );
    bulk.execute();
    printjson (db.runCommand({ getLastError: 1, w: "majority", wtimeout: 5000 } ));
EOF

  mongo cs_comments_service migrate-008-context.js

  # We are upgrading Python from 2.7.3 to 2.7.10, so remake the venvs.
  sudo rm -rf ${OPENEDX_ROOT}/app/*/v*envs/*

  echo "Upgrading to the end of Django 1.4"
  cd configuration/playbooks/vagrant
  $ANSIBLE_PLAYBOOK \
    $SERVER_VARS \
    --extra-vars="edx_platform_version=release-2015-11-09" \
    --extra-vars="xqueue_version=named-release/cypress" \
    --extra-vars="migrate_db=yes" \
    --skip-tags="edxapp-sandbox" \
    vagrant-$CONFIGURATION-delta.yml
  cd ../../..

  # Remake our own venv because of the Python 2.7.10 upgrade.
  rm -rf venv
  make_config_venv

  # Need to get rid of South from edx-platform, or things won't work.
  $PIP_EDXAPP uninstall -y South

  echo "Upgrading to the beginning of Django 1.8"
  cd configuration/playbooks/vagrant
  $ANSIBLE_PLAYBOOK \
    $SERVER_VARS \
    --extra-vars="edx_platform_version=dogwood-first-18" \
    --extra-vars="xqueue_version=dogwood-first-18" \
    --extra-vars="migrate_db=no" \
    --skip-tags="edxapp-sandbox" \
    vagrant-$CONFIGURATION-delta.yml
  cd ../../..

  echo "Running the Django 1.8 faked migrations"
  for item in lms cms; do
    sudo -u $APPUSER -E ${OPENEDX_ROOT}/bin/python.edxapp \
      ${OPENEDX_ROOT}/bin/manage.edxapp $item migrate --settings=aws --noinput --fake-initial
  done

  if [[ $CONFIGURATION == fullstack ]] ; then
    sudo -u xqueue \
    SERVICE_VARIANT=xqueue \
    ${OPENEDX_ROOT}/app/xqueue/venvs/xqueue/bin/python \
    ${OPENEDX_ROOT}/app/xqueue/xqueue/manage.py migrate \
    --settings=xqueue.aws_settings --noinput --fake-initial
  fi
fi

# Eucalyptus details

if [[ $TARGET == *eucalyptus* ]] ; then
  if check_pip edx-oauth2-provider ; then
    echo "Uninstall edx-oauth2-provider"
    $PIP_EDXAPP uninstall -y edx-oauth2-provider
  fi
  if check_pip django-oauth2-provider ; then
    echo "Uninstall django-oauth2-provider"
    $PIP_EDXAPP uninstall -y django-oauth2-provider
  fi

  # edx-milestones changed how it was installed, so it is possible to have it
  # installed twice.  Try to uninstall it twice.
  if check_pip edx-milestones ; then
    echo "Uninstall edx-milestones"
    $PIP_EDXAPP uninstall -y edx-milestones
  fi
  if check_pip edx-milestones ; then
    echo "Uninstall edx-milestones again"
    $PIP_EDXAPP uninstall -y edx-milestones
  fi

  if [[ $CONFIGURATION == devstack ]] ; then
    echo "Remove old Firefox"
    sudo apt-get purge -y firefox
  fi

  echo "Upgrade the code"
  cd configuration/playbooks/vagrant
  $ANSIBLE_PLAYBOOK \
    $SERVER_VARS \
    --extra-vars="edx_platform_version=$TARGET" \
    --extra-vars="xqueue_version=$TARGET" \
    --extra-vars="migrate_db=no" \
    --skip-tags="edxapp-sandbox,gather_static_assets" \
    vagrant-$CONFIGURATION-delta.yml
  cd ../../..

  echo "Migrate to fix oauth2_provider"
  ${OPENEDX_ROOT}/bin/edxapp-migrate-lms --fake oauth2_provider zero
  ${OPENEDX_ROOT}/bin/edxapp-migrate-lms --fake-initial

  echo "Clean up forums Ruby detritus"
  sudo rm -rf ${OPENEDX_ROOT}/app/forum/.rbenv ${OPENEDX_ROOT}/app/forum/.gem
fi

# Update to target.

echo "Updating to final version of code"
cd configuration/playbooks
echo "edx_platform_version: $TARGET" > vars.yml
echo "certs_version: $TARGET" >> vars.yml
echo "forum_version: $TARGET" >> vars.yml
echo "xqueue_version: $TARGET" >> vars.yml
echo "demo_version: $TARGET" >> vars.yml
echo "NOTIFIER_VERSION: $TARGET" >> vars.yml
echo "ECOMMERCE_VERSION: $TARGET" >> vars.yml
echo "ECOMMERCE_WORKER_VERSION: $TARGET" >> vars.yml
echo "PROGRAMS_VERSION: $TARGET" >> vars.yml
$ANSIBLE_PLAYBOOK \
    --extra-vars="@vars.yml" \
    $SERVER_VARS \
    vagrant-$CONFIGURATION.yml
cd ../..

# Post-upgrade work.

if [[ $TARGET == *dogwood* ]] ; then
  echo "Running data fixup management commands"
  sudo -u $APPUSER -E ${OPENEDX_ROOT}/bin/python.edxapp \
    ${OPENEDX_ROOT}/bin/manage.edxapp lms --settings=aws generate_course_overview --all

  sudo -u $APPUSER -E ${OPENEDX_ROOT}/bin/python.edxapp \
    ${OPENEDX_ROOT}/bin/manage.edxapp lms --settings=aws post_cohort_membership_fix --commit

  # Run the forums migrations again to catch things made while this script
  # was running.
  mongo cs_comments_service migrate-008-context.js
fi

cd /
sudo rm -rf $TEMPDIR
echo "Upgrade complete. Please reboot your machine."
