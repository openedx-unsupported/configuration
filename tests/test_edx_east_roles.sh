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

# Grab missing ansible variables from oxa-tools
wget -q https://raw.githubusercontent.com/Microsoft/oxa-tools/oxa/devfic/config/countries.yml -O countries.yml
wget -q https://raw.githubusercontent.com/Microsoft/oxa-tools/oxa/devfic/config/languages.yml -O languages.yml
wget -q https://raw.githubusercontent.com/Microsoft/oxa-tools/oxa/devfic/config/server-vars.yml -O server-vars.yml
sed -i -e "s/%%\([^%]*\)%%//g" server-vars.yml

output_dir="$PWD/test_output/env-dep"
mkdir -p $output_dir

helpful_message()
{
    echo -e "\033[1;36m"
    echo -e "\n These plays have a dependency on values in (oxa-tools)/config/ \n Please ensure \n\t a) relevant changes have been merged in oxa-tools AND \n\t b) (edx-configuration)/tests/test_edx_east_roles.sh has the correct references."
    echo -e " This failure case can be identified if an error $1 ends with 'is undefined'\n"
    echo -e '\033[0m'
}

echo "`helpful_message below`"
set +e
ansible-playbook -i localhost, -c local --tags edxapp_cfg edxapp.yml -e edxapp_user=`whoami` -e edxapp_app_dir=$output_dir -e edxapp_code_dir=$output_dir -e EDXAPP_CFG_DIR=$output_dir \
    -e@server-vars.yml \
    -e@countries.yml \
    -e@languages.yml \
    -e EDXAPP_PREVIEW_SITE_NAME=""

returnCode=$?
if [[ $returnCode != 0 ]] ; then
    echo "`helpful_message above`"
    exit $returnCode
fi
set -e

root_dir=$output_dir
environment_deployments="."
source $ROOT_DIR/tests/validate_templates.sh
