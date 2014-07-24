#!/usr/bin/env bash
set -x

if [[
        -z $WORKSPACE       ||
        -z $environment     ||
        -z $deployment
    ]]; then
    echo "Environment incorrect for this wrapper script"
    env
    exit 1
fi


env
cd $WORKSPACE/edx-platform

# install requirements
# These requirements will be installed into the shinginpanda
# virtualenv on the jenkins server and are necessary to run
# run migrations locally

pip install --exists-action w -r requirements/edx/pre.txt
pip install --exists-action w -r requirements/edx/base.txt
pip install --exists-action w -r requirements/edx/post.txt
pip install --exists-action w -r requirements/edx/repo.txt
pip install --exists-action w -r requirements/edx/github.txt
pip install --exists-action w -r requirements/edx/local.txt

cd $WORKSPACE/configuration/playbooks/edx-east

if [[ -f ${WORKSPACE}/configuration-secure/ansible/vars/${deployment}.yml ]]; then
    extra_var_args+=" -e@${WORKSPACE}/configuration-secure/ansible/vars/${deployment}.yml"
fi

if [[ $db_dry_run=="false" ]]; then
    # Set this to an empty string if db_dry_run is 
    # not set.  By default the db_dry_run var is
    # set to --db-dry-run
    extra_var_args+=" -e db_dry_run=''"
fi

extra_var_args+=" -e@${WORKSPACE}/configuration-secure/ansible/vars/${environment}-${deployment}.yml"
extra_var_args+=" -e edxapp_app_dir=${WORKSPACE}"
extra_var_args+=" -e edxapp_code_dir=${WORKSPACE}/edx-platform"
extra_var_args+=" -e edxapp_user=jenkins"
extra_var_args+=" -e edxapp_venv_dir=$VIRTUAL_ENV"

# Generate the json configuration files
ansible-playbook -c local $extra_var_args --tags edxapp_cfg -i localhost, -s -U jenkins edxapp.yml

# Run migrations and replace literal '\n' with actual newlines to make the output
# easier to read

ansible-playbook -v -c local $extra_var_args -i localhost, -s -U jenkins edxapp_migrate.yml | sed 's/\\n/\n/g'
