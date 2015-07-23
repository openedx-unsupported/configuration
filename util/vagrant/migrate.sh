#!/usr/bin/env bash

# defaults
CONFIGURATION="fullstack"
TARGET="named-release/cypress.rc"
INTERACTIVE=true
OPENEDX_ROOT="/edx"

read -d '' HELP_TEXT <<- EOM
Attempts to migrate your Open edX installation to a different release.

-c CONFIGURATION
    Use the given configuration. Either \"devstack\" or \"fullstack\".
    Defaults to \"$CONFIGURATION\"
-t TARGET
    Migrate to the given git ref. Defaults to \"$TARGET\"
-y
    Run in non-interactive mode (reply \"yes\" to all questions)
-r EDX_ROOT
    The root directory under which all edx applications are installed.
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
The Cypress release of Open edX upgraded the version of Celery used
by the edx-platform workers.  This change was introduced to fix the fact
that when trying to restart the celery worker, the process hangs while
trying to shutdown.  This will cause it to block indefinitely. In order
to prevent this from happening during the upgrade we will pre-emptively
kill all celery workers on this machine.

Birch also introduced a change that breaks the newer version of
ansible when it tries to update the forums rbenv repository. In order
to fix the issue, uncommited modifications made to the /edx/app/forum/.rbenv
repo will be reverted.

Note: that this script assumes the standard location for all tools
installed by edx-ansible (under the '/edx') directory if this is
not the case for you please re-run this script after setting the
'OPENEDX_ROOT' environment variable to your equivalent of '/edx'
and re-running this script.

Do you wish to proceed?
EOM
  read input
  if [ "$input" != "yes" -a "$input" != "y" ]; then
    echo "Quitting"
    exit 1
  else
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
fi

if [ -f /edx/app/edx_ansible/server-vars.yml ]; then
  SERVER_VARS="--extra-vars=\"@/edx/app/edx_ansible/server-vars.yml\""
fi

TEMPDIR=`mktemp -d`
chmod 777 $TEMPDIR
cd $TEMPDIR
git clone https://github.com/edx/configuration.git --depth=1 --single-branch --branch=$TARGET
virtualenv venv
source venv/bin/activate
pip install -r configuration/requirements.txt
echo "edx_platform_version: $TARGET" >> vars.yml
echo "ora2_version: $TARGET" >> vars.yml
echo "certs_version: $TARGET" >> vars.yml
echo "forum_version: $TARGET" >> vars.yml
echo "xqueue_version: $TARGET" >> vars.yml
cd configuration/playbooks
sudo ansible-playbook \
    --inventory-file=localhost, \
    --connection=local \
    --extra-vars=\"@../../vars.yml\" \
    $SERVER_VARS \
    vagrant-$CONFIGURATION.yml
# if this failed, bail out early
exitcode=$?
if [ $exitcode != 0 ]; then
  exit $exitcode;
fi
cd /
sudo rm -rf $TEMPDIR
echo "Migration complete. Please reboot your machine."
