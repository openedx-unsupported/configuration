Vagrant
=======

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
