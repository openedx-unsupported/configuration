#!/bin/bash

CONFIGS_LOCAL=$(cd ../../edx-configs && git rev-parse @)
CONFIGS_REMOTE=$(cd ../../edx-configs && git rev-parse @{u})

echo "Checking if edx-configs repo is up2date."
if [ $CONFIGS_LOCAL = $CONFIGS_REMOTE ]; then
    echo "edx-configs repo is Up-to-date."
else
    echo "edx-configs repo branch is not up2date."
    exit 1;
fi

# Check to see if there are any local changes on the edx-configs local branch
if [ -n "$(cd ../../edx-configs && git status --porcelain)" ]; then
  echo "ERROR: You have local uncommited changes in your local edx-configs branch.";
  exit 1;
fi

