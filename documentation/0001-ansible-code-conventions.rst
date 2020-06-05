========================
Ansible Code Conventions
========================

General Conventions
===================
**Spacing**
* YAML files - All yaml files should use 2 space indents and end with .yml
* Use spaces around jinja variable names. {{ var }} not {{var}}

**Variables**
* Variables - Use jinja variable syntax over deprecated variable syntax. {{ var }} not $var
* Variables that are environment specific and that need to be overridden should be in ALL CAPS.
* Variables that are internal to the role should be lowercase.
* Prefix all variables defined in a role with the name of the role. Example: EDXAPP_FOO

**Roles/Plays/Playbooks**
* Keep roles self contained - Roles should avoid including tasks from other roles when possible
* Plays should do nothing more than include a list of roles except where pre_tasks and post_tasks are required (to manage a load balancer for example)
* Plays/Playbooks that apply to the general community should be copied to configuration/playbooks

**ETC**
* Handlers - Do not use handlers. If you need to restart an app when specific tasks run, just add a task to do so at the end of the playbook. If necessary, it can be skipped with tags (see `Role Life-cycle Tags`_)
* Separators - Use underscores (e.g. my_role) not dashes (my-role).
* Paths - When defining paths, do not include trailing slashes (e.g. my_path: /foo not my_path: /foo/. When concatenating paths, follow the same convention (e.g. {{ my_path }}/bar not {{ my_path }}bar)

.. _Role Life-cycle Tags: https://openedx.atlassian.net/wiki/spaces/OpenOPS/pages/39584735/Role+Life-cycle+Tags


Conditionals and Return Status
==============================

Always use ``when:`` for conditionals

.. code-block:: bash

    when: my_var is defined
    when: my_var is not defined

To verify return status (see `ansible docs conditionals`_)

.. code-block:: yaml

  - command: /bin/false
    register: my_result
    ignore_errors: True
  - debug: msg="task failed"
    when: my_result|failed


.. _ansible docs conditionals: http://docs.ansible.com/playbooks_conditionals.html

Formatting
==========

Use yaml-style blocks.

Good:

.. code-block:: yaml

  - file:
      dest: "{{ test }}"
      src: "./foo.txt"
      mode: 0770
      state: present
      user: "root"
      group: "wheel"

Bad:

.. code-block:: yaml

  - file: >
      dest={{ test }} src=./foo.txt mode=0770
      state=present user=root group=wheel

Break long lines using yaml line continuation. `Reference`_

.. code-block:: yaml

  - shell: >
      python a very long command --with=very --long-options=foo
      --and-even=more_options --like-these


.. _Reference: http://docs.ansible.com/playbooks_intro.html

Roles
=====

**Role Variables**

- ``common`` role - Contains tasks that apply to all roles.
- ``common_vars`` role - Contains vars that apply to all roles.
- *Roles variables* - Variables specific to a role should be defined in /vars/main.yml. All variables should be prefixed with the role name.
- *Role defaults* - Default variables should configure a role to install edx in such away that all services can run on a single server
- Variables that are environment specific and that need to be overridden should be in all caps.
Every role should have a standard set of role directories, example that includes a python and ruby virtualenv:

.. code-block:: yaml

  edxapp_data_dir: "{{ COMMON_DATA_DIR }}/edxapp"
  edxapp_app_dir: "{{ COMMON_APP_DIR }}/edxapp"
  edxapp_log_dir: "{{ COMMON_LOG_DIR }}/edxapp"
  edxapp_venvs_dir: "{{ edxapp_app_dir }}/venvs"
  edxapp_venv_dir: "{{ edxapp_venvs_dir }}/edxapp"
  edxapp_venv_bin: "{{ edxapp_venv_dir }}/bin"
  edxapp_rbenv_dir: "{{ edxapp_app_dir }}"
  edxapp_rbenv_root: "{{ edxapp_rbenv_dir }}/.rbenv"
  edxapp_rbenv_shims: "{{ edxapp_rbenv_root }}/shims"
  edxapp_rbenv_bin: "{{ edxapp_rbenv_root }}/bin"
  edxapp_gem_root: "{{ edxapp_rbenv_dir }}/.gem"
  edxapp_gem_bin: "{{ edxapp_gem_root }}/bin"


**Role Naming Conventions**

- *Role names* - Terse, one word if possible, use underscores if necessary.
- *Role task names* - Terse, descriptive, spaces are OK and should be prefixed with the role name.

Secure vs. Insecure data
========================

As a general policy we want to protect the following data:

- Usernames
- Public keys (keys are OK to be public, but can be used to figure out usernames)
- Hostnames
- Passwords, API keys

Directory structure for the secure repository:

.. code-block:: text

  ansible
  ├── files
  ├── keys
  └── vars


  
Secure vars are set in files under the ``ansible/vars`` directory.  These files will be passed in when the relevant ansible-playbook commands are run.  If you need a secure variable defined, give it a name and use it in your playbooks like any other variable.  The value should be set in the secure vars files of the relevant deployment (edx, edge, etc.).  If you don't have access to this repository, you'll need to submit a ticket to the devops team to make the secure change.
