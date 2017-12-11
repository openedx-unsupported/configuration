#!/usr/bin/env bash
set -e
################################################################################
# This executes a small subset of the edx-platform tests.  It is intended as
# a means of testing newly provisioned AMIs for our jenkins workers.
#
# The two main things that happen here:
#   1. The setup from edx-platform/scripts/all-tests.sh, the script that is
#      run by the jenkins workers to kick off tests.
#   2. The paver command for tests, coverage and quality reports are run.
#      For the tests, it runs only a small number of test cases for each
#      test suite.
###############################################################################

# Doing this rather than copying the file into the scripts folder so that
# this file doesn't get cleaned out by the 'git clean' in all-tests.sh.
cd edx-platform-clone

# This will run all of the setup it usually runs, but none of the
# tests because TEST_SUITE isn't defined.
source scripts/jenkins-common.sh

echo `pwd`
echo "PASSED (no-op)"
echo `pwd`
