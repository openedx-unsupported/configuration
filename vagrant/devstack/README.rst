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


Wiki documation - https://github.com/edx/configuration/wiki/edX-Developer-Stack
