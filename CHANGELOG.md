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
