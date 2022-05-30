TinyMCE (Visual Text/HTML Editor) Plugins
-----------------------------------------

The flexibility of the TinyMCE Visual Text and HTML editor makes it possible to configure and extend the editor using different plugins. In order to make use of that modularity in Studio, you'll need to follow two different steps.

Installing Plugins
==================

In order to install the needed TinyMCE plugins while setting up the edX platform, you'll need to specify them in ``TINYMCE_ADDITIONAL_PLUGINS_LIST``. It is a list of objects with the following attributes:

.. list-table::
   :header-rows: 1
   :widths: 15 10 10 65

   * - attribute
     - type
     - required
     - description
   * - ``repo``
     - string
     - yes
     - The TinyMCE plugin's repository.
   * - ``name``
     - string
     - yes
     - Specifies the name of the cloned repository for the TinyMCE plugin.
   * - ``plugin_path``
     - string
     - no
     - Specifies the plugin's relative path in the repository. It is the directory that directly contains the ``plugin.js`` file.
       Default value is ``/``, which indicates that the repository directly contains the ``plugin.js`` file. If the repository doesn't directly contain the ``plugin.js``, then the folder containing it should share the same name as the plugin name.

Here's an example:

.. code:: yaml

   TINYMCE_ADDITIONAL_PLUGINS_LIST:
   - repo: https://github.com/name/demo-plugin
     name: demo-plugin
     plugin_path: "/demo-plugin"

Enabling Plugins
================

There's a decent `guide on enabling the plugins through the edX platform`_, specifically using the ``TINYMCE_ADDITIONAL_PLUGINS`` extra JavaScript configuration.

.. _guide on enabling the plugins through the edX platform: https://github.com/edx/edx-platform/blob/master/docs/guides/extensions/tinymce_plugins.rst
