Packer
=======

``jenkins_worker.json`` is the `packer configuration template`_ that tells packer how to build the image.

- `template variable`_ pattern ``"foo": "{{env `BAR`}}"``

  - What this does is take the value of the environment variable BAR which was set in the shell that kicks off the ``packer build jenkins_worker.json`` command (for example in a jenkins job) and pass it through to the user variable "foo".
  - This the user variable "foo" will now be available globally within the template.
  - If the environment variable is not set in the shell that kicks off the packer build command, the user variable value will be the empty string.

- Regarding the `ansible-playbook command`_ that is used to run the jenkins_worker role's -e (--extra-vars) option

  - `playbook variable`_ pattern ``-e 'bar={{ user `foo` }}'``
  - Packer has determined the value of the template user variable "foo" from the local environment variable (see above)
  - Ansible will use this as the value for the playbook variable "bar" when running the play.

.. _packer configuration template: http://www.packer.io/docs/templates/introduction.html
.. _template variable: http://www.packer.io/docs/templates/user-variables.html
.. _ansible-playbook command: http://docs.ansible.com/playbooks_intro.html#executing-a-playbook
.. _playbook variable: http://docs.ansible.com/playbooks_variables.html#passing-variables-on-the-command-line
