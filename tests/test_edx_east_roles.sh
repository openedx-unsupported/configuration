set -e

ROOT_DIR=$PWD
cd playbooks/edx-east
ROLE_DIRS=$(/bin/ls -d roles/*)
cat <<EOF >travis-test.yml
- name: Play to test all roles
  hosts: all
  roles:
EOF
for role_dir in $ROLE_DIRS; do
    echo "    - $(basename $role_dir)" >> travis-test.yml
done

ansible-playbook -i localhost, --syntax-check travis-test.yml

output_dir="$PWD/test_output/env-dep"
mkdir -p $output_dir
ansible-playbook -i localhost, -c local --tags edxapp_cfg edxapp.yml -e edxapp_user=`whoami` -e edxapp_app_dir=$output_dir -e edxapp_code_dir=$output_dir -e EDXAPP_CFG_DIR=$output_dir

root_dir=$output_dir
environment_deployments="."
source $ROOT_DIR/tests/validate_templates.sh
