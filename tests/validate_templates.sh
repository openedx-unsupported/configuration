#!/usr/bin/env bash
# This file should be sourced
# The 'root_dir' and 'environment_deployments' variables
# should be set when we source this.

FAIL=0
for e_d in $environment_deployments
do
  GREP_DIR="$root_dir/${e_d}"
  if ! egrep -q -r --include *.json '{{' "${GREP_DIR}"; then
    echo "No un-expanded vars in ${e_d}"
  else
    echo "Found un-expanded vars in ${e_d}"
    echo `egrep -r --include *.json '{{' "${GREP_DIR}"`
    FAIL=1
  fi

  if ! egrep -qi -r --include *.json \'"False"\' "${GREP_DIR}"; then
    echo "No quoted False."
  else
    echo "Found a quoted boolean in ${e_d}"
    echo `egrep -qi -r --include *.json "False" "${GREP_DIR}"`
    FAIL=1
  fi

  if ! egrep -qi -r --include *.json '\"True\"' "${GREP_DIR}"; then
    echo "No quoted False."
  else
    echo "Found a quoted boolean in ${e_d}"
    echo `egrep -qi -r --include *.json '\"True\"' "${GREP_DIR}"`
    FAIL=1
  fi
done

if [ "$FAIL" -eq 1 ] ; then
  echo "Failing..."
  exit 1
fi
