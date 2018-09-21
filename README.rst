Configuration Management
########################

Introduction
************

The goal of the edx/configuration project is to provide a simple, but flexible,
way for anyone to stand up an instance of Open edX that is fully configured and
ready-to-go.

Before getting started, please look at the `Open EdX Installation options`_, to
see which method for deploying OpenEdX is right for you.


**Important**: The Open edX configuration scripts need to be run as root on
your servers and will make changes to service configurations including, but not
limited to, sshd, dhclient, sudo, apparmor and syslogd. Our scripts are made
available as we use them and they implement our best practices. We strongly
recommend that you review everything that these scripts will do before running
them against your servers. We also recommend against running them against
servers that are hosting other applications. No warranty is expressed or
implied.

For more information including installation instruction please see the `OpenEdX
Wiki`_.

For info on any large recent changes please see the `change log`_.

.. _Open EdX Installation options: https://open.edx.org/installation-options
.. _Ansible: http://ansible.com/
.. _OpenEdX Wiki: https://openedx.atlassian.net/wiki/display/OpenOPS/Open+edX+Operations+Home
.. _change log: https://github.com/edx/configuration/blob/master/CHANGELOG.md
