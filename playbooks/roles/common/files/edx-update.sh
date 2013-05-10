#!/bin/bash

function usage() {
    echo "update.sh [cms|lms|all|none]"
    echo "    option is what services to collectstatic and restart (default=all)"
}

if [ $# -gt 1 ]; then
    usage
    exit 1
fi

if [ $# == 0 ]; then
    do_CMS=1
    do_LMS=1
else
    case $1 in
        cms)
            do_CMS=1
            ;;
        lms)
            do_LMS=1
            ;;
        both|all)
            do_CMS=1
            do_LMS=1
            ;;
        none)
            ;;
        *)
            usage
            exit 1
            ;;
    esac
fi

function run() {
    echo
    echo "======== $@"
    $@
}

source /etc/profile
source /opt/edx/bin/activate
export PATH=$PATH:/opt/www/.gem/bin

cd /opt/wwc/mitx

BRANCH="origin/feature/edx-west/stanford-theme"

export GIT_SSH="/tmp/git_ssh.sh"
run git fetch origin -p
run git checkout $BRANCH

if [[ $do_CMS ]]; then
    export SERVICE_VARIANT=cms
    run rake cms:gather_assets:aws
    run sudo restart cms
fi

if [[ $do_LMS ]]; then
    export SERVICE_VARIANT=lms
    run rake lms:gather_assets:aws
    run sudo restart lms
fi

