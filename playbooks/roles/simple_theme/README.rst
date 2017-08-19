Simple theme
############

This role allows you to deploy a basic theme on deploy time. The theme can be
customized via ansible variables. You can also change the contents of some pages.

This role will be included by edxapp. The main use case involves deploying a
theme as part of deploying an instance.

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
variables definitions you provide through the other variables.

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
- ansible-playbook -i localhost, -c local run_role.yml -e role=simple_theme  -e configuration_version=master -e edx_platform_version=master -e EDXAPP_DEFAULT_SITE_THEME=mytheme2 -e '{"SIMPLETHEME_SASS_OVERRIDES": [{"variable": "main-color", "value":"#823456"}, {"variable": "action-primary-bg", "value":"$main-color"}]}' -e EDXAPP_COMPREHENSIVE_THEME_SOURCE_REPO="https://github.com/open-craft/edx-theme/" -e EDXAPP_COMPREHENSIVE_THEME_VERSION="harvard-dcex" -e edxapp_user=vagrant -e common_web_group=www-data -e SIMPLETHEME_ENABLE_DEPLOY=true -e '{"EDXAPP_COMPREHENSIVE_THEME_DIRS":["/edx/var/edxapp/themes"], "EDXAPP_ENABLE_COMPREHENSIVE_THEMING": true}'


Or, if you want to test the task as part of the deployment, change to role=edxapp,
and add  --tags some-custom-tag-that-you-should-add-to-the-task
