#!/usr/bin/env bash

if [[ -z $1 ]]; then
    echo "Path to data directory required"
    exit 1
fi

data_dir=$1
dir=$(dirname $0)

if [[ ! -f /var/tmp/repos.txt ]]; then
    python $dir/repos_from_orgs.py
fi

for repo_url in $(cat /var/tmp/repos.txt); do 

    repo_name=${repo_url##*/}
    if [[ ! -d $data_dir/$repo_name ]]; then
        git clone --mirror $repo_url $data_dir/$repo_name
        cd $data_dir/$repo_name
        git update-server-info
    else
        cd $data_dir/$repo_name
        git remote update
        git update-server-info
    fi
done
