#!/bin/bash

# This is only relevant for AWS instances, and shouldnt be added or run otherwise.
# This script exists because when we build amis we take a snapshot and when we take this snapshot
# the best practice is to reboot the instance since if you do not do this reboot the instance's
# file system integrity cannot be guaranteed.
# Since we monitor hermes, this causes errors that are not a problem to be logged when hermes fails to run correctly
# on build boxes.
# This script is run before hermes is started, preventing it from booting during builds.

# Default startup timeout in systemd is 60 seconds, sleep 50 means we should return before the timeout
sleep_time=50

# This is a hack to sleep and then return 1 if on a build box
# The sleep slows down the looping caused by systemd trying to start the service again if it failed.
# Just returning 1 causes tons of "Unit entered failed state" messages. This will reduce them to 1 a minute or so.
if aws sts get-caller-identity --output=text --query 'Arn' | grep -q 'gocd'; then
    echo "Detected build server, sleeping ${sleep_time} seconds to reduce log noise"
    sleep $sleep_time
    exit 1
fi
