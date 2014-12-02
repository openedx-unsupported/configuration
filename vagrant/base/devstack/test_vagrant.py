# Copyright (c) 2014 edx
#
#
# The tests in this file are a smoke test against the different kinds of
# tests that are run on a devstack instance. It should hit the various system packages
# underneath (e.g., ensure firefox is installed by running acceptance tests)
#
from fabric.api import *
import unittest
import vagrant
import os


# Set configuration for vagrant instance
# The vagrant object defaults to current directory for its location.
# TODO: make dir more dynamic by using vagrant.Vagrant(root='foodir')
#
v = vagrant.Vagrant()
with open("ssh_file", "w") as f:
    f.write(v.ssh_config())


# Set configuration for fabric
env.use_ssh_config = True
env.ssh_config_path = os.path.realpath("ssh_file")
env.hosts = ["default"]


@task
def generic_test(paver_command):
"""
Via fabric, excutes given commands on a vagrant instance.
Description of fabric contexts used:
  hide is for cleaner output in the test runner
  cd sets the directory to execute on the target machine
  prefix will prepend all statements
  settings/command_timeout sets a timeout for the test command being used
"""
    with hide("commands"):
        with cd("/edx/app/edxapp/edx-platform"):
            with prefix("source '/edx/app/edxapp/edxapp_env' && export DISPLAY=':1'"):
                with settings(command_timeout=600):
                    return run(paver_command).return_code


class TestVagrant(unittest.TestCase):

    def verify_cmd(self, cmd):
        """Validates that a given command can successfully run on the vagrant instance"""
        fab_run = execute(generic_test, cmd)
        self.assertEqual(fab_run['default'], 0)

    def test_coverage_cmd(self):
        """Coverage command """
        self.verify_cmd("paver coverage")

    def test_xmodule_unit(self):
        """
        Specific unit test of a common lib module.
        Validates that the basic unit testing requirements are met.
        """
        self.verify_cmd("paver test_lib -t common/lib/xmodule/xmodule/tests/test_stringify.py")

    def test_systems(self):
        """unit tests on the two key systems"""
        self.verify_cmd("paver test_system -t lms/djangoapps/courseware/tests/tests.py")
        self.verify_cmd("paver test_system -t cms/djangoapps/course_creators/tests/test_views.py")

    def test_js_test(self):
        """javascript tests (use underlying browser install) """
        self.verify_cmd("paver test_js_run -s xmodule")

    def test_bokchoy(self):
        """bok-choy framework is selenium-based. Also validates x11 configuration."""
        self.verify_cmd("paver test_bokchoy -t lms/test_lms.py:RegistrationTest")
        self.verify_cmd("paver test_bokchoy -t discussion/test_discussion.py:DiscussionTabSingleThreadTest --fasttest")
        self.verify_cmd("paver test_bokchoy -t studio/test_studio_with_ora_component.py:ORAComponentTest --fasttest")
        self.verify_cmd("paver test_bokchoy -t lms/test_lms_matlab_problem.py:MatlabProblemTest --fasttest")

    def test_acceptance(self):
        """Run some acceptance tests to ensure their basic functionality is available"""
        self.verify_cmd("paver test_acceptance -s lms --extra_args='lms/djangoapps/courseware/features/problems.feature -s 1'")
        self.verify_cmd("paver test_acceptance -s cms --extra_args='cms/djangoapps/contentstore/features/html-editor.feature -s 1'")

    def test_codejail(self):
        """Ensures codejail infrastructure is in place (e.g., apparmor installed and configured)"""
        self.verify_cmd("paver test_lib -t common/lib/capa/capa/safe_exec/tests/test_safe_exec.py")
