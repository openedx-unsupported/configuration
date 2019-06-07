#!/bin/bash

# This is only relevant for AWS instances, and shouldnt be added or run otherwise.
# This script exists because when we build amis we take a snapshot and when we take this snapshot
# the best practice is to reboot the instance since if you do not do this reboot the instance's
# file system integrity cannot be guaranteed.
# Since we monitor hermes, this causes errors that are not a problem to be logged when hermes fails to run correctly
# on build boxes. 
# This script is run before hermes is started, preventing it from booting during builds.


# This is a hack to
# return 1 if build box, 0 otherwise
# If abbey is removed you will need to look for whatever the name of the new role is changed to.
aws sts get-caller-identity | grep Arn | grep -v abbey