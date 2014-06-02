- Role: Edxapp
  - Change the default settings for the code jail to limit jailed code(instructor code) to only run for 1 second
  - Create a separate sandbox virtualenv and don't install the sandbox code in the default virtualenv.

- Role: Edxapp
  - The repo.txt requirements file is no longer being processed in anyway.  This file was removed from edxplatform
    via pull #3487(https://github.com/edx/edx-platform/pull/3487)

- Update CMS_HOSTNAME default to allow any hostname that starts with `studio` along with `prod-studio` or `stage-studio`.

- Start a change log to keep track of backwards incompatible changes and deprecations.
