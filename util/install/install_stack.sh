#!/usr/bin/env bash

# Stop if any command fails
set -e

function usage
{
    cat << EOM

    --- install_stack.sh ---

    Usage: $ bash install_stack.sh stack release [-p] [-b vagrant_mount_base] [-l] [-v] [-h]

    Installs the Open edX devstack or fullstack. Reach out on the Open edX community Slack 
    on #ops (https://open.edx.org/blog/open-edx-slack) or the Open edX Ops Google Group
    (https://groups.google.com/forum/#!forum/openedx-ops) to get support questions answered.

    This script captures a log of all output produced during runtime, and saves it in a .log
    file within the current directory. If you encounter an error during installation, this is
    an invaluable tool for edX developers to help discover what went wrong, so please share it
    if you reach out for support!

    NOTE: This script assumes you have never installed devstack before. Installing multiple 
    versions of devstack can often cause conflicts that this script is not prepared to handle.
    

    stack
        Either 'fullstack' or 'devstack' (no quotes). Full stack mimics a production 
        environment, whereas devstack is useful if you plan on modifying the Open edX 
        code. You must specify this. If you choose fullstack, 'release' should be the
        latest named-release. If you choose devstack, 'release' should be the latest
        named-release or master.

    release
        The release of Open edX you wish to run. Install the given git ref 'release'.
        You must specify this. Named releases are called "named-release/dogwood",
        "named-release/dogwood.2", and so on. We recommend the latest stable named 
        release for general members of the open source community. Named releases can
        be found at: https://openedx.atlassian.net/wiki/display/DOC/Open+edX+Releases.
        If you plan on modifying the code, we recommend the "master" branch.

    -p
        Enable use of "preview" from within Studio. 

    -b vagrant_mount_base
        Customize the location of the source code that gets cloned during the 
        devstack provisioning.

    -l
        Disable logging. Enabled by default.

    -v 
        Verbose output from ansible playbooks.

    -h
        Show this help and exit.

    ---------------------------

EOM
}

# Logging
logging=1
# Output verbosity
verbosity=0
# OPENEDX_RELEASE
release=""
# Enable preview in Studio
enable_preview=0
# Vagrant source code provision location
vagrant_mount_location=""

if [[ $# -lt 2 || ${1:0:1} == '-' || ${2:0:1} == '-' ]]; then
  usage
  exit 1
fi

stack=$1
shift
release=$1
shift

while getopts "pb:lvh" opt; do
    case "$opt" in
        p)
            enable_preview=1
            ;;
        b)
            vagrant_mount_location=$OPTARG
            ;;
        l)
            logging=0
            ;;
        v)
            verbosity=1
            ;;
        h)
            usage
            exit
            ;;
        *)
            usage
            exit 1
            ;;
    esac
done

if [[ $logging > 0 ]]; then
    exec > >(tee install-$(date +%Y%m%d-%H%M%S).log) 2>&1
    echo "Logging enabled."
else
    echo "Logging disabled."
fi

ERROR='\033[0;31m' # Red
WARN='\033[1;33m' # Yellow
SUCCESS='\033[0;32m' # Green
NC='\033[0m' # No Color

export OPENEDX_RELEASE=$release

# Check if mount location was changed
if [[ $vagrant_mount_location != "" ]]; then
    echo "Changing Vagrant provision location to "$vagrant_mount_location"..."
    export VAGRANT_MOUNT_BASE=vagrant_mount_location
fi

if [[ $stack == "devstack" ]]; then # Install devstack
    # Warn if release chosen is not master or named-releaser
    if [[ $release != "master" && $release != *"named-release"* ]]; then
        echo -e "${WARN}The release you entered is not 'master' or a named-release. Please be aware that a branch other than master or a release other than the latest named-release could cause errors when installing devstack.${NC}"
    fi

    wiki_link="https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Devstack"
    mkdir -p devstack
    cd devstack
    curl -L https://raw.githubusercontent.com/edx/configuration/${OPENEDX_RELEASE}/vagrant/release/devstack/Vagrantfile > Vagrantfile
    vagrant plugin install vagrant-vbguest
elif [[ $stack == "fullstack" ]]; then # Install fullstack
    # Warn if release chosen is not named-release
    if [[ $release != *"named-release"* ]]; then
        echo -e "${WARN}The release you entered is not a named-release. Please be aware that a branch other than the latest named-release could cause errors when installing fullstack.${NC}"
    fi

    wiki_link="https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Fullstack"
    mkdir -p fullstack
    cd fullstack
    curl -L https://raw.githubusercontent.com/edx/configuration/${OPENEDX_RELEASE}/vagrant/release/fullstack/Vagrantfile > Vagrantfile
    vagrant plugin install vagrant-hostsupdater
else # Throw error
    echo -e "${ERROR}Unrecognized stack name, must be either devstack or fullstack!${NC}"
    exit 1
fi

# Check for verbosity level
if [[ $verbosity == 1 ]]; then
    sed -i '' 's/-e xqueue_version=\$OPENEDX_RELEASE/-e xqueue_version=\$OPENEDX_RELEASE \\\'$'\n    -vvv/' Vagrantfile
fi

vagrant up --provider virtualbox

# Check if preview mode was chosen
if [[ $enable_preview != 1 ]] || grep -q '192.168.33.10  preview.localhost' /etc/hosts; then
    echo "Studio preview already enabled, skipping..."
else
    echo "Enabling use of preview within Studio..."
    sudo bash -c "echo '192.168.33.10  preview.localhost' >> /etc/hosts"
fi

echo -e "${SUCCESS}Finished installing! You may now login using 'vagrant ssh'"
echo -e "Refer to the edX wiki ("$wiki_link") for more information on using "$stack".${NC}"
