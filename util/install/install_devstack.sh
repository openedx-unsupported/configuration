#!/usr/bin/env bash

# Stop if any command fails
set -e
# Echo all commands
set -x

function usage
{
    cat << EOM

    --- install_devstack.sh ---

    Installs the Open edX developer stack. More information on installing devstack 
    can be found here: https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Devstack

    -r RELEASE
        The release of Open edX you wish to run. Upgrade to the given git ref RELEASE.
        You must specify this. Named released are called "named-release/cypress",
        "named-release/dogwood.2", and so on. We recommend the latest stable named 
        release for general members of the open source community. Named releases can
        be found at: https://openedx.atlassian.net/wiki/display/DOC/Open+edX+Releases.
        If you plan on modifying the code, we recommend the "release" branch.

    -p
        Enable use of "preview" from within Studio.

    -v VAGRANT_MOUNT_BASE
        Customize the location of the source code that gets cloned during the 
        devstack provisioning.

    -h
        Show this help and exit.

    ---------------------------

EOM
}
##### MAIN
# Logging
#sudo mkdir -p /var/log/edx
#exec > >(sudo tee /var/log/edx/upgrade-$(date +%Y%m%d-%H%M%S).log) 2>&1


echo "Logs located at /var/log/edx"
#export OPENEDX_RELEASE=""

# Default OPENEDX_RELEASE
release="release"
# Enable preview in Studio
enable_preview=0
# Vagrant source code provision location
vagrant_mount_location=""

while getopts "r:pv:h" opt; do
    case "$opt" in
        r)
            release=$OPTARG
            ;;
        p)
            enable_preview=1
            ;;
        v)
            vagrant_mount_location=$OPTARG
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

# while [ "$1" != "" ]; do
#     case $1 in
#         -r | --release )        shift
#                                 if [[ "$1" != "" ]]; then
#                                     release=$1
#                                 else
#                                     echo "A git ref must follow -r"
#                                     exit 
#                                 ;;
#         -p | --preview )        enable_preview=1
#                                 ;;
#         -v | --vagrant_mount )  shift
#                                 vagrant_mount_location=$1
#                                 if [[ "$1" != "" ]]; then
#                                     vagrant_mount_location=$1
#                                 else
#                                     echo "A location must foillow"
#                                     exit 
#                                 ;;
#         -h | --help )           usage
#                                 exit
#                                 ;;
#         * )                     usage
#                                 exit 1
#     esac
#     shift
# done

if [[$release == " " ]]; then
    release="release"
fi
echo $release
#export OPENEDX_RELEASE=$release
#mkdir devstack
#cd devstack
#curl -L https://raw.githubusercontent.com/edx/configuration/master/vagrant/release/devstack/Vagrantfile > Vagrantfile
#vagrant plugin install vagrant-vbguest
#vagrant up --provider virtualbox
if [[ $enable_preview -eq 1 ]]; then
    echo "PREVIEW ENABLED"
    #sudo bash -c "echo '192.168.33.10  preview.localhost' >> /etc/hosts"
fi
if [[ $vagrant_mount_location != "" ]]; then
    echo "CHANGING PROVISION LOCATION TO"$vagrant_mount_location
    #export VAGRANT_MOUNT_BASE=vagrant_mount_location
fi
