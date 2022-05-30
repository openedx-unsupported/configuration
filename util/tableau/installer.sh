#!/usr/bin/env bash

# Tableau server installer.
# Usage:
##   installer.sh ADMIN_USER ADMIN_PASS TABLEAU_ADMIN_USER TABLEAU_ADMIN_PASS
##
## Example:
##   ./installer.sh ubuntu-user ubuntu-pass test-user test-pass
##

ADMIN_USER=$1
ADMIN_PASS=$2
TABLEAU_ADMIN_USER=$3
TABLEAU_ADMIN_PASS=$4

mkdir tableau
cd tableau/
git clone https://github.com/tableau/server-install-script-samples.git
cd server-install-script-samples/linux/automated-installer/
wget https://downloads.tableau.com/tssoftware/tableau-server-2020-4-1_amd64.deb

cat > secrets <<- EOM
# You can use this as a template for the secrets file used with the
# automated-installer script.
#
# Note: If you do not enter the tsm_admin_pass or the
# tableau_server_admin_pass in this file, you will be prompted to enter this
# information during installation. However, you must enter the account names
# for tsm_admin_user and tableau_server_admin_user.

# Credentials for the account that is running the automated-installer script.
# This account will be added to the 'tsmadmin' group. The 'tsmadmin' group is
# created during the Tableau installation process. Members of the 'tsmadmin'
# group can run TSM commands.
#
tsm_admin_user="$TABLEAU_ADMIN_USER"
tsm_admin_pass="$TABLEAU_ADMIN_PASS"

# Enter a username and password to create the initial Tableau administrator
# account. This account will be created in Tableau Server by the installation
# process and will have Tableau Server administrator rights. The user account
# will be local to Tableau Server and will not be a Linux OS account. If you
# are using LDAP or AD for authentication, then the account you specify for
# the Tableau administrator must be a valid account from the directory service.
#
tableau_server_admin_user="$ADMIN_USER"
tableau_server_admin_pass="$ADMIN_PASS"
EOM

sudo ./automated-installer -s secrets -f config.json -r registration.json --accepteula tableau-server-2020-4-1_amd64.deb
