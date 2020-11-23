User Retirement Pipeline.
#########################

In the Open edX platform, the user experience is enabled by several
services, such as LMS, Studio, ecommerce, credentials, discovery, and
more. Personally Identifiable Identification (PII) about a user can
exist in many of these services. As a consequence, to remove a user’s
PII, you must be able to request each service containing PII to remove,
delete, or unlink the data for that user in that service.

In the user retirement feature, a centralized process (the driver
scripts) orchestrates all of these requests. For information about how
to configure the driver scripts, see Setting Up the User Retirement
Driver Scripts.

`More info
here. <https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/user_retire/implementation_overview.html>`__

Configuration & Deployment
**************************

The user retirement pipeline can be deployed together with the edxapp
role, on small deployments that use a single AppServer to host all
services, or standalone, which is the default for bigger installs.

You can also use ansible-playbook to test this role independently. It
requires you to pass more variables manually because they're not
available except when running inside "edxapp" role.

When running this role, you'll need to set:

-  ``COMMON_RETIREMENT_SERVICE_SETUP``: Set to true to configure the
   retirement service pipeline
-  ``RETIREMENT_SERVICE_COOL_OFF_DAYS``: Number of days that an account
   stays marked for deletion before being picked up be the retirement
   service
-  ``RETIREMENT_SERVICE_ENABLE_CRON_JOB``: Set to true if you want to
   set up a daily cron job for the retirement service
-  ``EDXAPP_RETIREMENT_SERVICE_USER_EMAIL``: Email of the retirement
   worker user set up on LMS
-  ``EDXAPP_RETIREMENT_SERVICE_USER_NAME``: Username of the retirement
   worker user set up on LMS
-  ``RETIREMENT_SERVICE_EDX_OAUTH2_KEY``: OAuth2 client id from LMS
-  ``RETIREMENT_SERVICE_EDX_OAUTH2_SECRET``: OAuth2 client secret from
   LMS
-  ``RETIREMENT_LMS_BASE_URL``: Full LMS url
   (e.g. ``https://lms.domain.com``)
-  ``RETIREMENT_ECOMMERCE_BASE_BASE_URL``: Full LMS url
   (e.g. ``https://lms.domain.com``)
-  ``RETIREMENT_CREDENTIALS_BASE_URL``: Full LMS url
   (e.g. ``https://lms.domain.com``)

To use a custom retirement pipeline, you'll need to configure the git
remotes and also the retirement pipeline "steps".

To set up the git repository, you can follow this template:

::

   RETIREMENT_SERVICE_GIT_IDENTITY: !!null
   RETIREMENT_SERVICE_GIT_REPOS:
     - PROTOCOL: "https"
       DOMAIN: "github.com"
       PATH: "edx"
       REPO: "tubular.git"
       VERSION: "master"
       DESTINATION: "{{ retirement_service_app_dir }}"
       SSH_KEY: "{{ RETIREMENT_SERVICE_GIT_IDENTITY }}"

And to set up the retirement pipeline, you'll need to set
``RETIREMENT_SERVICE_PIPELINE_CONFIGURATION`` according to the following
example:

::

   RETIREMENT_SERVICE_PIPELINE_CONFIGURATION:
     - NAME: "RETIRING_ENROLLMENTS"
       NAME_COMPLETE: "ENROLLMENTS_COMPLETE"
       SERVICE: "LMS"
       FUNCTION: "retirement_unenroll"
     - NAME: "RETIRING_LMS_MISC"
       NAME_COMPLETE: "LMS_MISC_COMPLETE"
       SERVICE: "LMS"
       FUNCTION: "retirement_lms_retire_misc"
     - NAME: "RETIRING_LMS"
       NAME_COMPLETE: "LMS_COMPLETE"
       SERVICE: "LMS"
       FUNCTION: "retirement_lms_retire"

You can also test this role on your Docker devstack, like this:

1. Clone this branch to ``./src`` folder of your ``master`` devstack.
2. From the ``devstack`` folder, run ``make lms-shell`` and edit
   ``lms.env.json`` to set these variables:

::

   ....
   "RETIRED_USER_SALTS": ["oWiJVxbtp86kEV4jAHcZXSoSucSSF6GE6qjFA8rZp8yBPMSwKM",],
   "EDXAPP_RETIREMENT_SERVICE_USER_NAME": "retirement_service_worker",
   "RETIREMENT_STATES": [
       "PENDING",
       "RETIRING_ENROLLMENTS",
       "ENROLLMENTS_COMPLETE",
       "RETIRING_LMS_MISC",
       "LMS_MISC_COMPLETE",
       "RETIRING_LMS",
       "LMS_COMPLETE",
       "RETIRING_CREDENTIALS",
       "CREDENTIALS_COMPLETE",
       "ERRORED",
       "ABORTED",
       "COMPLETE"
   ],
   ...
   "FEATURES": {
       ...
       "ENABLE_ACCOUNT_DELETION": true
   }

3. Populate the retirement states:

::

    ./manage.py lms --settings=devstack_docker populate_retirement_states

3. Create the user and OAuth2 Credentials for the retirement worker:

::

   app_name=retirement
   user_name=retirement_service_worker
   ./manage.py lms --settings=<your-settings> manage_user $user_name $user_name@example.com --staff --superuser
   ./manage.py lms --settings=<your-settings> create_dot_application $app_name $user_name

Take a note of the generated client id and secret, you'll need it to set
up the retirement scripts. 4. Now, use the Ansible Role to set up the
User Retirement Pipeline:

::

   export PYTHONUNBUFFERED=1
   source /edx/app/edx_ansible/venvs/edx_ansible/bin/activate
   cd /edx/src/configuration/playbooks
   ansible-playbook \
     -i localhost, \
     -c local run_role.yml \
     -e role=user_retirement_pipeline \
     -e CONFIGURATION_VERSION=master \
     -e EDX_PLATFORM_VERSION=master \
     -e edxapp_user=root \
     -e COMMON_RETIREMENT_SERVICE_SETUP=true \
     -e RETIREMENT_SERVICE_COOL_OFF_DAYS=0 \
     -e RETIREMENT_SERVICE_ENABLE_CRON_JOB=true \
     -e EDXAPP_RETIREMENT_SERVICE_USER_EMAIL=retirement_service_worker@example.com \
     -e EDXAPP_RETIREMENT_SERVICE_USER_NAME=retirement_service_worker \
     -e RETIREMENT_SERVICE_EDX_OAUTH2_KEY=<CLIENT ID FROM PREVIOUS STEP> \
     -e RETIREMENT_SERVICE_EDX_OAUTH2_SECRET=<CLIENT SECRET FROM PREVIOUS STEP>

3. Check that the retirement pipeline is correctly set up at
   ``/edx/app/retirement_service``.
4. Create some users and go the their account page and mark them for
   deletion. |mar|
5. Check
   `here <http://edx.devstack.lms:18000/admin/user_api/userretirementrequest/>`__
   if the retirement requests have been registered.
6. Run the retirement script as root:

::

   /edx/app/retirement_service/retire_users.sh

.. |mar| image:: https://user-images.githubusercontent.com/27893385/53957569-6b9da180-40bd-11e9-9139-10c62e499ec4.png

