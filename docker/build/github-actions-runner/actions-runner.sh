#!/bin/bash

GITHUB_ORGANIZATION=$GITHUB_ORGANIZATION
GITHUB_ACCESS_TOKEN=$GITHUB_ACCESS_TOKEN

RUNNER_TOKEN=$(curl -sX POST -H "Authorization: token ${GITHUB_ACCESS_TOKEN}" https://api.github.com/orgs/${GITHUB_ORGANIZATION}/actions/runners/registration-token | jq .token --raw-output)

cd /home/actions-runner/actions-runner

./config.sh --url https://github.com/${GITHUB_ORGANIZATION} --token ${RUNNER_TOKEN} --unattended --replace

cleanup() {
    echo "Removing runner..."
    ./config.sh remove --unattended --token ${RUNNER_TOKEN}
}

trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

./bin/runsvc.sh & wait $!
