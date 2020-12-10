 #!/usr/bin/env bash

# function to create a virtual environment in a directory separate from
# where it is called. Name of venv is predictable based on where this
# script is called
#
# $ venv=$(create_virtualenv --python=python3.8 --clear)
# $ . "$venv/bin/activate"
#
# Optional Environmental Variables:
# 
# JOBVENVDIR - where on the system to create the virtualenv
#            - e.g. /edx/var/jenkins/jobvenvs/
#
# Reason for existence: shiningpanda, the jenkins plugin that manages our
# virtualenvironments for jenkins jobs, is no longer supported so we need
# to stop using it. The tricky part is shiningpanda uses virtualenvwrapper
# underneath the hood, so while we're moving jenkins jobs to python3.8
# and beyond withOUT shiningpanda, we want to be careful to not futz with
# virtualenvwrapper environmental variables (which are required for it to
# function). Therefore, we have this separate implementation of virtualenv
# management.
#
# Oh, why not create virtualenvironments right in the jenkins workspace
# where the job is run? Because workspaces are so deep in the filesystem
# that the autogenerated shebang line created by virtualenv on things in
# the virtualenv's bin directory will often be too long for the OS to
# parse.
function create_virtualenv () {
	if [ -z "$JOBVENVDIR" ]
	then
		echo "No JOBVENVDIR found. Using default value."
		JOBVENVDIR="/edx/var/jenkins/jobvenvs/"
	fi

	# create a unique hash for the job based location of where job is run
	venvname=($(echo -n `pwd` | md5sum))

	cd $JOBVENVDIR
	virtualenv $@ "$venvname"

	# return venv path so caller can source the environment
	return "$JOBVENVDIR$venvname"
}
