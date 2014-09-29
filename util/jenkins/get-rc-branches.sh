#!/bin/bash

usage() {

  prog=$(basename "$0")
  cat<<EOF

  This will clone a repo and look for release
  candidate branches that will be returned as
  a sorted list in json to be
  parsed by the dynamic choice jenkins plugin

  Usage: $prog
            -v    add verbosity (set -x)
            -n    echo what will be done
            -h    this
            -r    repo to look in
            -f    filter string for branch list

  Example: $prog -r https://github.com/edx/edx-platform -f "rc/"
EOF
}

while getopts "vnhr:f:" opt; do
  case $opt in
    v)
      set -x
      shift
      ;;
    h)
      usage
      exit 0
      ;;
    n)
      noop="echo Would have run: "
      shift
      ;;
    r)
      repo=$OPTARG
      ;;
    f)
      filter=$OPTARG
      ;;
  esac
done

if [[ -z $repo || -z $filter ]]; then
    echo  'Need to specify a filter and a repo'
    usage
    exit 1
fi

repo_basename=$(basename "$repo")
cd /var/tmp

if [[ ! -d $repo_basename ]]; then
    $noop git clone "$repo" "$repo_basename" --mirror > /dev/null 2>&1
else
    $noop cd "/var/tmp/$repo_basename"
    $noop git fetch > /dev/null > /dev/null 2>&1
fi

$noop cd "/var/tmp/$repo_basename"
if [[ -z $noop ]]; then
    for branch in $(git branch -a | sort -r | tr -d ' ' | grep -E "$filter" ); do
        echo "origin/${branch}"
    done
    for tag in $(git tag -l | sort -r | tr -d ' ' | grep -E "$filter"); do
        echo "$tag"
    done
else
    echo "Would have checked for branches or tags using filter $filter"
fi
