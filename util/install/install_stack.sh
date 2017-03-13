#!/usr/bin/env bash

# Setting OPENEDX_DEBUG makes this more verbose.
if [[ $OPENEDX_DEBUG ]]; then
    set -x
fi

# Stop if any command fails.
set -e

function usage
{
    cat << EOM

    Usage: $ bash ${0##*/} [-b mount_base] [-v] [-h] STACK [RELEASE]

    Installs the Open edX devstack or fullstack. If you encounter any trouble
    or have questions, head over to https://open.edx.org/getting-help.

    This script captures a log of all output produced during runtime, and saves
    it in a .log file within the current directory. If you encounter an error
    during installation, this is an invaluable tool for edX developers to help
    discover what went wrong, so please share it if you reach out for support!

    NOTE: This script assumes you have never installed devstack before.
    Installing multiple versions of devstack can often cause conflicts that
    this script is not prepared to handle.

    STACK
        Either 'fullstack' or 'devstack'. Fullstack mimics a production
        environment, whereas devstack is useful if you plan on modifying the
        Open edX code. You must specify this.

        If you choose fullstack, 'release' should be the latest Open edX
        release.

        If you choose devstack, 'release' should be the latest Open edX
        release or master.

    RELEASE
        The release of Open edX to install.  Defaults to \$OPENEDX_RELEASE.
        Open edX releases are called "open-release/eucalyptus.1",
        "open-release/eucalyptus.2", and so on.

        We recommend the latest stable open release for general members of the
        open source community. Details on available open releases can be found
        at: https://openedx.atlassian.net/wiki/display/DOC/Open+edX+Releases.

        If you plan on modifying the code, we recommend the "master" branch.

    -b mount_base
        Customize the location of the source code that gets cloned during the
        devstack provisioning. The default is the current directory. This
        option is not valid if installing fullstack.

    -v
        Verbose output from ansible playbooks.

    -h
        Show this help and exit.

EOM
}


ERROR='\033[0;31m' # Red
WARN='\033[1;33m' # Yellow
SUCCESS='\033[0;32m' # Green
NC='\033[0m' # No Color

# Output verbosity
verbosity=0
# OPENEDX_RELEASE
release=""
# Vagrant source code provision location
vagrant_mount_location=""

while getopts "b:vh" opt; do
    case "$opt" in
        b)
            if  [[ $stack == "devstack" ]]; then
                vagrant_mount_location=$OPTARG
            else
                echo -e "${ERROR}Fullstack has no mount location. The -b option is not valid for fullstack!${NC}"
                exit 1
            fi
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

shift "$((OPTIND-1))" # Shift off the options we've already parsed

# STACK is a required positional argument.
if [[ ! $1 ]]; then
    echo "STACK is required"
    usage
    exit 1
fi
stack=$1
shift

# RELEASE is an optional positional argument, defaulting to OPENEDX_RELEASE.
if [[ $1 ]]; then
    release=$1
    shift
else
    release=$OPENEDX_RELEASE
fi

if [[ ! $release ]]; then
    echo "You must specify RELEASE, or define OPENEDX_RELEASE before running."
    exit 1
fi

# If there are positional arguments left, something is wrong.
if [[ $1 ]]; then
    echo "Don't understand extra arguments: $*"
    usage
    exit 1
fi

mkdir -p logs
log_file=logs/install-$(date +%Y%m%d-%H%M%S).log
exec > >(tee $log_file) 2>&1
echo "Capturing output to $log_file"
echo "Installation started at $(date '+%Y-%m-%d %H:%M:%S')"

function finish {
    echo "Installation finished at $(date '+%Y-%m-%d %H:%M:%S')"
}
trap finish EXIT

export OPENEDX_RELEASE=$release
echo "Installing release '$OPENEDX_RELEASE'"

# Check if mount location was changed
if [[ $vagrant_mount_location != "" ]]; then
    echo "Changing Vagrant provision location to $vagrant_mount_location..."
    export VAGRANT_MOUNT_BASE=$vagrant_mount_location
fi

if [[ -d .vagrant ]]; then
    echo -e "${ERROR}A .vagrant directory already exists here. If you already tried installing $stack, make sure to vagrant destroy the $stack machine and 'rm -rf .vagrant' before trying to reinstall. If you would like to install a separate $stack, change to a different directory and try running the script again.${NC}"
    exit 1
fi

if [[ $stack == "devstack" ]]; then # Install devstack
    # Warn if release chosen is not master or open-release (Eucalyptus and up)
    if [[ $release != "master" && $release != "open-release"* ]]; then
        echo -e "${WARN}The release you entered is not 'master' or an open-release. Please be aware that a branch other than master or a release other than the latest open-release could cause errors when installing $stack.${NC}" | fmt
    fi

    wiki_link="https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Devstack"
    curl -fOL# https://raw.githubusercontent.com/edx/configuration/${OPENEDX_RELEASE}/vagrant/release/devstack/Vagrantfile
    vagrant plugin install vagrant-vbguest
elif [[ $stack == "fullstack" ]]; then # Install fullstack
    # Warn if release chosen is not open-release (Eucalyptus and up)
    if [[ $release != "open-release"* ]]; then
        echo -e "${WARN}The release you entered is not an open-release. Please be aware that a branch other than the latest open-release could cause errors when installing $stack.${NC}"
    fi

    wiki_link="https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Fullstack"
    curl -fOL# https://raw.githubusercontent.com/edx/configuration/${OPENEDX_RELEASE}/vagrant/release/fullstack/Vagrantfile
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

# Set preview host.
if grep -q '192.168.33.10  preview.localhost' /etc/hosts; then
    echo "Studio preview already enabled, skipping..."
else
    echo "Enabling use of preview within Studio..."
    sudo bash -c "echo '192.168.33.10  preview.localhost' >> /etc/hosts"
fi

echo -e "${SUCCESS}Finished installing! You may now log in using 'vagrant ssh'"
echo -e "Refer to the edX wiki ($wiki_link) for more information on using $stack.${NC}"
