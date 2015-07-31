#!/usr/bin/env bash

# defaults
CONFIGURATION="fullstack"
TARGET="named-release/birch.1"
INTERACTIVE=true

read -d '' HELP_TEXT <<- EOM
Attempts to migrate your Open edX installation to a different release.

-c CONFIGURATION
    Use the given configuration. Either \"devstack\" or \"fullstack\".
    Defaults to \"$CONFIGURATION\"
-t TARGET
    Migrate to the given git ref. Defaults to \"$TARGET\"
-y
    Run in non-interactive mode (reply \"yes\" to all questions)
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

if [ -f /edx/app/edx_ansible/server-vars.yml ]; then
  SERVER_VARS="--extra-vars=\"@/edx/app/edx_ansible/server-vars.yml\""
fi

TEMPDIR=`mktemp -d`
chmod 777 $TEMPDIR
cd $TEMPDIR
git clone https://github.com/edx/configuration.git --depth=1 --single-branch --branch=$TARGET
echo "edx_platform_version: $TARGET" >> vars.yml
echo "ora2_version: $TARGET" >> vars.yml
echo "certs_version: $TARGET" >> vars.yml
echo "forum_version: $TARGET" >> vars.yml
echo "xqueue_version: $TARGET" >> vars.yml
cd configuration/playbooks
sudo /edx/app/edx_ansible/venvs/edx_ansible/bin/ansible-playbook \
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
rm -rf $TEMPDIR
echo "Migration complete. Please reboot your machine."
