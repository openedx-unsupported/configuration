devstack
========

Vagrant instance for local development.


Overview
--------

``devstack`` is a Vagrant instance designed for local development.  The instance:

- Uses the same system requirements as production.  This allows developers to discover and fix system configuration issues early in development.
- Simplifies certain production settings to make development more convenient.  For example, it disables ``nginx`` and ``gunicorn`` in favor of ``runserver`` for Django development.

The ``devstack`` instance is designed to run code and tests, but you can do most development in the host environment:

- Git repositories are shared with the host system, so you can use your preferred text editor/IDE.
- You can load pages served by the running Vagrant instance.


Prerequisites
-------------

This guide assumes:

- You know how to open a terminal and use basic Linux operating system commands.
- You understand basic virtualization concepts and are familiar with `Vagrant`__
- You are familiar with `Django`__ development (for LMS and Studio)
- You are familiar with `Sinatra`__ development (for Forums)

__ http://docs.vagrantup.com/v2/
__ http://www.djangoproject.com/
__ http://www.sinatrarb.com/


Installation
------------

1. `Install Vagrant`__ (version 1.3.4 or higher)
2. Install the ``vagrant-hostsupdater`` plugin:

.. code:: bash

    vagrant plugin install vagrant-hostsupdater

3. `Install Ansible`__ (version 1.3.2 or higher)
4. Clone the edX configuration repo:

.. code:: bash

    git clone https://github.com/edx/configuration

5. From the ``configuration/vagrant/devstack`` directory, create the Vagrant instance.  If you have never used Vagrant before, take a moment to read the `Why Vagrant?`__ page, which explains the Vagrant commands in detail.

.. code:: bash

    vagrant up

A new Vagrant instance will be created, with requirements for these repositories installed:

- `edx-platform`__ (LMS and Studio)
- `cs_comments_service`__

The first time you create the instance, Vagrant will download the base box, which is about 2GB.
After downloading the base box, Vagrant will automatically provision your new virtual server using the Ansible scripts from this repo.
If you destroy and recreate the VM, Vagrant will re-use the box it downloaded.

__ http://docs.vagrantup.com/v2/installation/index.html
__ http://www.ansibleworks.com/docs/intro_installation.html
__ http://docs.vagrantup.com/v2/why-vagrant/index.html
__ https://github.com/edx/edx-platform
__ https://github.com/edx/cs_comments_service


Troubleshooting
---------------

Please refer to the `edx-platform wiki`__ for solutions to common issues.

__ https://github.com/edx/edx-platform/wiki/Simplified-install-with-vagrant#troubleshooting


Getting Started
---------------

In the ``configuration/vagrant/devstack`` directory, `ssh into the Vagrant instance`__:

.. code:: bash

    vagrant ssh

This will log you in as the ``vagrant`` user.  Within the Vagrant instance, you will be able to start services (LMS, Studio, and Forums) and run tests.

- The ``edx-platform`` repo (for LMS and Studio) is cloned to ``/edx/app/edxapp/edx-platform`` and synced with ``devstack/edx-platform`` on the host system.
- The ``cs_comments_service`` repo (for Forums) is cloned to ``/edx/app/forum/cs_comments_service`` and synced with ``devstack/cs_comments_service`` on the host system.

To start the services and run tests, you will need to log in as either the ``edxapp`` or ``forum`` user.  See below for instructions.

__ http://docs.vagrantup.com/v2/getting-started/up.html


LMS Workflow
------------

1. Within the Vagrant instance, switch to the ``edxapp`` account:

.. code:: bash

    sudo su edxapp

2. Compile Sass and CoffeeScript:

.. code:: bash

    rake assets[lms,devstack]

3. Update Python requirements:

.. code:: bash

    pip install -r requirements/edx/base.txt

4. Update the Ruby requirements:

.. code:: bash

    bundle install

5. Start the LMS using `runserver`__:

.. code:: bash

    ./manage.py lms runserver --settings=devstack 0.0.0.0:8000

6. Open a browser on your host machine and navigate to ``localhost:8000`` to load the LMS.  (Vagrant will forward port 8000 to the LMS server running in the VM.)

__ https://docs.djangoproject.com/en/dev/ref/django-admin/#runserver-port-or-address-port


Studio Workflow
---------------

1. Within the Vagrant instance, switch to the ``edxapp`` account:

.. code:: bash

    sudo su edxapp

2. Compile Sass and CoffeeScript:

.. code:: bash

    rake assets[cms,devstack]

3. Update Python requirements:

.. code:: bash

    pip install -r requirements/edx/base.txt

4. Update the Ruby requirements:

.. code:: bash

    bundle install

5. Start Studio using `runserver`__:

.. code:: bash

    ./manage.py cms runserver --settings=devstack 0.0.0.0:8001

6. Open a browser on your host machine and navigate to ``localhost:8001`` to load Studio.  (Vagrant will forward port 8001 to the Studio server running in the VM.)


__ https://docs.djangoproject.com/en/dev/ref/django-admin/#runserver-port-or-address-port


Forum Workflow
--------------

1. Within the Vagrant instance, switch to the ``forum`` account:

.. code:: bash

    sudo su forum

2. Update Ruby requirements:

.. code:: bash

    bundle install

3. Start the server:

.. code:: bash

    ruby app.rb

4. Access the API at ``localhost:4567`` (Vagrant will forward port 4567 to the Forum server running in the VM.)



Running LMS/Studio Tests
------------------------


1. Within the Vagrant instance, switch to the ``edxapp`` account:

.. code:: bash

    sudo su edxapp

2. Run the Python unit tests:

.. code:: bash

    rake test:python

3. Run the JavaScript unit tests:

.. code:: bash

    rake test:js

4. Run the LMS and Studio acceptance tests:

.. code:: bash

    rake test:acceptance

See `edx-platform testing documentation`__ for detailed information about writing and running tests.

__ https://github.com/edx/edx-platform/blob/master/docs/internal/testing.md



Updating the Environment
------------------------

If system requirements change, you will need to update the Vagrant instance:

1. Checkout the release branch of the configuration repo:

.. code:: bash

    git checkout release
    git pull

2. From the ``configuration/vagrant/devstack`` directory, provision the Vagrant instance:

.. code:: bash

    vagrant provision


This process will perform a ``git clean`` of the ``edx-platform`` and ``cs_comments_service`` repositories, so make sure that any changes you had are checked in or stashed.


Recreating the Environment
--------------------------

To destroy and recreate the environment:

.. code:: bash

    vagrant destroy
    vagrant up

This will perform a ``git clean`` of the ``edx-platform`` and ``cs_comments_service`` repositories.  You will also lose any work stored in the Vagrant instance as that instance will be destroyed and a new one created from scratch.
