# Changelog
All notable changes to this project will be documented in this file.
Add any new changes to the top(right below this line).


 - 2020-12-02
    - Role: mfe
        - Added logo-related configuration settings, with defaults.

 - 2020-12-01
    - Role: edxapp
        - Default the CodeJail Python version to the same as the rest of edxapp.

     - Role: edxapp
        - Added `EDXAPP_ORGANIZATIONS_AUTOCREATE` variable with default of
          `true`. See `ORGANIZATIONS_AUTOCREATE` toggle documentation in
          edx-platform/cms/envs/common.py for details.

 - 2020-11-20
    - Role: edxapp
        - Updated the worker newrelic config to have the service variant in the app name.  This will seperate the names
          of the newrelic apps to be `...-lms` and `...-cms` to make it easier to monitor them separately.  This will
          impact any newrelic monitoring and alerting you have that is linked to the old app name, which should be
          updated to use both of the new application names.
 - 2020-11-17
    - Removed mentions of ANSIBLE_REPO and ANSIBLE_VERSION since we no longer use our own fork of Ansible.

 - 2020-11-10
     - Role: mfe
       - Added role deploy to deploy MFE in a single machine with nginx.
     - Open edX
       - Use new role to deploy gradebook, profile and account MFEs in native installation.

 - 2020-11-04
     - Role: edxapp
       - Stopped rendering legacy auth and env json files that edxapp is no longer reading. Rendering can be reenabled by setting EDXAPP_ENABLE_LEGACY_JSON_CONFIGS to true

 - 2020-10-27
     - Role: notifier
       - Removed the notifier role (see DEPR-106 for details)

 - 2020-10-13
     - Role: forums
        - Add settings for ES7 upgrade.

 - 2020-09-23
     - Role: certs
       - Changed Python version used for creating virtualenv from the system's default (2.7) to 3.8.

 - 2020-09-18
     - Role: nginx
       - Add location to support accessing files from `EDXAPP_MEDIA_URL` under the cms site.

 - 2020-09-14
     - Playbook: program_manager
       - Removed. It is replaced by program_console

     - Role: program_manager
       - Removed. It is replaced by program_console

 - 2020-09-10
     - Playbook: program_console
       - Added playbook to setup program-console micro-frontend application on sandboxes
       - This is created to replace the program_manager application. The app was renamed

     - Role: program_console
       - Created the program-console role for micro-frontend application to be setup
       - This is created to replace the program_manager role. The app was renamed

 - 2020-09-03
     - Role: edxapp
        - Added `EDXAPP_FEATURES_DEFAULT` and `EDXAPP_FEATURES_EXTRA` that are combined into `EDXAPP_FEATURES` allowing for future options to be added as needed during provisioning.
        - Added `EDXAPP_AUTH_USE_OPENID_PROVIDER` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_COMBINED_LOGIN_REGISTRATION` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_CORS_HEADERS` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_COUNTRY_ACCESS` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_CROSS_DOMAIN_CSRF_COOKIE` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_DISCUSSION_HOME_PANEL` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_DISCUSSION_SERVICE` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_ENROLLMENT_RESET` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_GRADE_DOWNLOADS` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_INSTRUCTOR_ANALYTICS` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_LTI_PROVIDER` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_SPECIAL_EXAMS` to allow creating/updating the configuration values during provisioning.
        - Added `EDXAPP_ENABLE_VIDEO_UPLOAD_PIPELINE` to allow creating/updating the configuration values during provisioning.

 - 2020-08-26
     - Role: whitelabel
       - Removes the whitelabel role and all associated configuration for whitelabel sites.

 - 2020-08-17
     - Role: nginx
       - Added `NGINX_ALLOW_PRIVATE_IP_ACCESS` boolean, which allows to disable handling the IP disclosure within private subnetworks.
         This is needed by ELB to run health checks while using encrypted connection between ELB and AppServer (`NGINX_ENABLE_SSL`).
         Without this enabled, ELB will get `403` response when trying to reach the AppServer via its IP address (it is still impossible to specify the `Host` header for the health check).

 - 2020-08-01
     - Role: edxapp
       - Added `EDXAPP_SITE_CONFIGURATION` to allow creating/updating the `SiteConfiguration` values during provisioning.

 - 2020-07-27
     - Role: all
       - Convert ansible lowercase variables to upercase.

 - 2020-07-24
    - Role: newrelic_mongo_monitor
      - Added the new newrelic_mongo_monitor role and playbook for configuring newrelic infrastructure agent mongodb
        integration.

 - 2020-06-30
    - Role: edxapp
      - Added COURSE_CATALOG_URL_ROOT that contains root url of course catalog service (discovery service).

 - 2020-06-02
     - Role: edxapp
       - Add a new `edxapp_sandbox_python_version` variable that deterimens the python version of the edxapp sandbox
       used for instructor python code.  This will default to `python3.5` but can be reverted to `python2.7` if necessary.

 - 2020-05-06
     - Role: all
       - Split the COMMON_SANDBOX_BUILD variable with its two components: SANDBOX_CONFIG and CONFIGURE_JWTS.

       - Disable install of private requirements for docker devstack.
 - 2020-05-05
     - Role: edxapp
       - enable paver autocomplete in docker devstack

 - 2020-04-24
         Must be set if user credentials are in the connection string, or use `""` if no user credentials required.
 - 2020-04-21
     - Role: forum
       - Added `FORUM_MONGO_AUTH_MECH` to allow the authentication mechanism to be configurable.
         Defaults to `":scram"`, which is supported by Mongo>=3.0, because `":mongodb_cr"` is removed in Mongo>=4.0.
         Use `":mongodb_cr"` for mongo 2.6.

 - 2020-04-14
     - Docker: edxapp

     - Roles: edx_django_service, registrar, enterprise_catalog
       - Moved celery worker supervisor config files/scripts into edx_django_service
       - Removed the following variables
         - ENTERPRISE_CATALOG_WORKER_DEFAULT_STOPWAITSECS
         - ENTERPRISE_CATALOG_CELERY_HEARTBEAT_ENABLED
         - REGISTRAR_WORKER_DEFAULT_STOPWAITSECS
         - REGISTRAR_CELERY_HEARTBEAT_ENABLED
         - ENTERPRISE_CATALOG_WORKERS_ENABLE_NEWRELIC_DISTRIBUTED_TRACING
         - ENTERPRISE_CATALOG_NEWRELIC_WORKERS_APPNAME
         - REGISTRAR_WORKERS_ENABLE_NEWRELIC_DISTRIBUTED_TRACING
         - REGISTRAR_NEWRELIC_WORKERS_APPNAME

 - 2020-03-31
     - Role: edxapp
       - Added Stanford-developed Image Modal XBlock.

 - 2020-03-23
     - Role: edxapp
       - Added Stanford-developed SQL Grader XBlock.

 - 2020-03-04

     - Role: mount_ebs
       - Added check for disk size, size is now a required parameter in variables volumes and MONGO_VOLUMES
       - This is to prevent mounting the wrong volumes when AWS swaps the order

     - Role: all
       - Removed OPENID settings

     - Role: all
       - Removed all settings with OIDC in name

 - 2020-02-26
     - Role: edxapp
       - Added `ENTERPRISE_LEARNER_PORTAL_HOSTNAME` env var for lms.

 - 2020-02-25
     - Role: all
       - Removed the unused task timing callback plugin.
 - 2020-02-24
     - Role: ecommerce
       - Added `ENTERPRISE_LEARNER_PORTAL_HOSTNAME` env var for ecommerce.

 - 2020-01-31
     - Role: edxapp
       - Added Stanford-developed Free Text Response XBlock.

     - Role: edxapp
       - Added Stanford-developed Submit-and-Compare XBlock.

 - 2020-01-29
     - Role: edxapp
       - Added Stanford-developed Qualtrics and In-Video Quiz XBlocks.

     - Open edX
       - Don't use AWS_GATHER_FACTS, it was only for tagging which we don't need.

 - 2020-01-24
     - Open edX
       - The wrong version of xqueue was being installed, fixed.


       `EDXAPP_RETIREMENT_SERVICE_USER_NAME` to generic_env_config to allow user retirement to be configurable.
 - 2020-01-21
     - Role: enterprise_catalog
       - Added infrstructure to start up and deploy celery workers

 - 2020-01-07
     - Role: insights
       - install libssl-dev, needed for mysqlclient
 - 2020-01-03
     - Role: insights
       - add DOT config (deprecate DOP)

 - 2019-12-26
     - Role: edxapp
       - Added Celery worker `prefetch_optimization` option to allow switching from 'default' to 'fair' (only write to available worker processes)

 - 2019-12-20
     - Open edX
       - native.sh needed to uninstall pyyaml to proceed

 - 2019-12-09
     - Role: enterprise_catalog
       - Create role

 - 2019-12-04
     - Role: blockstore
       - Increased upload limit to 10M

 - 2019-11-12
     - Role: ecommerce
       - Fixed paypal payment processor default configuration

 - 2019-08-30
     - Role: edxapp
       - Added `ENABLE_PUBLISHER` for indicating that the publisher frontend service is in use

     - Role: discovery
       - Added `ENABLE_PUBLISHER` for indicating that the publisher frontend service is in use

 - 2019-08-02
     - Role: edxapp
       - Added `ENABLE_ENROLLMENT_RESET` feature flag for masters integration sandboxes

 - 2019-08-01
     - Role: conductor
       - New role added to configure the conductor service

       - Set CORS_ORIGIN_WHITELIST.
 - 2019-07-22
     - Role: jwt_signature
       - Added role to inject JWT signing keys into application config, used from edxapp, worker, and registrar.

 - 2019-07-15
     - Playbook: masters_sandbox_update
       - Create edx partner

 - 2019-07-12
     - Role: registrar
       - Set CSRF_TRUSTED_ORIGINS.

     - Role: registrar

 - 2019-07-11
     - Role: discovery
       - Override DISCOVERY_MYSQL_REPLICA_HOST to `edx.devstack.mysql` in docker.

 - 2019-07-10
     - Playbook: masters_sandbox
       - Include call to create_api_access_request

 - 2019-07-09
     - Role: discovery
       - Add mysql replica settings to env config.

 - 2019-07-05
     - Playbook: program_manager
       - Added playbook to setup program-manager micro-frontend application on sandboxes

     - Role: program_manager
       - Created the program-manager role for micro-frontend application to be setup

 - 2019-06-24
     - Role: common_vars
       - Default `COMMON_JWT_PUBLIC_SIGNING_JWK_SET` to `''`
         instead of `!!null`. Because of how this setting is handled,
         `!!null` ends up rendering as the literal string `None` instead
         of the value `null`, which causes JSON decoding to fail
         wherever the default value is used (as `'None'` is not valid JSON).
         By setting the default to a Falsy value like the
         empty string, edx-drf-extensions does not attempt to JSON-
         decode it.

 - 2019-06-20
     - Playbook: masters_sandbox
       - Added playbook to setup user and api access

 - 2019-06-19
     - Role: registrar
       - Changed `REGISTRAR_CELERY_ALWAYS_EAGER` default to `false`.

     - Role: registrar
       - Added `REGISTRAR_CELERY_ALWAYS_EAGER` with default `True`.
       - Injected above settings as environment variable for Registrar.

     - Role: supervisor
       - Add registrar to `pre_supervisor_checks.py`

     - Role: registrar
       - Added `registrar-workers.conf.j2`
       - Add task to generate `registrar-workers.conf` from `registrar-workers.conf.j2`
       - Added `REGISTRAR_WORKERS_ENABLE_NEWRELIC_DISTRIBUTED_TRACING`
       - Added `REGISTRAR_WORKER_DEFAULT_STOPWAITSECS`
       - Added `REGISTRAR_CELERY_HEARTBEAT_ENABLED`
       - Added `REGISTRAR_NEWRELIC_WORKERS_APPNAME`
       - Added `REGISTRAR_CELERY_WORKERS`

     - Role: registrar
       - Added `REGISTRAR_CELERY_BROKER_TRANSPORT`.
       - Added `REGISTRAR_CELERY_BROKER_USER`.
       - Added `REGISTRAR_CELERY_BROKER_PASSWORD`.
       - Added `REGISTRAR_CELERY_BROKER_HOSTNAME`.
       - Added `REGISTRAR_CELERY_BROKER_VHOST`.
       - Injected all above settings as environment variables for Registrar.

     - Role: registrar
       - Added `REGISTRAR_API_ROOT`
       - Modified `REGISTRAR_MEDIA_URL`.

     - Role: edx_django_service
       - Added new overridable variable `edx_django_service_api_root`

     - Role: registrar
       - Replaced `REGISTRAR_MEDIA_ROOT`.
       - Added `REGISTRAR_MEDIA_STORAGE_BACKEND`.

     - Role: registrar
       - Replaced `REGISTRAR_LMS_URL_ROOT` with `REGISTRAR_LMS_BASE_URL`.
       - Replaced `REGISTRAR_DISCOVERY_API_URL` with `REGISTRAR_DISCOVERY_BASE_URL`.

     - Role: registrar
       - Added `REGISTRAR_SEGMENT_KEY` for segment.io event tracking.

     - Role: registrar
       - Added `REGISTRAR_SOCIAL_AUTH_EDX_OAUTH2_KEY` for oauth2.
       - Added `REGISTRAR_SOCIAL_AUTH_EDX_OAUTH2_SECRET` for oauth2.
       - Added `REGISTRAR_BACKEND_SERVICE_EDX_OAUTH2_KEY` for backend auth.
       - Added `REGISTRAR_BACKEND_SERVICE_EDX_OAUTH2_SECRET` for backend auth.
       - Added `REGISTRAR_SERVICE_USER_EMAIL` to have a registrar service user on LMS
       - Added `REGISTRAR_SERVICE_USER_NAME` to have a registrar service user on LMS

     - Role: registrar
       - Create role

 - 2019-06-12
     - Role: oauth_client_setup
       - Ensure that created DOT applications have corresponding ApplicationAccess records with user_id scope.

     - Role: edx_notes_api
       - Added `EDX_NOTES_API_HOSTNAME` to set a hostname for the edx-notes-api IDA.

     - Open edX
       - Added `SANDBOX_ENABLE_NOTES` to enable/disable setting up the edx-notes-api IDA.

 - 2019-06-05
     - Role: registrar
       - Change default celery queue to `registrar.default`, explicitly set default exchange and routing key.

 - 2019-05-24
     - Role: xserver
       - Remove xserver from sandbox builds.

     - Role: registrar
       - Add registrar to sandbox builds.

 - 2019-05-10
     - Role: edxapp
       - Added ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS to allow for edx specific query params to be added for business marketing footer.

 - 2019-05-09
     - Role: designer
 - 2019-05-08
       - Create role

 - 2019-04-16
     - Role: edxapp
       - Removed the OfficeMix XBlock (the service that it uses has been dead for months).

 - 2019-03-28
     - Role: edxapp
       - Added 'SYSTEM_WIDE_ROLE_CLASSES' for use of edx-rbac roles in the jwt in the lms

 - 2019-02-20
     - Open edX
       - Renamed edx_sandbox.yml to openedx_native.yml

     - Role: nginx
       - Added CORS Access-Control-Allow-Origin for static assets.
       - Replaced wildcard Access-Control-Allow-Origin header for fonts. Make sure you set EDXAPP_CORS_ORIGIN_WHITELIST to include all your domains.

 - 2019-02-14
     - Role: ecomworker
       - Added `assignment_email` default template value in `SAILTHRU` config to send offer assignment emails.

       - Added CORS_ORIGIN_WHITELIST and CORS_URLS_REGEX to allow selective CORS whitelisting of origins/urls.

       - Remove unused JWT_SECRET_KEYS.
       - Transformed the JWT_ISSUERS to match the format expected by edx-drf-extensions jwt_decode_handler.
 - 2019-02-11

 - 2019-02-05
     - Role: ecommerce
     - common_vars
       - Added new overridable variable `COMMON_LMS_BASE_URL`.

 - 2019-01-18
     - Role: discovery
       - Added `DISCOVERY_CORS_ORIGIN_WHITELIST` to allow CORS whitelisting of origins.

 - 2019-01-14
     - Role: nginx
       - Modified robots.txt.j2 to accept the Allow rule.
       - Modified robots.txt.j2 to accept either a single string or a list of strings for agent, disallow, and allow.

 - 2019-01-09
     - abbey.py
       - Removed abbey.py

 - 2019-01-03
       - Render auth and env config to a single yml file
 - 2019-01-02
     - Role: edxapp
       - Renamed proctoring backend setting to work with edx-proctoring 1.5.0

 - 2018-11-20
     - Role: edxapp
       - Remove low priority queue, use default instead.

 - 2018-11-14
     - Role: ecommerce



 - 2018-11-07
     - Role: ecommerce
 - 2018-11-05
     - Role: edxapp
       - Added `ENTERPRISE_CUSTOMER_SUCCESS_EMAIL` to lms_env_config for configuring emails to the customer success team.
 - 2018-10-31
     - Role: edx_django_service
       - Added new overridable variable `edx_django_service_gunicorn_max_requests`
     - Role: ecommerce
       - Set default max_requests to 3000.(eg. restart gunicorn process every 3000 requests.)

 - 2018-10-03
     - Role: edx_notes_api
       - Added `JWT_AUTH` to edx-notes-api that is used in other IDAs.

 - 2018-10-01
     - Role: edxapp
       - Removed `PASSWORD_MIN_LENGTH`, `PASSWORD_MAX_LENGTH`, and `PASSWORD_COMPLEXITY` in favor of specifying these in `AUTH_PASSWORD_VALIDATORS`.

     - Role: edxapp
       - Added `AUTH_PASSWORD_VALIDATORS` to utilize Django's password validation. Base validators included in configuration are UserAttributeSimilarity to test the password against the username and email using the default similarity threshold of 0.7 (1.0 fails exact matches only), MinimumLength to test password minimum length, and MaximumLength to test password maximum length.

 - 2018-09-29
     - Role: edxapp
       - Added `EDXAPP_LOGIN_REDIRECT_WHITELIST` which provides a whitelist of domains to which the login/logout pages will redirect.

 - 2018-09-17

     - Role: edxapp
       - `EDXAPP_EDXAPP_SECRET_KEY` no longer has a default value

 - 2018-08-30
     - Role: edxapp
       - `EDXAPP_CACHE_BACKEND` added to allow overriding Django's memcache backend

 - 2018-08-28
     - Role: prospectus
       - New role added to configure the prospectus service

 - 2018-08-14
     - Removed the obsolete install_stack.sh file (the last reference to fullstack)

 - 2018-08-07
     - Role: analytics_api
       - Added `basic_auth_exempted_paths` configuration for enterprise api endpoints

 - 2018-08-06
     - Role: edx_django_service
       - Added optional `edx_django_service_allow_cors_headers` boolean option to pass CORS headers (`Access-Control-Allow-Origin` and `Access-Control-Allow-Methods`) on non basic-auth
       calls to support `/api` endpoints for analytics_api.

 - 2018-08-03
     - Role: edxapp
       - `EDXAPP_X_FRAME_OPTIONS` added in studio to prevent clickjacking.

 - 2018-08-02
     - Role: analytics_api
       - Added `ANALYTICS_API_CORS_ORIGIN_WHITELIST` to allow CORS whitelisting of origins.

 - 2018-07-31
     - Role: nginx
       - Added `NGINX_EDXAPP_PROXY_INTERCEPT_ERRORS` to be able to use custom static error pages for error responses from the LMS.
       - Added `NGINX_SERVER_HTML_FILES_TEMPLATE` to make the error file template configurable.
       - Added `NGINX_SERVER_STATIC_FILES` to allow copying static contents to the server static folder. Can be used to deploy static contents for the error pages for example.

     - Role: edxapp
       - Added `EDXAPP_X_FRAME_OPTIONS` to prevent click jacking in LMS.

 - 2018-07-11
       - sandbox.sh has been renamed native.sh to better indicate what it does.
 - 2018-07-10
     - git_clone:
       - The working tree is explicitly checked for modified files, to prevent mysterious failures.

 - 2018-07-05
     - Installation
       - OPENEDX_RELEASE is now required, to prevent accidental installation of master.

 - 2018-06-21
     - XQueue
       - Expose CLOUDWATCH_QUEUE_COUNT_METRIC which is defined XQueue's settings.py for further dictionary structure

 - 2018-06-12
     - Role: edxapp
       - Create EDXAPP_CMS_GUNICORN_TIMEOUT and EDXAPP_LMS_STATIC_URL_BASE to allow overriding of the gunicorn timeout

 - 2018-06-11
     - nginx:
       - remove nginx_cfg - an internal variable that was really only used for the edx-release nginx site, which served version.{html,json} off of a nonstandard port.  The file it served was never populated.

 - 2018-06-07
     - Structure: edx-east
       - Deprecated the edx-east folder, playbooks now live in the top level directory instead of edx-east/playbooks. A symbolic link was added for now, but should not be relied upon.

       - EDXAPP_LMS_STATIC_URL_BASE and EDXAPP_CMS_STATIC_URL_BASE allow a per-application setting of the static URL.  You can stil use EDXAPP_STATIC_URL_BASE for now but we may retire that as we continue to separate LMS and CMS.
 - 2018-06-06
     - Role: edxapp
       - EDXAPP_NGINX_SKIP_ENABLE_SITES added to allow you to not sync in the lms or cms nginx configuration.  Instead you can enable them during deployment.
       - EDXAPP_NGINX_DEFAULT_SITES added to allow you to mark both lms and cms as defaults, best paired with picking which site to enable during deployment.

 - 2018-05-11
       - XQUEUE_SETTINGS now prefers production.py over aws_settings.py
 - 2018-05-09
     - Role: credentials
       - Set `LANGUAGE_COOKIE_NAME` so that Credentials will use the global language cookie.

 - 2018-05-08
     - Role: edxapp
       - Added `PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG` to make configurable whether password complexity is checked on login and how such complexity is rolled out to users.

 - 2018-05-03
     - Role: XQueue
       - Convert to a yaml config (instead of xqueue.auth.json and xqueue.env.json we get xqueue.yml and it lives by default in /edx/etc/xqueue.yml like standard IDAs)
       - Add XQUEUE_DEFAULT_FILE_STORAGE so that you can specify S3 or Swift in your config

 - 2018-04-25
     - Role: edxapp
       - Added `RETIREMENT_STATES` to generic_env_config to support making the retirement workflow configurable.

 - 2018-04-19
     - Removed Vagrantfiles for devstack and fullstack, and supporting files.

     - Role: xqueue
       - Added XQUEUE_SUBMISSION_PROCESSING_DELAY and XQUEUE_CONSUMER_DELAY to xqueue env so they can be passed along to the app.

 - 2018-04-13
     - Role: edxapp
       - Added GOOGLE_SITE_VERIFICATION_ID to move a previously hardcoded value into configuration.
       - Changed `EDXAPP_RETIRED_USERNAME_FMT` to `EDXAPP_RETIRED_USERNAME_PREFIX`. Changed/split `EDXAPP_RETIRED_EMAIL_FMT` to be `EDXAPP_RETIRED_EMAIL_PREFIX` and `EDXAPP_RETIRED_EMAIL_DOMAIN`.

         XQUEUE_RABBITMQ_USER XQUEUE_RABBITMQ_PASS XQUEUE_RABBITMQ_VHOST XQUEUE_RABBITMQ_HOSTNAME

       - Added `EDXAPP_RETIRED_USERNAME_FMT`, `EDXAPP_RETIRED_EMAIL_FMT`, `EDXAPP_RETIRED_USER_SALTS`, and
 - 2018-04-12
       - Retired XQUEUE_WORKERS_PER_QUEUE
 - 2018-04-11
     - Role: edxapp
       - Moved `PASSWORD_MIN_LENGTH`, `PASSWORD_MAX_LENGTH`, and `PASSWORD_COMPLEXITY` to generic_env_config to allow CMS and LMS to share these configurations

 - 2018-04-09
       - Added XQUEUE_CONSUMER_NEWRELIC_APPNAME which is added to the supervisor start of xqueue_consumer
         if you have New Relic enabled.
 - 2018-04-04
     - Role xqueue
       - Removed RabbitMQ in earlier changes in XQueue itself, we don't need any of the configuration
         XQUEUE_RABBITMQ_PORT XQUEUE_RABBITMQ_TLS
 - 2018-04-02
       - Added NEWRELIC_APPNAME and NEWRELIC_LICENSE_KEY to the configuration files consumed by XQueue.
         Useful for external utilities that are reporting NR metrics.
     - Role: edxapp

 - 2018-03-28
     - Role: xqueue
       - Added XQUEUE_MYSQL_CONN_MAX_AGE so that you can have xqueue use django's persistent DB connections
 - 2018-03-22
     - Role edx_django_service
       - Added maintenance page under the flag EDX_DJANGO_SERVICE_ENABLE_S3_MAINTENANCE.
       - Added the s3_maintenance.j2 file to point to the s3 maintenance page.


 - 2018-03-20
     - Role: splunkforwarder
       - Updated the role so the splunkforwarder can be installed on Amazon Linux OS environment, which is a RHEL variant

     - Role: server_utils
       - Update to only do things for debian varient environment

 - 2018-03-08
     - Role: edxapp
       - Added empty `EDXAPP_PASSWORD_COMPLEXITY` setting to ease overriding complexity.

 - 2018-02-27
       - The manage_users management command is only run when disable_edx_services is false (previously this play would try
         to update databases while building images, where services are generally disabled).
 - 2018-02-22
     - Role: xqueue
       - Remove S3_BUCKET and S3_PATH_PREFIX - they were deprecated prior to ginkgo
       - Remove SERVICE_VARIANT - it was copied from edxapp but never truly used (except to complicate things)

 - 2018-02-09
       - Added `CERTS_QUEUE_POLL_FREQUENCY` to make configurable the certificate agent's queue polling frequency.
 - 2018-02-06
     - Role: certs

 - 2018-02-02
     - Role: xqueue
       - Added `XQUEUE_SESSION_ENGINE` to allow a configurable xqueue session engine.
       - Added `XQUEUE_CACHES` to allow a configurable xqueue cache.


 - 2018-01-31
     - Role: devpi
       - New role added to configure a devpi service as a pass-through cache for PyPI.

     - Role: devpi_consumer
       - Added role to configure Python containers to use devpi for Docker Devstack

 - 2018-01-26
     - Role: edxapp
       - Added `ENTERPRISE_REPORTING_SECRET` to CMS auth settings to allow edx-enterprise migrations to run.

 - 2018-01-25
     - Role: edxapp
       - Added `EDXAPP_FERNET_KEYS` to allow for use of django-fernet-keys in LMS.
 - 2018-01-04
     - Role: nginx
       - Added `NGINX_EDXAPP_DEFAULT_SITE_THEME` to allow to completely
       override `favicon.ico` file when Comprehensive Theme is enabled.

 - 2017-12-14
     - Role: edxapp
       - Added `EDX_PLATFORM_REVISION` (set from `edx_platform_version`). This is for
       edx-platform debugging purposes, and replaces calling dealer.git at startup.

 - 2017-12-07
     - Role: edxapp
       - Added `EDXAPP_BRANCH_IO_KEY` to configure branch.io journey app banners.

 - 2017-12-06
     - Role: veda_pipeline_worker
       - New role to run all (`deliver, ingest, youtubecallback`) [video pipeline workers](https://github.com/edx/edx-video-pipeline/blob/master/bin/)

     - Role: ecomworker
       - Added `ECOMMERCE_WORKER_BROKER_TRANSPORT` with a default value of 'ampq' to be backwards compatible with rabbit.  Set to 'redis' if you wish to use redis instead of rabbit as a queue for ecommerce worker.

 - 2017-12-05
       - Added `ECOMMERCE_BROKER_TRANSPORT` with a default value of 'ampq' to be backwards compatible with rabbit.  Set to 'redis' if you wish to use redis instead of rabbit as a queue for ecommerce.
 - 2017-12-04
     - Role: ecommerce

 - 2017-12-01
     - Role: credentials
       - This role is now dependent on the edx_django_service role. Settings are all the same, but nearly all of the tasks are performed by the edx_django_service role.

 - 2017-11-29
     - Role: veda_delivery_worker
       - New role added to run [video delivery worker](https://github.com/edx/edx-video-pipeline/blob/master/bin/deliver)

 - 2017-11-23
       - Added `EDXAPP_DEFAULT_COURSE_VISIBILITY_IN_CATALOG` setting (defaults to `both`).

       - Added `EDXAPP_DEFAULT_MOBILE_AVAILABLE` setting (defaults to `false`).

 - 2017-11-21
     - Role: veda_ffmpeg
       - New role added to compile ffmpeg for video pipeline. It will be used as a dependency for video pipeline roles.

 - 2017-11-15
     - Role: nginx
       - Modified `lms.j2` , `cms.j2` , `credentials.j2` , `edx_notes_api.j2` and `insights.j2` to enable HTTP Strict Transport Security
       - Added `NGINX_HSTS_MAX_AGE` to make HSTS header `max_age` value configurable and used in templates
 - 2017-11-14
     - Role: edxapp
       - Added `EDXAPP_MONGO_REPLICA_SET`, which is required to use


 - 2017-11-13

     - Role: edxapp
       - Added `EDXAPP_ZENDESK_OAUTH_ACCESS_TOKEN` for making requests to Zendesk through front-end.
 - 2017-11-09
     - Role: edxapp
       - Added `EDXAPP_LMS_INTERNAL_ROOT_URL` setting (defaults to `EDXAPP_LMS_ROOT_URL`).

 - 2017-11-07
     - Role: edxapp
       - Added `EDXAPP_CELERY_BROKER_TRANSPORT` and renamed `EDXAPP_RABBIT_HOSTNAME`
         to `EDXAPP_CELERY_BROKER_HOSTNAME`. This is to support non-amqp brokers,
         specifically redis. If `EDXAPP_CELERY_BROKER_HOSTNAME` is unset it will use
         the value of `EDXAPP_RABBIT_HOSTNAME`, however it is recommended to update
         your configuration to set `EDXAPP_CELERY_BROKER_TRANSPORT` explicitly.

 - 2017-11-03
     - Role: server_utils
       - Install "vim", not "vim-tiny".

     - Role: edxapp
       - Added GOOGLE_ANALYTICS_TRACKING_ID setting for inserting GA tracking into emails generated via ACE.

 - 2017-10-30
     - Role: edxapp
       - Added `EDXAPP_REINDEX_ALL_COURSES` to rebuild the course index on deploy. Disabled by default.

 - 2017-10-26
     - Role: ecommerce
       - This role is now dependent on the edx_django_service role. Settings are all the same, but nearly all of the tasks are performed by the edx_django_service role.

 - 2017-10-24
     - Role: notifier
       - Added notifier back to continuous integration.

 - 2017-10-20
         pymongo.MongoReplicaSetClient in PyMongo 2.9.1.  This should be set to the
         name of your replica set.
         This setting causes the `EDXAPP_*_READ_PREFERENCE` settings below to be used.
       - Added `EDXAPP_MONGO_CMS_READ_PREFERENCE` with a default value of `PRIMARY`.
       - Added `EDXAPP_MONGO_LMS_READ_PREFERENCE` with a default value of
         `SECONDARY_PREFERED` to distribute the read workload across the replica set
         for replicated docstores and contentstores.
       - Added `EDXAPP_LMS_SPLIT_DOC_STORE_READ_PREFERENCE` with a default value of
         `EDXAPP_MONGO_LMS_READ_PREFERENCE`.
       - Added `EDXAPP_LMS_DRAFT_DOC_STORE_CONFIG` with a default value of
         `EDXAPP_MONGO_CMS_READ_PREFERENCE`, to enforce consistency between
         Studio and the LMS Preview modes.
       - Removed `EDXAPP_CONTENTSTORE_ADDITIONAL_OPTS`, since there is no notion of
         common options to the content store anymore.
 - 2017-10-19
     - Role: veda_web_frontend
       - New role added for [edx-video-pipeline](https://github.com/edx/edx-video-pipeline)

 - 2017-10-07
     - Role: discovery
       - Added `DISCOVERY_REPOS` to allow configuring discovery repository details.

     - Role: edx_django_service
       - Made the keys `edx_django_service_git_protocol`, `edx_django_service_git_domain`, and `edx_django_service_git_path` of `edx_django_service_repos` all individually configurable.

 - 2017-10-05

     - Role: whitelabel
       - Added `WHITELABEL_THEME_DIR` to point to the location of whitelabel themes.
       - Added `WHITELABEL_ADMIN_USER` to specify an admin user.
       - Added `WHITELABEL_DNS` for DNS settings of themes.
       - Added `WHITELABEL_ORG` for whitelabel organization settings.
 - 2017-09-26
     - Role: edxapp
       - Added `EDXAPP_EXTRA_MIDDLEWARE_CLASSES` for configuring additional middleware logic.

 - 2017-09-25
     - Role: discovery
       - Updated LANGUAGE_CODE to generic english. Added configuration for multilingual language package django-parler.

 - 2017-09-14
     - Role: edxapp
       - Added `EDXAPP_SCORM_PKG_STORAGE_DIR`, with default value as it was in the server template.
       - Added `EDXAPP_SCORM_PLAYER_LOCAL_STORAGE_ROOT`, with default value as it was in the server template.

     - Role: edxapp
       - Added `ENTERPRISE_SUPPORT_URL` variable used by the LMS.

 - 2017-09-13
     - Role: discovery
       - Added `OPENEXCHANGERATES_API_KEY` for retrieving currency exchange rates.

 - 2017-09-12
       - Added `EDXAPP_PLATFORM_DESCRIPTION` used to describe the specific Open edX platform.
 - 2017-09-11
     - Role: edxapp
       - Added `EDXAPP_ENTERPRISE_TAGLINE` for customized header taglines for different enterprises.

 - 2017-09-05
     - Role: edxapp
       - Added OAUTH_DELETE_EXPIRED to enable automatic deletion of edx-django-oauth2-provider grants, access tokens, and refresh tokens as they are consumed. This will not do a bulk delete of existing rows.

 - 2017-08-23
     - Role: mongo_3_2
       - Added role for mongo 3.2, not yet in use.
       - Removed MONGO_CLUSTERED variable. In this role mongo replication is always configured, even if there is only one node.

 - 2017-08-16
       - Removed unused `EDXAPP_BOOK_URL` setting
 - 2017-08-08

     - Role: credentials
       - Replaced `CREDENTIALS_OAUTH_URL_ROOT` with `COMMON_OAUTH_URL_ROOT` from `common_vars`
       - Replaced `CREDENTIALS_OIDC_LOGOUT_URL` with `COMMON_OAUTH_LOGOUT_URL` from `common_vars`
       - Replaced `CREDENTIALS_JWT_AUDIENCE` with `COMMON_JWT_AUDIENCE` from `common_vars`
       - Replaced `CREDENTIALS_JWT_ISSUER` with `COMMON_JWT_ISSUER` from `common_vars`
       - Replaced `CREDENTIALS_JWT_SECRET_KEY` with `COMMON_JWT_SECRET_KEY` from `common_vars`
       - Replaced `CREDENTIALS_SOCIAL_AUTH_EDX_OIDC_ISSUER` with `COMMON_JWT_ISSUER` from `common_vars`

     - Role: ecommerce
       - Replaced `ECOMMERCE_OAUTH_URL_ROOT` with `COMMON_OAUTH_URL_ROOT` from `common_vars`
       - Replaced `ECOMMERCE_OIDC_LOGOUT_URL` with `COMMON_OAUTH_LOGOUT_URL` from `common_vars`
       - Replaced `ECOMMERCE_JWT_SECRET_KEY` with `COMMON_JWT_SECRET_KEY` from `common_vars`
       - Replaced `ECOMMERCE_SOCIAL_AUTH_EDX_OIDC_ISSUER` with `COMMON_JWT_ISSUER` from `common_vars`
 - 2017-08-04
     - Role: edxapp
       - Added `PASSWORD_MIN_LENGTH` for password minimum length validation on reset page.
       - Added `PASSWORD_MAX_LENGTH` for password maximum length validation on reset page.
 - 2017-08-03

     - Role: edxapp
       - Added `EDXAPP_VIDEO_TRANSCRIPTS_SETTINGS` to configure S3-backed video transcripts.
 - 2017-07-28
     - Role: edxapp
       - Added creation of enterprise_worker user to provisioning. This user is used by the edx-enterprise package when making API requests to Open edX IDAs.

 - 2017-07-25
     - Role: neo4j
       - Increase heap and page caches sizes for neo4j

 - 2017-07-21

     - Role: edxapp
       - Remove EDXAPP_ANALYTICS_API_KEY, EDXAPP_ANALYTICS_SERVER_URL, EDXAPP_ANALYTICS_DATA_TOKEN, EDXAPP_ANALYTICS_DATA_URL since they are old and
       no longer consumed.

 - 2017-07-18

     - Role: insights
       - Moved `THEME_SCSS` from `INSIGHTS_CONFIG` to `insights_environment`
 - 2017-07-14
     - Role: forum
       - Added `FORUM_REBUILD_INDEX` to rebuild the ElasticSearch index from the database, when enabled.  Default: `False`.


     - Role: insights
       - Removed `bower install` task
       - Replaced r.js build task with webpack build task
 - 2017-07-13
       - Removed `./manage.py compress` task

     - Role: analytics_api
       - Added a number of `ANALYTICS_API_DEFAULT_*` and `ANALYTICS_API_REPORTS_*` variables to allow more selective specification of database parameters (rather than
           overriding the whole structure).
 - 2017-07-06
       - Removed authentication requirement for neo4j
 - 2017-06-30

     - Role: insights
       - Added `INSIGHTS_DOMAIN` to configure the domain Insights is deployed on
       - Added `INSIGHTS_CLOUDFRONT_DOMAIN` to configure the domain static files can be served from
       - Added `INSIGHTS_CORS_ORIGIN_WHITELIST_EXTRA` to configure allowing CORS on domains other than the `INSIGHTS_DOMAIN`
 - 2017-06-28
     - Role: edxapp
       - Let `confirm_email` in `EDXAPP_REGISTRATION_EXTRA_FIELDS` default to `"hidden"`.
       - Let `terms_of_service` in `EDXAPP_REGISTRATION_EXTRA_FIELDS` default to `"hidden"`.


 - 2017-06-27
     - Role: ecommerce
       - Added ECOMMERCE_LANGUAGE_COOKIE_NAME which is the name of the cookie the ecommerce django app looks at for determining the language preference.
 - 2017-06-26
     - Role: neo4j
       - Enabled splunk forwarding for neo4j logs.
       - Increased maximum amount of open files to 40000, as suggested by neo4j.
       - Updated the java build that neo4j uses to run.

 - 2017-06-22

     - Role: edxapp
       - Added `EDXAPP_BASE_COOKIE_DOMAIN` for sharing cookies across edx domains.
 - 2017-06-21
     - Role: edxapp
       - Set the default value for EDXAPP_POLICY_CHANGE_GRADES_ROUTING_KEY to
      'edx.lms.core.default'.

     - Role: edxapp
       - Set the default value for EDXAPP_BULK_EMAIL_ROUTING_KEY_SMALL_JOBS to
      'edx.lms.core.low'.

 - 2017-06-16
     - Role: neo4j
       - Updated neo4j to 3.2.2

 - 2017-06-15
     - Role: jenkins_master
       - Update pinned use of JDK7 in Jenkins installs to default JDK version from role `oraclejdk`.

 - 2017-06-12
     - Role: elasticsearch
       - Replaced `elasticsearch_apt_key` and `elastic_search_apt_keyserver` with `elasticsearch_apt_key_url`
       - Updated elasticsearch version to 1.5.0

 - 2017-06-08
     - Role: edxapp
       - Set the EDXAPP_IMPORT_EXPORT_BUCKET setting to an empty string

 - 2017-06-07
     - Role: edxapp
       - Updated default value of the EDXAPP_ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES setting to ["audit", "honor"]

     - Role: edx_notes_api
       - Removed EDX_NOTES_API_ELASTICSEARCH_HOST.
       - Removed EDX_NOTES_API_ELASTICSEARCH_PORT.
       - EDX_NOTES_API_ELASTICSEARCH_URL.


     - Role: insights
       - Removed `SUPPORT_EMAIL` setting from `INSIGHTS_CONFIG`, as it is was replaced by `SUPPORT_URL`.
 - 2017-06-05

     - Role: insights
       - Removed `INSIGHTS_FEEDBACK_EMAIL` which is no longer used, as it was deemed redundant with `INSIGHTS_SUPPORT_EMAIL`.
 - 2017-06-01
     - Role: nginx
       - Modified `server-template.j2` to be more accessible and configurable.
       - The template should contain the `lang` attribute in the HTML tag.
       - If the image loaded has some meaning, as a logo, it should have the `alt` attribute.
       - After the header 1 (h1) there is no relevant text content, so next it can not be
         another header (h2). It was changed to be a paragraph with the header 2 CSS style.
       - Added `NGINX_SERVER_ERROR_IMG_ALT` with default value as it was in the server template
       - Added `NGINX_SERVER_ERROR_LANG` with default value `en`
       - Added `NGINX_SERVER_ERROR_STYLE_H1` with default value as it was in the server template
       - Added `NGINX_SERVER_ERROR_STYLE_P_H2` with default value as it was in the server template
       - Added `NGINX_SERVER_ERROR_STYLE_P` with default value as it was in the server template
       - Added `NGINX_SERVER_ERROR_STYLE_DIV` with default value as it was in the server template

 - 2017-05-31
     - Role: edxapp
       - Install development.txt in Vagrant and Docker devstacks

 - 2017-05-26
     - Role: edxapp
       - Added the EDXAPP_ACTIVATION_EMAIL_SUPPORT_LINK URL with default value `''`.
       - Added the EDXAPP_PASSWORD_RESET_SUPPORT_LINK URL with default value `''`.

 - 2017-05-23
     - Role: edxapp
       - Added the EDXAPP_SHOW_HEADER_LANGUAGE_SELECTOR feature flag with default value [false]
       - Added the EDXAPP_SHOW_FOOTER_LANGUAGE_SELECTOR feature flag with default value [false]

     - Role: edxapp
       - Added the EDXAPP_ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES setting with default value ["audit"]

 - 2017-05-15
     - Role: nginx
       - Added `NGINX_EDXAPP_CMS_APP_EXTRA`, which makes it possible to add custom settings to the site configuration for Studio.
       - Added `NGINX_EDXAPP_LMS_APP_EXTRA`, which makes it possible to add custom settings to the site configuration for the LMS.

 - 2017-05-04

     - Role: edxapp
       - Added `EDXAPP_VIDEO_IMAGE_SETTINGS` to configure S3-backed video images.
 - 2017-04-24
     - Role: edxapp
       - DOC_LINK_BASE settings have been removed, replaced by HELP_TOKENS_BOOKS

     - Role: edxapp
       - Add the EDXAPP_LANGUAGE_COOKIE setting

 - 2017-04-12
       - Added a new EDXAPP_MYSQL_CONN_MAX_AGE, default to 0.  Adjust it to change how long a connection is kept open
       for reuse before it is closed.
 - 2017-04-11
     - Role: rabbitmq
       - Upgraded to 3.6.9
       - Switched to a PPA rather than a .deb hosted in S3
       - Note that you generally cannot upgrade RabbitMQ live in place https://www.rabbitmq.com/clustering.html
         this is particularly true coming from 3.2 to 3.6.  We are using the shovel plugin to move tasks across clusters
         but their documentation covers different scenarios.
 - 2017-03-31
     - Role: edxapp
       - Set preload_app to False in gunicorn config for LMS and Studio.
 - 2017-03-13

     - Role: edxapp
       - Added `EDXAPP_BLOCK_STRUCTURES_SETTINGS` to configure S3-backed Course Block Structures.
 - 2017-03-07
     - Role: analytics_api
       - Added `ANALYTICS_API_AGGREGATE_PAGE_SIZE`, default value 10.  Adjust this parameter to increase the number of
         aggregate search results returned by the Analytics API, i.e. in course_metadata: enrollment_modes, cohorts, and
         segments.
 - 2017-02-27
     - Role: xqueue
       - Changed `XQUEUE_RABBITMQ_TLS` default from `true` to `false`.
       - Added `XQUEUE_RABBITMQ_TLS` to allow configuring xqueue to use TLS when connecting to the AMQP broker.
       - Added `XQUEUE_RABBITMQ_VHOST` to allow configuring the xqueue RabbitMQ host.
       - Added `XQUEUE_RABBITMQ_PORT` to allow configuring the RabbitMQ port.
       - Added `EDXAPP_CELERY_BROKER_USE_SSL` to allow configuring celery to use TLS.
 - 2017-02-24
     - Role: programs
       - This role has been removed as this service is no longer supported. The role is still available on the [Ficus branch](https://github.com/edx/configuration/releases/tag/open-release%2Fficus.1).
 - 2017-02-16
     - Role: mongo_2_6
       - Added `MONGO_AUTH` to turn authentication on/off. Auth is now enabled by default, and was previously disabled by default.

       - Added `MONGO_AUTH` to turn authentication on/off. Auth is now enabled by default, and was previously disabled by default.
 - 2017-02-14
     - Role: notifier
       - Added `NOTIFIER_DATABASE_ENGINE`, `NOTIFIER_DATABASE_NAME`, `NOTIFIER_DATABASE_USER`, `NOTIFIER_DATABASE_PASSWORD`, `NOTIFIER_DATABASE_HOST`, and `NOTIFIER_DATABASE_PORT` to be able to configure the `notifier` service to use a database engine other than sqlite. Defaults to local sqlite.
       - Deprecated: `NOTIFIER_DB_DIR`: Please use `NOTIFIER_DATABASE_NAME` instead.

 - 2017-02-02
       - Support parsing the replset JSON in 3.2 and 3.0

     - Role: ecommerce
       - Removed `SEGMENT_KEY` which is no longer used.  Segment key is now defined in DB configuration. (https://github.com/edx/ecommerce/pull/1121)
 - 2017-02-01

     - Role: ecommerce
       - Added `ECOMMERCE_ENTERPRISE_URL` for the `enterprise` API endpoint exposed by a new service `edx-enterprise` (currently hosted by `LMS`), which defaults to the existing setting `ECOMMERCE_LMS_URL_ROOT`.
 - 2017-01-12
     - Role: credentials
       - Added `CREDENTIALS_EXTRA_APPS` to enable the inclusion of additional Django apps in the Credentials Service.
 - 2017-01-10
       - Added `COMMON_EDXAPP_SETTINGS`. Default: `aws`
 - 2016-11-18

     - Role: mongo_3_0
       - Changed MONGO_STORAGE_ENGINE to default to wiredTiger which is the default in 3.2 and 3.4 and what edX suggests be used even on 3.0.
         If you have a mmapv1 3.0 install, override MONGO_STORAGE_ENGINE to be mmapv1 which was the old default.
 - 2016-11-03

     - Role: xqueue

     - Role: edxapp
 - 2016-10-27

     - Role: security
       - Changed SECURITY_UPGRADE_ON_ANSIBLE to only apply security updates.  If you want to retain the behavior of running safe-upgrade,
         you should switch to using SAFE_UPGRADE_ON_ANSIBLE.
 - 2016-10-24

     - Role: discovery
       - Added `PUBLISHER_FROM_EMAIL` for sending emails to publisher app users.
 - 2016-10-18

     - Role: edxapp
       - Added `EXPIRING_SOON_WINDOW` to show message to learners if their verification is expiring soon.
 - 2016-10-11

     - Role: edxapp
       - Added COMPREHENSIVE_THEME_LOCALE_PATHS to support internationalization of strings originating from custom themes.
 - 2016-06-30
     - Role: discovery
       - Course Discovery JWT configuration now takes a list of issuers instead of a single issuer.  This change is not backward compatible with older versions of course discovery.

 - 2016-06-22
     - Role: hadoop_common
       - Enable log retention by default to assist with debugging. Now YARN will retain stdout and stderr logs produced by map reduce tasks for 24 hours. They can be retrieved by running "yarn logs -applicationId YOUR_APPLICATION_ID".

 - 2016-06-08

     - Role: Edxapp
       - `EDXAPP_COMPREHENSIVE_THEME_DIR` is deprecated and is maintained for backward compatibility, `EDXAPP_COMPREHENSIVE_THEME_DIRS`
         should be used instead which is a list of directories. `EDXAPP_COMPREHENSIVE_THEME_DIR` if present will have priority over `EDXAPP_COMPREHENSIVE_THEME_DIRS`
       - `COMPREHENSIVE_THEME_DIR` is deprecated and is maintained for backward compatibility, `COMPREHENSIVE_THEME_DIRS` should be used
         instead which is a list of directories. `COMPREHENSIVE_THEME_DIR` if present will have priority over `COMPREHENSIVE_THEME_DIRS`
 - 2016-05-23

     - Role: ecommerce
       - Renamed `ECOMMERCE_COMPREHENSIVE_THEME_DIR` to `ECOMMERCE_COMPREHENSIVE_THEME_DIRS`, `ECOMMERCE_COMPREHENSIVE_THEME_DIRS`
         is now a list of directories. Change is backward incompatible.
       - Renamed `COMPREHENSIVE_THEME_DIR` to `COMPREHENSIVE_THEME_DIRS`, `COMPREHENSIVE_THEME_DIRS` is now a list of directories.
         Change is backward incompatible.
 - 2016-01-25
     - Role: common
       - Renamed `COMMON_AWS_SYNC` to `COMMON_OBJECT_STORE_LOG_SYNC`
       - Renamed `COMMON_AWS_SYNC_BUCKET` to `COMMON_OBJECT_STORE_LOG_SYNC_BUCKET`
       - Renamed `COMMON_AWS_S3_SYNC_SCRIPT` to `COMMON_OBJECT_STORE_LOG_SYNC_SCRIPT`
       - Added `COMMON_OBJECT_STORE_LOG_SYNC_PREFIX`. Default: `logs/tracking/`
     - Role: aws
       - Removed `AWS_S3_LOGS`
       - Added `vhost` role as dependency
     - Role: edxapp
       - Added `EDXAPP_SWIFT_USERNAME`
       - Added `EDXAPP_SWIFT_KEY`
       - Added `EDXAPP_SWIFT_TENANT_ID`
       - Added `EDXAPP_SWIFT_TENANT_NAME`
       - Added `EDXAPP_SWIFT_AUTH_URL`
       - Added `EDXAPP_SWIFT_AUTH_VERSION`
       - Added `EDXAPP_SWIFT_REGION_NAME`
       - Added `EDXAPP_SWIFT_USE_TEMP_URLS`
       - Added `EDXAPP_SWIFT_TEMP_URL_KEY`
       - Added `EDXAPP_SWIFT_TEMP_URL_DURATION`
       - Added `EDXAPP_SETTINGS` to allow using a settings file other than `aws.py`. Default: `aws`
       - Renamed `ENABLE_S3_GRADE_DOWNLOADS` to `ENABLE_GRADE_DOWNLOADS`
       - Replaced `EDXAPP_GRADE_STORAGE_TYPE`, `EDXAPP_GRADE_BUCKET` and `EDXAPP_GRADE_ROOT_PATH` with `EDXAPP_GRADE_STORAGE_CLASS` and `EDXAPP_GRADE_STORAGE_KWARGS`
     - Role: openstack
       - Added role
     - Role: vhost
       - Added as dependency for aws and openstack roles. Handles common functionality for setting up VM hosts
     - Role: xqueue
       - Added `XQUEUE_SETTINGS` to specify which settings file to use. Default: `aws_settings`
       - Renamed `XQUEUE_S3_BUCKET` to `XQUEUE_UPLOAD_BUCKET`
       - Renamed `XQUEUE_S3_PATH_PREFIX` to `XQUEUE_UPLOAD_PATH_PREFIX`

 - 2015-12-15
     - Role: edxapp
       - Removed SUBDOMAIN_BRANDING and SUBDOMAIN_COURSE_LISTINGS variables

 - 2015-12-03
     - Role: ora
       - Remove the ora1 role as support for it was deprecated in Cypress.
       - Removed dependencies on ora throughout the playbooks / vagrantfiles.
 - 2015-11-12
     - Role: edxapp
       - Removed XmlModuleStore from the default list of modulestores for the LMS.
       - EDXAPP_XML_MAPPINGS variable no longer exists by default and is not used by the edxapp role.

 - 2015-11-03
     - Role: ecommerce
       - Removed ECOMMERCE_ORDER_NUMBER_PREFIX variable

 - 2015-09-28
     - Role: edxapp
       - All of the following changes are BACKWARDS-INCOMPATABLE:
         - Renamed two top level variables SEGMENT_IO_LMS_KEY and SEGMENT_IO_KEY to SEGMENT_KEY in {lms|cms].auth.json.
         - Renamed two top level variables in roles/edxapp/defaults/main.yml.  EDXAPP_SEGMENT_IO_LMS_KEY and EDXAPP_SEGMENT_IO_KEY are now EDXAPP_LMS_SEGMENT_KEY and EDXAPP_CMS_SEGMENT_KEY respectively
         - REMOVED two top level variables SEGMENT_IO_LMS and SEGMENT_IO from {lms|cms].auth.json. We will use the existence of the SEGMENT_KEY to to serve the same function that these boolean variables served.
         - REMOVED two top level variables EDXAPP_SEGMENT_IO_LMS and EDXAPP_SEGMENT_IO from roles/edxapp/defaults/main.yml.

 - 2015-08-17
     - Updated ansible fork to be based on ansible 1.9.3rc1 instead of 1.9.1
       - Ansible Changelog: https://github.com/ansible/ansible/blob/stable-1.9/CHANGELOG.md

 - 2015-06-17
     - Role: rabbitmq
       - Removed the RABBITMQ_CLUSTERED var and related tooling. The goal of the var was to be able to setup a cluster in the aws environment without having to know all the IPs of the cluster before hand.  It relied on the `hostvars` ansible varible to work correctly which it no longer does in 1.9.  This may get fixed in the future but for now, the "magic" setup doesn't work.
       - Changed `rabbitmq_clustered_hosts` to RABBITMQ_CLUSTERED_HOSTS.

 - 2015-05-27
     - Role: edxapp
       - Removed deprecated variables EDXAPP_PLATFORM_TWITTER_URL, EDXAPP_PLATFORM_MEETUP_URL, EDXAPP_PLATFORM_LINKEDIN_URL, and EDXAPP_PLATFORM_GOOGLE_PLUS_URL in favor of EDXAPP_SOCIAL_MEDIA_FOOTER_URLS.  These variables haven't been used in edx-platform since March 17, 2015 (when https://github.com/edx/edx-platform/pull/7383 was merged).  This change is backwards incompatible with versions of edx-platform from before March 17, 2015.
       - Added EDXAPP_MOBILE_STORE_URLS and EDXAPP_FOOTER_ORGANIZATION_IMAGE variables, used in https://github.com/edx/edx-platform/pull/8175 (v3 version of the edx.org footer).


       - We now remove the default syslog.d conf file (50-default.conf) this will
       - Added EDXAPP_LMS_AUTH_EXTRA and EDXAPP_CMS_AUTH_EXTRA for passing unique AUTH_EXTRA configurations to the LMS and CMS.
 - 2015-05-11
     - Updated ansible fork with small bug fix.
       - https://github.com/ansible/ansible/pull/10957

 - 2015-05-07
     - Role: edxapp
       - Removed post.txt from the list of files that will have its github urls replaced with git mirror urls.

 - 2015-04-29
     - Role: edxapp
       - The edxapp role no longer uses checksums to bypass pip installs.
         - pip install will always run for all known requirements files.

     - Role: edx-ansible
 - 2015-04-12
       - `/edx/bin/update` no longer runs the ansible command with `--tags deploy`

 - 2015-03-23
     - Role: edxapp
       - Added newrelic monitoring capabilities to edxapp workers. Note that this is a BACKWARDS-INCOMPATABLE CHANGE, as it introduces a new key, `monitor`, to each item in `EDXAPP_CELERY_WORKERS` in `defaults/main.yml`, and plays including this role will fail if that key is not set.

 - 2015-03-05
     - Role: analytics_api, xqwatcher, insights, minos, edx_notes_api
       - Expanded `edx_service` role to do git checkout and ec2 tagging
       - Refactored roles that depend on `edx_service` to use the new interface: `minos`, `analytics_api`, `insights`, and `xqwatcher`
       - Refactored name from `analytics-api` to `analytics_api`
       - Changed location of minos' config file from `/edx/etc/minos/minos.yml` to `/edx/etc/minos.yml`
       - Added new `edx_notes_api` role for forthcoming notes api
       - This is a __BACKWARDS INCOMPATABLE__ change and will require additional migrations when upgrading an existing server. While we recommend building from scratch, running the following command _might_ work:
           rm -rf /edx/etc/minos
 - 2015-02-06
           ```
           rm -rf /edx/app/analytics-api /edx/app/ /edx/app/nginx/sites-available/analytics-api.j2 /edx/app/supervisor/conf.d.available/analytics_api.conf
           ```

 - 2015-02-02
     - Role: edxapp
       - Enabled combined login registration feature by default

 - 2014-12-29
     - Role: notifier
       - Refactored `NOTIFIER_HOME` and `NOTIFIER_USER` to `notifier_app_dir` and `notifier_user` to match other roles. This shouldn't change anything since users should've only been overriding COMMON_HOME.

 - 2014-12-10
     - Role: gitreload
       - New role added for running
         [gitreload](https://github.com/mitodl/gitreload) that can be used
         for importing courses via github/gitlab Web hooks, or more
         generally updating any git repository that is already checked out
         on disk via a hook.

 - 2014-12-01
     - Role: analytics-api, edxapp, ora, xqueue, xserver
       - Switched gunicorn from using an entirely command argument based
         configuration to usign python configuration files. Variables for
         extra configuration in the configuration file template, and
         command line argument overrides are available.

 - 2014-11-13
     - Role: analytics-api, insights
       - Using Django 1.7 migrate command.

 - 2014-10-15
     - Role: edxapp
       - A new var was added to make it easy ot invalidate the default
         memcache store to make it easier to invalidate sessions. Updating
         the edxapp env.json files will result in all users getting logged
         out.  This is a one time penalty as long as the value of `EDXAPP_DEFAULT_CACHE_VERSION`
         is not explicitly changed.

 - 2014-09-18
     - Role: nginx
       - New html templates for server errors added.
         Defaults for a ratelimiting static page and server error static page.
         CMS/LMS are set to use them by default, wording can be changed in the
         Nginx default vars.

 - 2014-09-15
     - Role: edxapp
       - We now have an all caps variable override for celery workers
 - 2014-08-28

     - Role: Edxapp
         Both variables default to EDXAPP_AUTH_EXTRA for backward compatibility
 - 2014-08-22

     - Role: Mongo
       - Fixed case of variable used in if block that breaks cluster configuration
         by changing mongo_clustered to MONGO_CLUSTERED.
 - 2014-08-20
     - Role: common
       break people who have hand edited that file.

 - 2014-08-15
     - Role: edxapp
       - Updated the module store settings to match the new settings format.

 - 2014-08-05
     - Update, possible breaking change: the edxapp role vars edxapp_lms_env and edxapp_cms_env have
       been changed to EDXAPP_LMS_ENV and EDXAPP_CMS_ENV to indicate, via our convention,
       that overridding them is expected.  The default values remain the same.

 - 2014-06-26
     - Role: analytics-api
       - Added a new role for the analytics-api Django app.  Currently a private repo

     - Logrotation now happens hourly by default for all logs.

       - Basic auth will be turned on by default
     - Update `CMS_HOSTNAME` default to allow any hostname that starts with `studio` along with `prod-studio` or `stage-studio`.
 - 2014-06-11
     - Role: xqwatcher, xqueue, nginx, edxapp, common
       - Moving nginx basic authorization flag and credentials to the common role

 - 2014-06-02
     - Role: Edxapp
       - Turn on code sandboxing by default and allow the jailed code to be able to write
         files to the tmp directory created for it by codejail.

 - 2014-05-28
     - Role: Edxapp
       - The repo.txt requirements file is no longer being processed in anyway.  This file was removed from edxplatform
         via pull #3487(https://github.com/edx/edx-platform/pull/3487)

 - 2014-05-19

     - Start a change log to keep track of backwards incompatible changes and deprecations.
