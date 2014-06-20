Vagrant
=======

Vagrant instances for local development and testing.

- Vagrant stacks in ``base`` create new base boxes from scratch.
- Vagrant stacks in ``release`` download a base box with most requirements already installed.  The instances then update themselves with the latest versions of the application code.

If you are a developer or designer, you should use the ``release`` stacks.

There are two versions of the stack:

- ``fullstack`` is a production-like configuration running all the services on a single server.  https://github.com/edx/configuration/wiki/edX-Production-Stack
- ``devstack`` is designed for local development.  Although it uses the same system requirements as in production, it simplifies certain settings to make development more convenient.  https://github.com/edx/configuration/wiki/edX-Developer-Stack
- ``test_role`` (under ``base`` directory) is not used for creating test edx instances. Instead, it is used for testing the configuration scripts themselves.
