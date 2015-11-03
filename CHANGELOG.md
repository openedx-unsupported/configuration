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
