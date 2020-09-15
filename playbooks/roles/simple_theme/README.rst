Simple theme
############

This role allows you to deploy a basic theme on deploy time. The theme can be
customized via ansible variables in the following ways:
- to redefine SASS variables (like colors)
- to include some static files provided in a local directory (e.g. logo)
- to download some static files from URLs (e.g. logo, favicon)
- in addition the theme can be based on an existing theme from a repository

This role will be included by edxapp. The main use case involves deploying a
theme as part of deploying an instance. The new theme will be enabled when
the instance starts.

Configuration
*************
- The theme name for the deployed theme will be the one specifed in EDXAPP_DEFAULT_SITE_THEME
- The theme will be deployed to a directory of that name.

You have the option to use a skeleton theme. This is the base theme that will be
copied to the target machine, and modified afterwards via the customizations
applied by this role's variables.

Example: if you have a theme in https://github.com/open-craft/edx-theme/tree/harvard-dcex:
- Set EDXAPP_COMPREHENSIVE_THEME_SOURCE_REPO: "https://github.com/open-craft/edx-theme/"
- and EDXAPP_COMPREHENSIVE_THEME_VERSION: "harvard-dcex"

If you don't use a skeleton theme, the deployed theme will just contain the SASS
variables definitions you provide through the other variables, and the static files
you provide. For simple changes like colors+logo+image this will be enough.

Static files (like logo and favicon) will be added from the following sources and in
the following order:
- If no skeleton theme nor static files are provided, the theme will have no static files
- If a skeleton theme was provided, its static files will be used
- Local files from SIMPLETHEME_STATIC_FILES_DIR will be copied, replacing previous ones
- Files from SIMPLETHEME_STATIC_FILES_URLS will be downloaded, replacing previous ones

Testing
*******

The intended use of this role is to be run as part of deploy, not after it.

There are other cases in which you may want to run the role independently (after
 the instance is running):
- When testing this role.
- If you plan to use it to deploy theme changes. Be aware that this will
  overwrite the old theme.

You can use ansible-playbook to test this role independently.
It requires you to pass more variables manually because they're not available
except when running inside "edxapp" role. For instance you might need to pass
 edxapp_user (e.g. "vagrant" if you test inside devstack).

Example script to test this role, to be run from devstack, from "vagrant" user:
- export PYTHONUNBUFFERED=1
- source /edx/app/edx_ansible/venvs/edx_ansible/bin/activate
- cd /edx/app/edx_ansible/edx_ansible/playbooks
- ansible-playbook -i localhost, -c local run_role.yml -e role=simple_theme  -e CONFIGURATION_VERSION=master -e EDX_PLATFORM_VERSION=master -e EDXAPP_DEFAULT_SITE_THEME=mytheme2 -e '{"SIMPLETHEME_SASS_OVERRIDES": [{"variable": "link-color", "value":"#00b0f0"}, {"variable": "action-primary-bg", "value":"#ff8000"}, {"variable": "action-secondary-bg", "value":"#ff8000"}, {"variable": "theme-colors", "value":"(\"primary\": #ff8000, \"secondary\": #ff8000)"}, {"variable": "button-color", "value":"#ff8000"}], "SIMPLETHEME_EXTRA_SASS": ".global-header { background: #7ec832 } \n .wrapper-footer { background: #7ec832 }"}' -e EDXAPP_COMPREHENSIVE_THEME_SOURCE_REPO="https://github.com/open-craft/edx-theme/" -e EDXAPP_COMPREHENSIVE_THEME_VERSION="harvard-dcex" -e edxapp_user=vagrant -e common_web_group=www-data -e SIMPLETHEME_ENABLE_DEPLOY=true -e '{"SIMPLETHEME_STATIC_FILES_URLS": [{"url": "http://docs.ansible.com/ansible/latest/_static/images/logo_invert.png", "dest":"lms/static/images/logo.png"}, {"url": "http://docs.ansible.com/favicon.ico", "dest":"lms/static/images/favicon.ico"}]}' -e '{"EDXAPP_COMPREHENSIVE_THEME_DIRS":["/edx/var/edxapp/themes"], "EDXAPP_ENABLE_COMPREHENSIVE_THEMING": true}'

Or, if you want to test the task as part of the deployment, change to role=edxapp,
and add  --tags some-custom-tag-that-you-should-add-to-the-task

Note, that header and footer background color need to be overriden using SIMPLETHEME_EXTRA_SASS variable, previously those colors were defined as SASS variables - `$header-bg` and `$footer-bg`. Since Hawthorn they are defined using bootstrap's theming mechanism.

