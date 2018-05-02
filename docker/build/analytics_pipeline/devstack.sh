#!/usr/bin/env bash

COMMAND=$1

case $COMMAND in
    open)
        . /edx/app/analytics_pipeline/venvs/analytics_pipeline/bin/activate
        cd /edx/app/analytics_pipeline/analytics_pipeline

        /bin/bash
        ;;
esac
