#!/bin/bash

usage() {
    echo "Usage: $0 environment-deploy (enable|disable)"
    echo
    echo "Examples:"
    echo "    Turn on maintenance page for stage-edx:    $0 stage-edx enable"
    echo "    Turn off maintenance page for stage-edx:   $0 stage-edx disable"
    exit 1
}

ED=$1
ENABLE_ARG=$2

case $ED in
    loadtest-edx|stage-edx|prod-edx|prod-edge)
        ;;
    *)
        echo "ERROR: environment-deploy must be one of loadtest-edx, stage-edx, prod-edx or prod-edge"
        echo
        usage
        ;;
esac

case $ENABLE_ARG in
    enable)
        ENABLE="True"
        ;;
    disable)
        ENABLE="False"
        ;;
    *)
        echo "ERROR: must specify enable or disable"
        echo
        usage
        ;;
esac

INVENTORY=$(aws ec2 describe-instances --filter "Name=tag:Name,Values=${ED}-edxapp,${ED}-studio,${ED}-worker" --query 'Reservations[].Instances[].PrivateIpAddress' --output text | tr '\t' ',')
ENABLE_EXTRA_VAR="{\"ENABLE_MAINTENANCE\": ${ENABLE}}"

ansible-playbook ./edx_maintenance.yml -i "${INVENTORY}," -e "${ENABLE_EXTRA_VAR}"
