- Role: edxapp
  - Added `EDXAPP_CELERY_BROKER_TRANSPORT` and renamed `EDXAPP_RABBIT_HOSTNAME`
    to `EDXAPP_CELERY_BROKER_HOSTNAME`. This is to support non-amqp brokers,
    specifically redis. If `EDXAPP_CELERY_BROKER_HOSTNAME` is unset it will use
    the value of `EDXAPP_RABBIT_HOSTNAME`, however it is recommended to update
    your configuration to set `EDXAPP_CELERY_BROKER_TRANSPORT` explicitly.

  - Install development.txt in Vagrant and Docker devstacks

- Role: edxapp
  - Set the EDXAPP_IMPORT_EXPORT_BUCKET setting to an empty string

- Role: edxapp
  - Updated default value of the EDXAPP_ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES setting to ["audit", "honor"]

- Role: edx_notes_api
  - Removed EDX_NOTES_API_ELASTICSEARCH_HOST.
  - Removed EDX_NOTES_API_ELASTICSEARCH_PORT.
  - EDX_NOTES_API_ELASTICSEARCH_URL.

- Role: edxapp
  - Added the EDXAPP_ACTIVATION_EMAIL_SUPPORT_LINK URL with default value `''`.
  - Added the EDXAPP_PASSWORD_RESET_SUPPORT_LINK URL with default value `''`.

- Role: edxapp
  - Added the EDXAPP_SHOW_HEADER_LANGUAGE_SELECTOR feature flag with default value [false]
  - Added the EDXAPP_SHOW_FOOTER_LANGUAGE_SELECTOR feature flag with default value [false]

- Role: edxapp
  - Added the EDXAPP_ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES setting with default value ["audit"]

- Role: edxapp
  - DOC_LINK_BASE settings have been removed, replaced by HELP_TOKENS_BOOKS

- Role: edxapp
  - Add the EDXAPP_LANGUAGE_COOKIE setting

- Role: rabbitmq
  - Upgraded to 3.6.9
  - Switched to a PPA rather than a .deb hosted in S3
  - Note that you generally cannot upgrade RabbitMQ live in place https://www.rabbitmq.com/clustering.html
    this is particularly true coming from 3.2 to 3.6.  We are using the shovel plugin to move tasks across clusters
    but their documentation covers different scenarios.
- Role: edxapp
  - Added a new EDXAPP_MYSQL_CONN_MAX_AGE, default to 0.  Adjust it to change how long a connection is kept open
  for reuse before it is closed.
  - Set preload_app to False in gunicorn config for LMS and Studio.
- Role: analytics_api
  - Added `ANALYTICS_API_AGGREGATE_PAGE_SIZE`, default value 10.  Adjust this parameter to increase the number of
    aggregate search results returned by the Analytics API, i.e. in course_metadata: enrollment_modes, cohorts, and
    segments.
- Role: programs
  - This role has been removed as this service is no longer supported. The role is still available on the [Ficus branch](https://github.com/edx/configuration/releases/tag/open-release%2Fficus.1).
- Role: xqueue
  - Changed `XQUEUE_RABBITMQ_TLS` default from `true` to `false`.
- Role: credentials
  - Added `CREDENTIALS_EXTRA_APPS` to enable the inclusion of additional Django apps in the Credentials Service.
- Role: common
  - Renamed `COMMON_AWS_SYNC` to `COMMON_OBJECT_STORE_LOG_SYNC`
  - Renamed `COMMON_AWS_SYNC_BUCKET` to `COMMON_OBJECT_STORE_LOG_SYNC_BUCKET`
  - Renamed `COMMON_AWS_S3_SYNC_SCRIPT` to `COMMON_OBJECT_STORE_LOG_SYNC_SCRIPT`
  - Added `COMMON_OBJECT_STORE_LOG_SYNC_PREFIX`. Default: `logs/tracking/`
  - Added `COMMON_EDXAPP_SETTINGS`. Default: `aws`
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

- Role: discovery
  - Course Discovery JWT configuration now takes a list of issuers instead of a single issuer.  This change is not backward compatible with older versions of course discovery.

- Role: hadoop_common
  - Enable log retention by default to assist with debugging. Now YARN will retain stdout and stderr logs produced by map reduce tasks for 24 hours. They can be retrieved by running "yarn logs -applicationId YOUR_APPLICATION_ID".

- Role: rabbitmq
  - Removed the RABBITMQ_CLUSTERED var and related tooling. The goal of the var was to be able to setup a cluster in the aws environment without having to know all the IPs of the cluster before hand.  It relied on the `hostvars` ansible varible to work correctly which it no longer does in 1.9.  This may get fixed in the future but for now, the "magic" setup doesn't work.
  - Changed `rabbitmq_clustered_hosts` to RABBITMQ_CLUSTERED_HOSTS.

- Role: edxapp
  - Removed SUBDOMAIN_BRANDING and SUBDOMAIN_COURSE_LISTINGS variables

- Role: ora
  - Remove the ora1 role as support for it was deprecated in Cypress.
  - Removed dependencies on ora throughout the playbooks / vagrantfiles.
- Role: edxapp
  - Removed XmlModuleStore from the default list of modulestores for the LMS.
  - EDXAPP_XML_MAPPINGS variable no longer exists by default and is not used by the edxapp role.

- Role: ecommerce
  - Removed ECOMMERCE_ORDER_NUMBER_PREFIX variable

- Role: edxapp
  - All of the following changes are BACKWARDS-INCOMPATABLE:
    - Renamed two top level variables SEGMENT_IO_LMS_KEY and SEGMENT_IO_KEY to SEGMENT_KEY in {lms|cms].auth.json.
    - Renamed two top level variables in roles/edxapp/defaults/main.yml.  EDXAPP_SEGMENT_IO_LMS_KEY and EDXAPP_SEGMENT_IO_KEY are now EDXAPP_LMS_SEGMENT_KEY and EDXAPP_CMS_SEGMENT_KEY respectively
    - REMOVED two top level variables SEGMENT_IO_LMS and SEGMENT_IO from {lms|cms].auth.json. We will use the existence of the SEGMENT_KEY to to serve the same function that these boolean variables served.
    - REMOVED two top level variables EDXAPP_SEGMENT_IO_LMS and EDXAPP_SEGMENT_IO from roles/edxapp/defaults/main.yml.

- Updated ansible fork to be based on ansible 1.9.3rc1 instead of 1.9.1
  - Ansible Changelog: https://github.com/ansible/ansible/blob/stable-1.9/CHANGELOG.md

- Role: edxapp
  - Removed deprecated variables EDXAPP_PLATFORM_TWITTER_URL, EDXAPP_PLATFORM_MEETUP_URL, EDXAPP_PLATFORM_LINKEDIN_URL, and EDXAPP_PLATFORM_GOOGLE_PLUS_URL in favor of EDXAPP_SOCIAL_MEDIA_FOOTER_URLS.  These variables haven't been used in edx-platform since March 17, 2015 (when https://github.com/edx/edx-platform/pull/7383 was merged).  This change is backwards incompatible with versions of edx-platform from before March 17, 2015.
  - Added EDXAPP_MOBILE_STORE_URLS and EDXAPP_FOOTER_ORGANIZATION_IMAGE variables, used in https://github.com/edx/edx-platform/pull/8175 (v3 version of the edx.org footer).

- Updated ansible fork with small bug fix.
  - https://github.com/ansible/ansible/pull/10957

- Role: edxapp
  - Removed post.txt from the list of files that will have its github urls replaced with git mirror urls.

- Role: edxapp
  - The edxapp role no longer uses checksums to bypass pip installs.
    - pip install will always run for all known requirements files.

- Role: edx-ansible
  - `/edx/bin/update` no longer runs the ansible command with `--tags deploy`

- Role: edxapp
  - Added newrelic monitoring capabilities to edxapp workers. Note that this is a BACKWARDS-INCOMPATABLE CHANGE, as it introduces a new key, `monitor`, to each item in `EDXAPP_CELERY_WORKERS` in `defaults/main.yml`, and plays including this role will fail if that key is not set.

- Role: edxapp
  - Enabled combined login registration feature by default

- Role: analytics_api, xqwatcher, insights, minos, edx_notes_api
  - Expanded `edx_service` role to do git checkout and ec2 tagging
  - Refactored roles that depend on `edx_service` to use the new interface: `minos`, `analytics_api`, `insights`, and `xqwatcher`
  - Refactored name from `analytics-api` to `analytics_api`
  - Changed location of minos' config file from `/edx/etc/minos/minos.yml` to `/edx/etc/minos.yml`
  - Added new `edx_notes_api` role for forthcoming notes api
  - This is a __BACKWARDS INCOMPATABLE__ change and will require additional migrations when upgrading an existing server. While we recommend building from scratch, running the following command _might_ work:

      ```
      rm -rf /edx/app/analytics-api /edx/app/ /edx/app/nginx/sites-available/analytics-api.j2 /edx/app/supervisor/conf.d.available/analytics_api.conf
      rm -rf /edx/etc/minos
      ```

- Role: notifier
  - Refactored `NOTIFIER_HOME` and `NOTIFIER_USER` to `notifier_app_dir` and `notifier_user` to match other roles. This shouldn't change anything since users should've only been overriding COMMON_HOME.

- Role: gitreload
  - New role added for running
    [gitreload](https://github.com/mitodl/gitreload) that can be used
    for importing courses via github/gitlab Web hooks, or more
    generally updating any git repository that is already checked out
    on disk via a hook.

- Role: analytics-api, edxapp, ora, xqueue, xserver
  - Switched gunicorn from using an entirely command argument based
    configuration to usign python configuration files. Variables for
    extra configuration in the configuration file template, and
    command line argument overrides are available.

- Role: analytics-api, insights
  - Using Django 1.7 migrate command.

- Role: edxapp
  - A new var was added to make it easy ot invalidate the default
    memcache store to make it easier to invalidate sessions. Updating
    the edxapp env.json files will result in all users getting logged
    out.  This is a one time penalty as long as the value of `EDXAPP_DEFAULT_CACHE_VERSION`
    is not explicitly changed.

- Role: nginx
  - New html templates for server errors added.
    Defaults for a ratelimiting static page and server error static page.
    CMS/LMS are set to use them by default, wording can be changed in the
    Nginx default vars.

- Role: edxapp
  - We now have an all caps variable override for celery workers
- Role: common
  - We now remove the default syslog.d conf file (50-default.conf) this will
  break people who have hand edited that file.

- Role: edxapp
  - Updated the module store settings to match the new settings format.

- Update, possible breaking change: the edxapp role vars edxapp_lms_env and edxapp_cms_env have
  been changed to EDXAPP_LMS_ENV and EDXAPP_CMS_ENV to indicate, via our convention,
  that overridding them is expected.  The default values remain the same.

- Role: analytics-api
  - Added a new role for the analytics-api Django app.  Currently a private repo

- Logrotation now happens hourly by default for all logs.

- Role: xqwatcher, xqueue, nginx, edxapp, common
  - Moving nginx basic authorization flag and credentials to the common role
  - Basic auth will be turned on by default

- Role: Edxapp
  - Turn on code sandboxing by default and allow the jailed code to be able to write
    files to the tmp directory created for it by codejail.

- Role: Edxapp
  - The repo.txt requirements file is no longer being processed in anyway.  This file was removed from edxplatform
    via pull #3487(https://github.com/edx/edx-platform/pull/3487)

- Update `CMS_HOSTNAME` default to allow any hostname that starts with `studio` along with `prod-studio` or `stage-studio`.

- Start a change log to keep track of backwards incompatible changes and deprecations.

- Role: Mongo
  - Fixed case of variable used in if block that breaks cluster configuration
    by changing mongo_clustered to MONGO_CLUSTERED.

- Role: Edxapp
  - Added EDXAPP_LMS_AUTH_EXTRA and EDXAPP_CMS_AUTH_EXTRA for passing unique AUTH_EXTRA configurations to the LMS and CMS.
    Both variables default to EDXAPP_AUTH_EXTRA for backward compatibility

- Role: ecommerce
  - Renamed `ECOMMERCE_COMPREHENSIVE_THEME_DIR` to `ECOMMERCE_COMPREHENSIVE_THEME_DIRS`, `ECOMMERCE_COMPREHENSIVE_THEME_DIRS`
    is now a list of directories. Change is backward incompatible.
  - Renamed `COMPREHENSIVE_THEME_DIR` to `COMPREHENSIVE_THEME_DIRS`, `COMPREHENSIVE_THEME_DIRS` is now a list of directories.
    Change is backward incompatible.

- Role: Edxapp
  - `EDXAPP_COMPREHENSIVE_THEME_DIR` is deprecated and is maintained for backward compatibility, `EDXAPP_COMPREHENSIVE_THEME_DIRS`
    should be used instead which is a list of directories. `EDXAPP_COMPREHENSIVE_THEME_DIR` if present will have priority over `EDXAPP_COMPREHENSIVE_THEME_DIRS`
  - `COMPREHENSIVE_THEME_DIR` is deprecated and is maintained for backward compatibility, `COMPREHENSIVE_THEME_DIRS` should be used
    instead which is a list of directories. `COMPREHENSIVE_THEME_DIR` if present will have priority over `COMPREHENSIVE_THEME_DIRS`

- Role: edxapp
  - Added COMPREHENSIVE_THEME_LOCALE_PATHS to support internationalization of strings originating from custom themes.

- Role: edxapp
  - Added `EXPIRING_SOON_WINDOW` to show message to learners if their verification is expiring soon.

- Role: discovery
  - Added `PUBLISHER_FROM_EMAIL` for sending emails to publisher app users.

- Role: security
  - Changed SECURITY_UPGRADE_ON_ANSIBLE to only apply security updates.  If you want to retain the behavior of running safe-upgrade,
    you should switch to using SAFE_UPGRADE_ON_ANSIBLE.

- Role: mongo_2_6
  - Added `MONGO_AUTH` to turn authentication on/off. Auth is now enabled by default, and was previously disabled by default.

- Role: mongo_3_0
  - Changed MONGO_STORAGE_ENGINE to default to wiredTiger which is the default in 3.2 and 3.4 and what edX suggests be used even on 3.0.
    If you have a mmapv1 3.0 install, override MONGO_STORAGE_ENGINE to be mmapv1 which was the old default.
  - Support parsing the replset JSON in 3.2 and 3.0
  - Added `MONGO_AUTH` to turn authentication on/off. Auth is now enabled by default, and was previously disabled by default.

- Role: xqueue
  - Added `XQUEUE_RABBITMQ_TLS` to allow configuring xqueue to use TLS when connecting to the AMQP broker.
  - Added `XQUEUE_RABBITMQ_VHOST` to allow configuring the xqueue RabbitMQ host.
  - Added `XQUEUE_RABBITMQ_PORT` to allow configuring the RabbitMQ port.

- Role: edxapp
  - Added `EDXAPP_CELERY_BROKER_USE_SSL` to allow configuring celery to use TLS.

- Role: ecommerce
  - Added `ECOMMERCE_ENTERPRISE_URL` for the `enterprise` API endpoint exposed by a new service `edx-enterprise` (currently hosted by `LMS`), which defaults to the existing setting `ECOMMERCE_LMS_URL_ROOT`.

- Role: ecommerce
  - Removed `SEGMENT_KEY` which is no longer used.  Segment key is now defined in DB configuration. (https://github.com/edx/ecommerce/pull/1121)

- Role: edxapp
  - Added `EDXAPP_BLOCK_STRUCTURES_SETTINGS` to configure S3-backed Course Block Structures.

- Role: insights
  - Removed `INSIGHTS_FEEDBACK_EMAIL` which is no longer used, as it was deemed redundant with `INSIGHTS_SUPPORT_EMAIL`.

- Role: insights
  - Removed `SUPPORT_EMAIL` setting from `INSIGHTS_CONFIG`, as it is was replaced by `SUPPORT_URL`.
