- git_clone:
  - The working tree is explicitly checked for modified files, to prevent mysterious failures.

- Installation
  - OPENEDX_RELEASE is now required, to prevent accidental installation of master.

- XQueue
  - Expose CLOUDWATCH_QUEUE_COUNT_METRIC which is defined XQueue's settings.py for further dictionary structure

- nginx:
  - remove nginx_cfg - an internal variable that was really only used for the edx-release nginx site, which served version.{html,json} off of a nonstandard port.  The file it served was never populated.

- Role: edxapp
  - Create EDXAPP_CMS_GUNICORN_TIMEOUT and EDXAPP_LMS_STATIC_URL_BASE to allow overriding of the gunicorn timeout

- Structure: edx-east
  - Deprecated the edx-east folder, playbooks now live in the top level directory instead of edx-east/playbooks. A symbolic link was added for now, but should not be relied upon.

- Role: edxapp
  - EDXAPP_NGINX_SKIP_ENABLE_SITES added to allow you to not sync in the lms or cms nginx configuration.  Instead you can enable them during deployment.
  - EDXAPP_NGINX_DEFAULT_SITES added to allow you to mark both lms and cms as defaults, best paired with picking which site to enable during deployment.
  - EDXAPP_LMS_STATIC_URL_BASE and EDXAPP_CMS_STATIC_URL_BASE allow a per-application setting of the static URL.  You can stil use EDXAPP_STATIC_URL_BASE for now but we may retire that as we continue to separate LMS and CMS.

- Role: XQueue
  - Convert to a yaml config (instead of xqueue.auth.json and xqueue.env.json we get xqueue.yml and it lives by default in /edx/etc/xqueue.yml like standard IDAs)
  - Add XQUEUE_DEFAULT_FILE_STORAGE so that you can specify S3 or Swift in your config
  - XQUEUE_SETTINGS now prefers production.py over aws_settings.py

- Role: credentials
  - Set `LANGUAGE_COOKIE_NAME` so that Credentials will use the global language cookie.

- Role: edxapp
  - Added `PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG` to make configurable whether password complexity is checked on login and how such complexity is rolled out to users.

- Role: certs
  - Added `CERTS_QUEUE_POLL_FREQUENCY` to make configurable the certificate agent's queue polling frequency.

- Role: edxapp
  - Added `RETIREMENT_STATES` to generic_env_config to support making the retirement workflow configurable.

- Removed Vagrantfiles for devstack and fullstack, and supporting files.

- Role: xqueue
  - Added XQUEUE_SUBMISSION_PROCESSING_DELAY and XQUEUE_CONSUMER_DELAY to xqueue env so they can be passed along to the app.

- Role: edxapp
  - Moved `PASSWORD_MIN_LENGTH`, `PASSWORD_MAX_LENGTH`, and `PASSWORD_COMPLEXITY` to generic_env_config to allow CMS and LMS to share these configurations

- Role: edxapp
  - Added GOOGLE_SITE_VERIFICATION_ID to move a previously hardcoded value into configuration.
  - Changed `EDXAPP_RETIRED_USERNAME_FMT` to `EDXAPP_RETIRED_USERNAME_PREFIX`. Changed/split `EDXAPP_RETIRED_EMAIL_FMT` to be `EDXAPP_RETIRED_EMAIL_PREFIX` and `EDXAPP_RETIRED_EMAIL_DOMAIN`.

- Role xqueue
  - Removed RabbitMQ in earlier changes in XQueue itself, we don't need any of the configuration
    XQUEUE_RABBITMQ_USER XQUEUE_RABBITMQ_PASS XQUEUE_RABBITMQ_VHOST XQUEUE_RABBITMQ_HOSTNAME
    XQUEUE_RABBITMQ_PORT XQUEUE_RABBITMQ_TLS
  - Added NEWRELIC_APPNAME and NEWRELIC_LICENSE_KEY to the configuration files consumed by XQueue.
    Useful for external utilities that are reporting NR metrics.
  - Added XQUEUE_CONSUMER_NEWRELIC_APPNAME which is added to the supervisor start of xqueue_consumer
    if you have New Relic enabled.
  - Retired XQUEUE_WORKERS_PER_QUEUE

- Role edx_django_service
  - Added maintenance page under the flag EDX_DJANGO_SERVICE_ENABLE_S3_MAINTENANCE.
  - Added the s3_maintenance.j2 file to point to the s3 maintenance page.

- Role: xqueue
  - Added XQUEUE_MYSQL_CONN_MAX_AGE so that you can have xqueue use django's persistent DB connections

- Role: edxapp
  - Added empty `EDXAPP_PASSWORD_COMPLEXITY` setting to ease overriding complexity.

- Role: splunkforwarder
  - Updated the role so the splunkforwarder can be installed on Amazon Linux OS environment, which is a RHEL variant

- Role: server_utils
  - Update to only do things for debian varient environment

- Role: xqueue
  - Added `XQUEUE_SESSION_ENGINE` to allow a configurable xqueue session engine.
  - Added `XQUEUE_CACHES` to allow a configurable xqueue cache.

- Role: devpi
  - New role added to configure a devpi service as a pass-through cache for PyPI.

- Role: devpi_consumer
  - Added role to configure Python containers to use devpi for Docker Devstack

- Role: xqueue
  - Remove S3_BUCKET and S3_PATH_PREFIX - they were deprecated prior to ginkgo
  - Remove SERVICE_VARIANT - it was copied from edxapp but never truly used (except to complicate things)
  - The manage_users management command is only run when disable_edx_services is false (previously this play would try
    to update databases while building images, where services are generally disabled).

- Role: edxapp
  - Added `EDXAPP_RETIRED_USERNAME_FMT`, `EDXAPP_RETIRED_EMAIL_FMT`, `EDXAPP_RETIRED_USER_SALTS`, and
  `EDXAPP_RETIREMENT_SERVICE_WORKER_USERNAME` to generic_env_config to allow user retirement to be configurable.

- Role: edxapp
  - Added `ENTERPRISE_REPORTING_SECRET` to CMS auth settings to allow edx-enterprise migrations to run.

- Role: edxapp
  - Added `EDXAPP_FERNET_KEYS` to allow for use of django-fernet-keys in LMS.

- Role: edxapp
  - Added `EDXAPP_DEFAULT_COURSE_VISIBILITY_IN_CATALOG` setting (defaults to `both`).

  - Added `EDXAPP_DEFAULT_MOBILE_AVAILABLE` setting (defaults to `false`).

  - Added `EDX_PLATFORM_REVISION` (set from `edx_platform_version`). This is for
  edx-platform debugging purposes, and replaces calling dealer.git at startup.

- Role: veda_pipeline_worker
  - New role to run all (`deliver, ingest, youtubecallback`) [video pipeline workers](https://github.com/edx/edx-video-pipeline/blob/master/bin/)

- Role: veda_ffmpeg
  - New role added to compile ffmpeg for video pipeline. It will be used as a dependency for video pipeline roles.

- Role: edxapp
  - Added `EDXAPP_BRANCH_IO_KEY` to configure branch.io journey app banners.

- Role: ecomworker
  - Added `ECOMMERCE_WORKER_BROKER_TRANSPORT` with a default value of 'ampq' to be backwards compatible with rabbit.  Set to 'redis' if you wish to use redis instead of rabbit as a queue for ecommerce worker.

- Role: ecommerce
  - Added `ECOMMERCE_BROKER_TRANSPORT` with a default value of 'ampq' to be backwards compatible with rabbit.  Set to 'redis' if you wish to use redis instead of rabbit as a queue for ecommerce.

- Role: credentials
  - This role is now dependent on the edx_django_service role. Settings are all the same, but nearly all of the tasks are performed by the edx_django_service role.

- Role: veda_delivery_worker
  - New role added to run [video delivery worker](https://github.com/edx/edx-video-pipeline/blob/master/bin/deliver)

- Role: veda_web_frontend
  - New role added for [edx-video-pipeline](https://github.com/edx/edx-video-pipeline)

- Role: edxapp
  - Added `EDXAPP_LMS_INTERNAL_ROOT_URL` setting (defaults to `EDXAPP_LMS_ROOT_URL`).

- Role: edxapp
  - Added `EDXAPP_CELERY_BROKER_TRANSPORT` and renamed `EDXAPP_RABBIT_HOSTNAME`
    to `EDXAPP_CELERY_BROKER_HOSTNAME`. This is to support non-amqp brokers,
    specifically redis. If `EDXAPP_CELERY_BROKER_HOSTNAME` is unset it will use
    the value of `EDXAPP_RABBIT_HOSTNAME`, however it is recommended to update
    your configuration to set `EDXAPP_CELERY_BROKER_TRANSPORT` explicitly.

- Role: edxapp
  - Added `EDXAPP_MONGO_REPLICA_SET`, which is required to use
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

- Role: nginx
  - Modified `lms.j2` , `cms.j2` , `credentials.j2` , `edx_notes_api.j2` and `insights.j2` to enable HTTP Strict Transport Security
  - Added `NGINX_HSTS_MAX_AGE` to make HSTS header `max_age` value configurable and used in templates

- Role: server_utils
  - Install "vim", not "vim-tiny".

- Role: edxapp
  - Added GOOGLE_ANALYTICS_TRACKING_ID setting for inserting GA tracking into emails generated via ACE.

- Role: notifier
  - Added notifier back to continuous integration.

- Role: ecommerce
  - This role is now dependent on the edx_django_service role. Settings are all the same, but nearly all of the tasks are performed by the edx_django_service role.

- Role: discovery
  - Added `DISCOVERY_REPOS` to allow configuring discovery repository details.

- Role: edx_django_service
  - Made the keys `edx_django_service_git_protocol`, `edx_django_service_git_domain`, and `edx_django_service_git_path` of `edx_django_service_repos` all individually configurable.

- Role: discovery
  - Updated LANGUAGE_CODE to generic english. Added configuration for multilingual language package django-parler.

- Role: edxapp
  - Added `EDXAPP_EXTRA_MIDDLEWARE_CLASSES` for configuring additional middleware logic.

- Role: discovery
  - Added `OPENEXCHANGERATES_API_KEY` for retrieving currency exchange rates.

- Role: edxapp
  - Added `EDXAPP_SCORM_PKG_STORAGE_DIR`, with default value as it was in the server template.
  - Added `EDXAPP_SCORM_PLAYER_LOCAL_STORAGE_ROOT`, with default value as it was in the server template.

- Role: edxapp
  - Added `EDXAPP_ENTERPRISE_TAGLINE` for customized header taglines for different enterprises.
  - Added `EDXAPP_PLATFORM_DESCRIPTION` used to describe the specific Open edX platform.

- Role: edxapp
  - Added `EDXAPP_REINDEX_ALL_COURSES` to rebuild the course index on deploy. Disabled by default.

- Role: edxapp
  - Added `ENTERPRISE_SUPPORT_URL` variable used by the LMS.

- Role: edxapp
  - Added OAUTH_DELETE_EXPIRED to enable automatic deletion of edx-django-oauth2-provider grants, access tokens, and refresh tokens as they are consumed. This will not do a bulk delete of existing rows.

- Role: mongo_3_2
  - Added role for mongo 3.2, not yet in use.
  - Removed MONGO_CLUSTERED variable. In this role mongo replication is always configured, even if there is only one node.

- Role: edxapp
  - Added creation of enterprise_worker user to provisioning. This user is used by the edx-enterprise package when making API requests to Open edX IDAs.

- Role: neo4j
  - Increase heap and page caches sizes for neo4j

- Role: neo4j
  - Updated neo4j to 3.2.2
  - Removed authentication requirement for neo4j

- Role: forum
  - Added `FORUM_REBUILD_INDEX` to rebuild the ElasticSearch index from the database, when enabled.  Default: `False`.

- Role: nginx
  - Added `NGINX_EDXAPP_CMS_APP_EXTRA`, which makes it possible to add custom settings to the site configuration for Studio.
  - Added `NGINX_EDXAPP_LMS_APP_EXTRA`, which makes it possible to add custom settings to the site configuration for the LMS.

- Role: edxapp
  - Let `confirm_email` in `EDXAPP_REGISTRATION_EXTRA_FIELDS` default to `"hidden"`.
  - Let `terms_of_service` in `EDXAPP_REGISTRATION_EXTRA_FIELDS` default to `"hidden"`.

- Role: ecommerce
  - Added ECOMMERCE_LANGUAGE_COOKIE_NAME which is the name of the cookie the ecommerce django app looks at for determining the language preference.

- Role: neo4j
  - Enabled splunk forwarding for neo4j logs.
  - Increased maximum amount of open files to 40000, as suggested by neo4j.
  - Updated the java build that neo4j uses to run.

- Role: edxapp
  - Set the default value for EDXAPP_POLICY_CHANGE_GRADES_ROUTING_KEY to
 'edx.lms.core.default'.

- Role: edxapp
  - Set the default value for EDXAPP_BULK_EMAIL_ROUTING_KEY_SMALL_JOBS to
 'edx.lms.core.low'.

- Role: jenkins_master
  - Update pinned use of JDK7 in Jenkins installs to default JDK version from role `oraclejdk`.

- Role: notifier
  - Added `NOTIFIER_DATABASE_ENGINE`, `NOTIFIER_DATABASE_NAME`, `NOTIFIER_DATABASE_USER`, `NOTIFIER_DATABASE_PASSWORD`, `NOTIFIER_DATABASE_HOST`, and `NOTIFIER_DATABASE_PORT` to be able to configure the `notifier` service to use a database engine other than sqlite. Defaults to local sqlite.
  - Deprecated: `NOTIFIER_DB_DIR`: Please use `NOTIFIER_DATABASE_NAME` instead.

- Role: elasticsearch
  - Replaced `elasticsearch_apt_key` and `elastic_search_apt_keyserver` with `elasticsearch_apt_key_url`
  - Updated elasticsearch version to 1.5.0

- Role: edxapp
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

- Role: insights
  - Added `INSIGHTS_DOMAIN` to configure the domain Insights is deployed on
  - Added `INSIGHTS_CLOUDFRONT_DOMAIN` to configure the domain static files can be served from
  - Added `INSIGHTS_CORS_ORIGIN_WHITELIST_EXTRA` to configure allowing CORS on domains other than the `INSIGHTS_DOMAIN`

- Role: edxapp
  - Added `EDXAPP_VIDEO_IMAGE_SETTINGS` to configure S3-backed video images.

- Role: edxapp
  - Added `EDXAPP_BASE_COOKIE_DOMAIN` for sharing cookies across edx domains.

- Role: insights
  - Removed `bower install` task
  - Replaced r.js build task with webpack build task
  - Removed `./manage.py compress` task

- Role: insights
  - Moved `THEME_SCSS` from `INSIGHTS_CONFIG` to `insights_environment`

- Role: analytics_api
  - Added a number of `ANALYTICS_API_DEFAULT_*` and `ANALYTICS_API_REPORTS_*` variables to allow more selective specification of database parameters (rather than
      overriding the whole structure).

- Role: edxapp
  - Remove EDXAPP_ANALYTICS_API_KEY, EDXAPP_ANALYTICS_SERVER_URL, EDXAPP_ANALYTICS_DATA_TOKEN, EDXAPP_ANALYTICS_DATA_URL since they are old and
  no longer consumed.

- Role: edxapp
  - Added `PASSWORD_MIN_LENGTH` for password minimum length validation on reset page.
  - Added `PASSWORD_MAX_LENGTH` for password maximum length validation on reset page.

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

- Role: edxapp
  - Added `EDXAPP_VIDEO_TRANSCRIPTS_SETTINGS` to configure S3-backed video transcripts.
  - Removed unused `EDXAPP_BOOK_URL` setting

- Role: edxapp
  - Added `EDXAPP_ZENDESK_OAUTH_ACCESS_TOKEN` for making requests to Zendesk through front-end.

- Role: whitelabel
  - Added `WHITELABEL_THEME_DIR` to point to the location of whitelabel themes.
  - Added `WHITELABEL_ADMIN_USER` to specify an admin user.
  - Added `WHITELABEL_DNS` for DNS settings of themes.
  - Added `WHITELABEL_ORG` for whitelabel organization settings.
