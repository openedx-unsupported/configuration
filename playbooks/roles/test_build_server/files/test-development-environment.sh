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
export PYTHON_VERSION=3.5
source scripts/jenkins-common.sh

case "$1" in
    "unit")

        # Now we can run a subset of the tests via paver.
        # Run some of the common/lib unit tests
        paver test_lib -t common/lib/xmodule/xmodule/tests/test_stringify.py

        # Generate some coverage reports
        # Since `TEST_SUITE` is not set, change the coverage file written by the
        # previous test to a generic one.
        cp reports/common_lib_xmodule.coverage reports/.coverage
        paver coverage

        # Run some of the djangoapp unit tests
        paver test_system -t lms/djangoapps/courseware/tests/tests.py
        paver test_system -t cms/djangoapps/course_creators/tests/test_views.py
        ;;

    "js")

        # Run some of the javascript unit tests
        paver test_js_run -s lms-coffee
        ;;

    "bokchoy")

        # Run some of the bok-choy tests
        paver test_bokchoy -t discussion/test_discussion.py::DiscussionTabMultipleThreadTest
        paver test_bokchoy -t studio/test_studio_settings.py::StudioSettingsA11yTest
        ;;

    "quality")
        # Generate quality reports
        paver run_quality
        ;;

    *)
        echo "args required"
        exit 1
esac
