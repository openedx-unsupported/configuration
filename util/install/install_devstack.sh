#!/usr/bin/env bash

# Stop if any command fails
set -e
# Echo all commands
set -x

function usage
{
    cat << EOM

    --- install_devstack.sh ---

    Usage: $ bash install_devstack.sh release [-p] [-v vagrant_mount_base] [-h]

    Installs the Open edX developer stack. More information on installing devstack 
    can be found here: https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Devstack

    release
        The release of Open edX you wish to run. Upgrade to the given git ref 'release'.
        You must specify this. Named released are called "named-release/cypress",
        "named-release/dogwood.2", and so on. We recommend the latest stable named 
        release for general members of the open source community. Named releases can
        be found at: https://openedx.atlassian.net/wiki/display/DOC/Open+edX+Releases.
        If you plan on modifying the code, we recommend the "release" branch.

    -p
        Enable use of "preview" from within Studio.

    -v vagrant_mount_base
        Customize the location of the source code that gets cloned during the 
        devstack provisioning.

    -h
        Show this help and exit.

    ---------------------------

EOM
}

# Logging
mkdir -p install_logs
exec > >(tee install_logs/install-$(date +%Y%m%d-%H%M%S).log) 2>&1
echo "Logs located in install_logs directory"

# Default OPENEDX_RELEASE
release=""
# Enable preview in Studio
enable_preview=0
# Vagrant source code provision location
vagrant_mount_location=""

if [[ $# -lt 1 || ${1:0:1} == '-' ]]; then
  usage
  exit 1
fi

release=$1
shift

while getopts "r:pv:h" opt; do
    case "$opt" in
        p)
            enable_preview=1
            ;;
        v)
            vagrant_mount_location=$OPTARG
            ;;
        *)
            usage
            exit 1
            ;;
    esac
done


export OPENEDX_RELEASE=$release
mkdir -p devstack
cd devstack

# Install devstack
curl -L https://raw.githubusercontent.com/edx/configuration/master/vagrant/release/devstack/Vagrantfile > Vagrantfile
vagrant plugin install vagrant-vbguest
vagrant up --provider virtualbox

# Check if preview mode was chosen
if [[ $enable_preview -eq 1 ]]; then
    echo "Enabling use of preview within Studio..."
    sudo bash -c "echo '192.168.33.10  preview.localhost' >> /etc/hosts"
fi
# Check if mount location was changed
if [[ $vagrant_mount_location != "" ]]; then
    echo "Changing Vagrant provision location to "$vagrant_mount_location"..."
    export VAGRANT_MOUNT_BASE=vagrant_mount_location
fi

echo "Finished installing! You may now login using 'vagrant ssh'"
