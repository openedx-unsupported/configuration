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

- Role: Splunkforwarder
  - Changed splunkforwarder_output_dir to SPLUNK_HOME and default to /opt/splunk/
  - Added SPLUNKFORWARDER_WEB_PORT for changing splunkforwarder default httpport.
