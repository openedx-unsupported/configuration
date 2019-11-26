#!/usr/bin/env bash

COMMAND=$1

case $COMMAND in
    start)
        /edx/app/supervisor/venvs/supervisor/bin/supervisord -n --configuration /edx/app/supervisor/supervisord.conf
        ;;
    open)
        . /edx/app/insights/venvs/insights/bin/activate
        cd /edx/app/insights/insights

        /bin/bash
        ;;
    exec)
        shift

        . /edx/app/insights/venvs/insights/bin/activate
        cd /edx/app/insights/insights

        "$@"
        ;;
    *)
        "$@"
        ;;
esac
