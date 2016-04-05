Vagrant
=======

Vagrant instances for local development and testing of edX instances and Ansible playbooks/roles.

- Vagrant stacks in ``base`` create new base boxes from scratch.
- Vagrant stacks in ``release`` download a base box with most requirements already installed.  The instances then update themselves with the latest versions of the application code.

If you are a developer or designer, you should use the ``release`` stacks.

For creating test edX instances, there are two versions of the stack:

- ``fullstack`` is a production-like configuration running all the services on a single server.  https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Fullstack
- ``devstack`` is designed for local development. It uses the same system requirements as in production, but simplifies certain settings to make development more convenient.  https://openedx.atlassian.net/wiki/display/OpenOPS/Running+Devstack

For testing Ansible playbooks and roles, there are two directories under the ``base`` directory:

- ``test_playbook`` is used for testing the playbooks in the Ansible configuration scripts.
- ``test_role`` is used for testing the roles in the Ansible configuration scripts.

To test an Ansible playbook using Vagrant:

- Create/modify a playbook under ``/playbooks`` (e.g. "foo.yml")
- Export its name as the value of the environment variable ``VAGRANT_ANSIBLE_PLAYBOOK``, like this:
 - ``export VAGRANT_ANSIBLE_PLAYBOOK=foo``
- Execute ``vagrant up`` from within the ``test_playbook`` directory.

To test an Ansible role using Vagrant:

- Create/modify a role under ``/playbooks/roles`` (e.g. "bar-role")
- Export its name as the value of the environment variable ``VAGRANT_ANSIBLE_ROLE``, like this:
 - ``export VAGRANT_ANSIBLE_ROLE=bar-role``
- Execute ``vagrant up`` from within the ``test_role`` directory.
