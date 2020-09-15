#!/usr/bin/env bash
#
# Read a list of Ansible variables that should have generated values, and make
# a new file just like it, with the generated values.

TARGET=${CONFIGURATION_VERSION-${OPENEDX_RELEASE-master}}
wget -q "https://raw.githubusercontent.com/edx/configuration/$TARGET/playbooks/sample_vars/passwords.yml" -O passwords-template.yml

while IFS= read -r line; do
    # Make a random string. SECRET_KEY's should be longer.
    length=35
    if [[ $line == *SECRET_KEY* ]]; then
        length=100
    fi
    REPLACE=$(LC_ALL=C < /dev/urandom tr -dc 'A-Za-z0-9' | head -c$length)
    # Change "!!null"-to-end-of-line to the password.
    echo "$line" | sed "s/\!\!null.*/\'$REPLACE\'/"
done < passwords-template.yml > my-passwords.yml
