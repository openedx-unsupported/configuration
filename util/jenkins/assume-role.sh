#!/usr/bin/env bash

# assume-role function for use by machine services that don't use MFA to assume role.
# source this into your bash script and then
#
# assume-role(${AWS_ROLE_ARN})
#
# The function turns off echoing, so no tokens are exposed.
# If you wish to hide your Role's ARN, you can set +x before calling the function.

assume-role() {
    set +x
    ROLE_ARN="${1}"
    SESSIONID=$(date +"%s")
    DURATIONSECONDS="${2:-3600}"

    RESULT=(`aws sts assume-role --role-arn $ROLE_ARN \
            --role-session-name $SESSIONID \
	    --duration-seconds $DURATIONSECONDS \
            --query '[Credentials.AccessKeyId,Credentials.SecretAccessKey,Credentials.SessionToken]' \
            --output text`)

    export AWS_ACCESS_KEY_ID=${RESULT[0]}
    export AWS_SECRET_ACCESS_KEY=${RESULT[1]}
    export AWS_SECURITY_TOKEN=${RESULT[2]}
    export AWS_SESSION_TOKEN=${AWS_SECURITY_TOKEN}
    set -x
}

unassume-role () {
    unset AWS_ACCESS_KEY_ID
    unset AWS_SECRET_ACCESS_KEY
    unset AWS_SECURITY_TOKEN
    unset AWS_SESSION_TOKEN
}
