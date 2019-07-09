#!/usr/bin/env bash

COMMAND=$1

case $COMMAND in
    start)
        /edx/app/supervisor/venvs/supervisor/bin/supervisord -n --configuration /edx/app/supervisor/supervisord.conf
        ;;
    open)
        . /edx/app/analytics_pipeline/venvs/analytics_pipeline/bin/activate
        cd /edx/app/analytics_pipeline/analytics_pipeline

        /bin/bash
        ;;
    exec)
        shift

        . /edx/app/analytics_pipeline/venvs/analytics_pipeline/bin/activate
        cd /edx/app/analytics_pipeline/analytics_pipeline

        "$@"
        ;;
    *)
        "$@"
        ;;
esac
