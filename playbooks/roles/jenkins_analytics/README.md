# Jenkins Analytics

A role that sets up Jenkins for scheduling analytics tasks.

This role performs the following steps:

* Installs Jenkins using `jenkins_master`.
* Configures `config.xml` to enable security and use
  Github OAuth plugin (by default) or Unix Auth Domain.
* Creates Jenkins credentials.
* Enables the use of Jenkins CLI.
* Installs a seed job from configured repository, launches it and waits
  for it to finish.
* The seed job creates the analytics task jobs.

Each analytics task job is created using a task-specific DSL script which
determines the structure of the Jenkins job, e.g. its scheduled frequency, the
git repos cloned to run the task, the parameters the job requires, and the
shell script used to run the analytics task.  These DSL scripts live in a
separate git repo, configured by `ANALYTICS_SCHEDULE_JOBS_DSL_REPO_*`.


## Configuration

When you are using vagrant you **need** to set `VAGRANT_JENKINS_LOCAL_VARS_FILE`
environment variable. This variable must point to a file containing
all required variables from this section.

This file needs to contain, at least, the following variables
(see the next few sections for more information about them):

* `JENKINS_ANALYTICS_GITHUB_OAUTH_CLIENT_*` or `JENKINS_ANALYTICS_USER_PASSWORD_PLAIN`.
  See [Jenkins Security](#jenkins-security) for details.
* (`JENKINS_ANALYTICS_GITHUB_CREDENTIAL_*` and `ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_*`)
  and/or `JENKINS_ANALYTICS_CREDENTIALS`.
  See [Jenkins Credentials](#jenkins-credentials) for details.
* `ANALYTICS_SCHEDULE_SECURE_REPO_*` and `ANALYTICS_SCHEDULE_<TASK_NAME>_EXTRA_VARS`.
  See [Jenkins Seed Job Configuration](#jenkins-seed-job-configuration) for details.

### End-user editable configuration

#### Jenkins Security

The `jenkins_analytics` role provides two options for controlling authentication and authorization to the Jenkins
application:

* [Github OAuth plugin](https://wiki.jenkins-ci.org/display/JENKINS/Github+OAuth+Plugin) (default)
* Unix system user

Both roles control authorization permissions using the 
[Matrix Authorization Strategy](https://wiki.jenkins-ci.org/display/JENKINS/Matrix+Authorization+Strategy+Plugin).
See [Authorization](#authorization) for details.

##### Github OAuth

To select this security mechanism, set `JENKINS_ANALYTICS_AUTH_REALM: github_oauth`.

The [Github OAuth plugin](https://wiki.jenkins-ci.org/display/JENKINS/Github+OAuth+Plugin) 
uses Github usernames and organization memberships to control access to the
Jenkins GUI and CLI tool.

To configure Github OAuth:

1. Create a [GitHub application registration](https://github.com/settings/applications/new).

    * Application name: choose an appropriate name, e.g. edX Analytics Scheduler
    * Homepage URL: choose an appropriate URL within your Jenkins install, usually the home page.  
      e.g., `http://localhost:8080`
    * Authorization callback URL: Must be your Jenkins base URL, with path `/securityRealm/finishLogin`.  
      e.g., `http://localhost:8080/securityRealm/finishLogin`

1. Copy the Client ID and Client Secret into these variables:

        JENKINS_ANALYTICS_GITHUB_OAUTH_CLIENT_ID: <Github Client ID>
        JENKINS_ANALYTICS_GITHUB_OAUTH_CLIENT_SECRET: <Github Client Secret>

1. Optionally add your Github username or groups to the `JENKINS_ANALYTICS_AUTH_JOB_BUILDERS` and/or 
   `JENKINS_ANALYTICS_AUTH_ADMINISTRATORS` lists.  See [Authorization](#authorization) below for details.

1. Optionally, but only with good reason, update the list of Github OAuth Scopes.  This setting determines the Github
   permissions that the Jenkins application will have in Github on behalf of the authenticated user.  
   Default value is:

        JENKINS_ANALYTICS_GITHUB_OAUTH_SCOPES:
          - read:org
          - user:email

1. You may also update the Github OAuth Web URI and API URI values, if for instance, you're using a locally installed
enterprise version of Github.  Default values are:

        JENKINS_ANALYTICS_GITHUB_OAUTH_WEB_URI: 'https://github.com'
        JENKINS_ANALYTICS_GITHUB_OAUTH_API_URI: 'https://api.github.com'


##### Unix system user

To select this security mechanism, set `JENKINS_ANALYTICS_AUTH_REALM: unix`.

This security mechanism uses the `jenkins` system user and password for access
to the Jenkins GUI and CLI tool.

You'll need to override default `jenkins` user password, please do that carefully
as this sets up the **shell** password for this user.

You'll need to set a plain password so ansible can reach Jenkins via the command line tool.

    JENKINS_ANALYTICS_AUTH_REALM: unix
    JENKINS_ANALYTICS_USER_PASSWORD_PLAIN: "your plain password"

##### Authorization

The `jenkins_analytics` role configures authorization using the
[Matrix Authorization Strategy](https://wiki.jenkins-ci.org/display/JENKINS/Matrix+Authorization+Strategy+Plugin).
This strategy provides fine-grained control over which permissions are granted to which users or group members.

Currently there are three different levels of user access configured:

* `anonymous`: The `anonymous` user is special in Jenkins, and denotes any unauthenticated user.  By default, no
  permissions are granted to anonymous users, which forces all users to the login screen.
* `JENKINS_ANALYTICS_AUTH_ADMINISTRATORS`: list of members who are granted all permissions by default.  The
  `jenkins` user is automatically added to this list, so that ansible can maintain the Jenkins instance.  
  See [Security Note](#security-note) below.
* `JENKINS_ANALYTICS_AUTH_JOB_BUILDERS`: list of members who are granted permissions sufficient for maintaining Jobs,
  Credentials, and Views.

When `JENKINS_ANALYTICS_AUTH_REALM: github_oauth`, members of the above lists may be GitHub users, organizations, or
teams.

* `username` - give permissions to a specific GitHub username.
* `organization` - give permissions to every user that belongs to a specific GitHub organization. Members must be
  *public members* of the organization for the authorization to work correctly.  Also, the organization itself must
  allow access by the Github OAuth application, which must be granted by an administrator of the organization.
  See [Github third-party application restrictions](https://github.com/organizations/open-craft/settings/oauth_application_policy) 
  for more information.
* `organization*team` - give permissions to a specific GitHub team of a GitHub organization. Notice that organization
  and team are separated by an asterisk (`*`).  The Github OAuth plugin documentation doesn't say so, but the team
  probably needs to be a public team.

For example, this configuration grants job builder access to all of `edx-ops`, and admin access only to members of the
`jenkins-config-push-pull` team within `edx-ops`.

    JENKINS_ANALYTICS_AUTH_JOB_BUILDERS:
      - edx-ops
    JENKINS_ANALYTICS_AUTH_ADMINISTRATORS:
      - edx-ops*jenkins-config-push-pull

The list of permissions granted to each group is also configurable, but exercise caution when changing.

* `JENKINS_ANALYTICS_AUTH_ANONYMOUS_PERMISSIONS`: Defaults to an empty list, indicating no permissions.
* `JENKINS_ANALYTICS_AUTH_ADMINISTRATOR_PERMISSIONS`: Defaults to the full list of available Jenkins permissions at time
  of writing.
* `JENKINS_ANALYTICS_AUTH_JOB_BUILDER_PERMISSIONS`: By default, job builders are missing Jenkins Admin/Update
  permissions, as well as access required to administer slave Jenkins instances.  However, they are granted these
  permissions:
    - `com.cloudbees.plugins.credentials.CredentialsProvider.*`: Allows management of Jenkins Credentials.
    - `hudson.model.Hudson.Read`: Grants read access to almost all pages in Jenkins.
    - `hudson.model.Hudson.RunScripts`: Grants access to the Jenkins Script Console and CLI groovy interface.
    - `hudson.model.Item.*`: Allows management of Jenkins Jobs.
    - `hudson.model.Run.*`: Allows management of Jenkins Job Runs.
    - `hudson.model.View.*`: Allows management of Jenkins Views.
    - `hudson.scm.SCM.Tag`: Allows users to create a new tag in the source code repository for a given build.

The user/group lists and permissions are joined using matching keys in the `jenkins_auth_users` and
`jenkins_auth_permissions` structures.  

If additional groups are required, you must add them to both `jenkins_auth_users` and `jenkins_auth_permissions`.  This
example shows the current 3 groups, plus a fourth group whose members can view Job status:

    jenkins_auth_users:
      anonymous: 
        - anonymous
      administrators: "{{ jenkins_admin_users + JENKINS_ANALYTICS_AUTH_ADMINISTRATORS }}"
      job_builders: "{{ JENKINS_ANALYTICS_AUTH_JOB_BUILDERS | default([]) }}"
      job_readers: "{{ JENKINS_ANALYTICS_AUTH_JOB_READERS | default([]) }}"

    jenkins_auth_permissions:
      anonymous: "{{ JENKINS_ANALYTICS_AUTH_ANONYMOUS_PERMISSIONS }}"
      administrators: "{{ JENKINS_ANALYTICS_AUTH_ADMINISTRATOR_PERMISSIONS }}"
      job_builders: "{{ JENKINS_ANALYTICS_AUTH_JOB_BUILDER_PERMISSIONS }}"
      job_readers:
        - `hudson.model.Hudson.Read`
        - `hudson.model.Item.Discover`
        - `hudson.model.Item.Read`
        - `hudson.model.View.Read`

###### Security Note

As mentioned above, we append the `jenkins` user to the `JENKINS_ANALYTICS_AUTH_ADMINISTRATORS` list, to allow ansible
to configure Jenkins via the CLI tool.  However, when `JENKINS_ANALYTICS_AUTH_REALM: github_oauth`, there is a risk that
the owner of the Github username jenkins use that login to gain admin access to Jenkins.  This would be a risk no matter
which username we chose for this role.


#### Jenkins credentials

Jenkins contains its own credential store. To fill it with credentials,
we recommend overriding these variables:

* `JENKINS_ANALYTICS_GITHUB_CREDENTIAL_USER`: github username, with read access to the
  secure config and job dsl repos.
* `JENKINS_ANALYTICS_GITHUB_CREDENTIAL_PASSPHRASE`: optional passphrase, if required for
  `JENKINS_ANALYTICS_GITHUB_CREDENTIAL_USER`.  Default is `null`.
* `JENKINS_ANALYTICS_GITHUB_CREDENTIAL_KEY`: private key for the `JENKINS_ANALYTICS_GITHUB_CREDENTIAL_USER`, e.g.
   `"{{ lookup('file', '/home/you/.ssh/id_rsa') }}"`
* `ANALYTICS_SCHEDULE_SECURE_REPO_MASTER_SSH_CREDENTIAL_FILE`: path to the ssh
  key file, relative to the `ANALYTICS_SCHEDULE_SECURE_REPO_URL`.
  This file will be used as the private key to grant ssh access to the EMR instances.
   See [Jenkins Seed Job Configuration](#jenkins-seed-job-configuration) for details.

Note that because the `ANALYTICS_SCHEDULE_SECURE_REPO_*` isn't cloned until the
seed job is built, the `ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_ID` credential uses
`type: ssh-private-keyfile`, which allows the credential to be created before
the private key file actually exists on the file system.

Alternatively, you may override the `JENKINS_ANALYTICS_CREDENTIALS` variable.
This variable is a list of objects, each object representing a single
credential.  For now passwords, ssh-keys, and ssh key files are supported.
Each credential has a unique ID, which is used to match the credential to the
task(s) for which it is needed.

Default value for `JENKINS_ANALYTICS_CREDENTIALS`, and the variables it depends on:

    JENKINS_ANALYTICS_GITHUB_CREDENTIAL_ID: 'github-deploy-key'
    JENKINS_ANALYTICS_GITHUB_USER: 'git'
    JENKINS_ANALYTICS_GITHUB_PASSPHRASE: null

    ANALYTICS_SCHEDULE_SECURE_REPO_DEST: "analytics-secure-config"
    ANALYTICS_SCHEDULE_SECURE_REPO_MASTER_SSH_CREDENTIAL_FILE: "aws.pem"
    ANALYTICS_SCHEDULE_SEED_JOB_NAME: "AnalyticsSeedJob"
    ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_ID: "ssh-access-key"
    ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_USER: "hadoop"
    ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_PASSPHRASE: null
    ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_FILE: "{{ jenkins_home }}/workspace/{{ ANALYTICS_SCHEDULE_SEED_JOB_NAME }}/{{ ANALYTICS_SCHEDULE_SECURE_REPO_DEST }}/{{ ANALYTICS_SCHEDULE_SECURE_REPO_MASTER_SSH_CREDENTIAL_FILE }}"

    JENKINS_ANALYTICS_CREDENTIALS:
      - id: "{{ JENKINS_ANALYTICS_GITHUB_CREDENTIAL_ID }}"
        scope: GLOBAL
        username: "{{ JENKINS_ANALYTICS_GITHUB_USER }}"
        type: ssh-private-key
        passphrase: "{{ JENKINS_ANALYTICS_GITHUB_PASSPHRASE }}"
        description: github access key, generated by ansible
        privatekey: "{{ JENKINS_ANALYTICS_GITHUB_CREDENTIAL_KEY }}"
      - id: "{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_ID }}"
        scope: GLOBAL
        username: "{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_USER }}"
        type: ssh-private-keyfile
        passphrase: "{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_PASSPHRASE }}"
        description: ssh access key, generated by ansible
        privatekey: "{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_FILE }}"

If you wish to use an explicit SSH key instead of reading it from a file, you
could override `JENKINS_ANALYTICS_CREDENTIALS` like this:

    ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_KEY: |
        -----BEGIN RSA PRIVATE KEY-----
        ...
        -----END RSA PRIVATE KEY-----

    JENKINS_ANALYTICS_CREDENTIALS:
      - id: "{{ JENKINS_ANALYTICS_GITHUB_CREDENTIAL_ID }}"
        scope: GLOBAL
        username: "{{ JENKINS_ANALYTICS_GITHUB_CREDENTIAL_USER }}"
        type: ssh-private-key
        passphrase: "{{ JENKINS_ANALYTICS_GITHUB_CREDENTIAL_PASSPHRASE }}"
        description: github access key, generated by ansible
        privatekey: "{{ JENKINS_ANALYTICS_GITHUB_CREDENTIAL_KEY }}"
      - id: "{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_ID }}"
        scope: GLOBAL
        username: "{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_USER }}"
        type: ssh-private-key
        passphrase: "{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_PASSPHRASE }}"
        description: ssh access key, generated by ansible
        privatekey: "{{ ANALYTICS_SCHEDULE_MASTER_SSH_CREDENTIAL_KEY }}"

#### Jenkins seed job configuration

The seed job creates the Analytics Jobs that will run the analytics tasks.  By
default, the seed job creates all the available Analytics Jobs, but you can disable
these jobs, and set their parameters, using `ANALYTICS_SCHEDULE_<TASK_NAME>_*`.

Currently supported analytics tasks are:

* `ANSWER_DISTRIBUTION`: invokes
  `edx.analytics.tasks.answer_dist.AnswerDistributionWorkflow` via the
  `AnswerDistributionWorkflow.groovy` DSL.
* `IMPORT_ENROLLMENTS_INTO_MYSQL`: invokes
  `edx.analytics.tasks.enrollments.ImportEnrollmentsIntoMysql` via the
  `ImportEnrollmentsIntoMysql.groovy` DSL.
* `COURSE_ACTIVITY_WEEKLY`: invokes
  `edx.analytics.tasks.user_activity.CourseActivityWeeklyTask` via the
  `CourseActivityWeeklyTask.groovy` DSL.
* `INSERT_TO_MYSQL_ALL_VIDEO`: invokes
  `edx.analytics.tasks.video.InsertToMysqlAllVideoTask` via the
  `InsertToMysqlAllVideoTask.groovy` DSL.
* `INSERT_TO_MYSQL_COURSE_ENROLL_BY_COUNTRY:` invokes
  `edx.analytics.tasks.location_per_course.InsertToMysqlCourseEnrollByCountryWorkflow` via the
  `InsertToMysqlCourseEnrollByCountryWorkflow.groovy` DSL.

Since running the analytics tasks on EMR requires confidential ssh keys, the
convention is to store them in a secure repo, which is then cloned when running
the seed job.  To use a secure repo, override
`ANALYTICS_SCHEDULE_SECURE_REPO_URL` and
`ANALYTICS_SCHEDULE_SECURE_REPO_VERSION`.

For example:

    ANALYTICS_SCHEDULE_SECURE_REPO_URL: "git@github.com:open-craft/analytics-sandbox-private.git"
    ANALYTICS_SCHEDULE_SECURE_REPO_VERSION: "customer-analytics-schedule"

The seed job also clones a second repo, which contains the DSL scripts that
contain the analytics task DSLs.  That repo is configured using
`ANALYTICS_SCHEDULE_JOBS_DSL_REPO_*`, and it will be cloned directly into the
seed job workspace.

**Note:** There are two ways to specify a ssl-based github repo URL.  Note the
subtle difference in the paths: `github.com:your-org` vs. `github.com/your-org`.

* git@github.com:your-org/private-repo.git ✓
* ssh://git@github.com/your-org/private-repo.git ✓

*Not like this:*

* git@github.com/your-org/private-repo.git ❌
* ssh://git@github.com:your-org/private-repo.git ❌

The full list of seed job configuration variables is:

* `ANALYTICS_SCHEDULE_SECURE_REPO_URL`: Optional URL for the git repo that contains the
  analytics task schedule configuration file.  If set, Jenkins will clone this
  repo when the seed job is run.  Default is `null`.
* `ANALYTICS_SCHEDULE_SECURE_REPO_VERSION`: Optional branch/tagname to checkout
  for the secure repo.  Default is `master`.
* `ANALYTICS_SCHEDULE_SECURE_REPO_DEST`: Optional target dir for the the secure
  repo clone, relative to the seed job workspace.  Default is `analytics-secure-config`.
* `ANALYTICS_SCHEDULE_SECURE_REPO_CREDENTIAL_ID`: Credential id with read
  access to the secure repo.  Default is `{{ JENKINS_ANALYTICS_GITHUB_CREDENTIAL_ID }}`.
  See [Jenkins Credentials](#jenkins-credentials) below for details.
* `ANALYTICS_SCHEDULE_JOBS_DSL_REPO_URL`: Optional URL for the git repo that contains the analytics job DSLs.
  Default is `git@github.com:edx/jenkins-job-dsl-internal.git`.
  This repo is cloned directly into the seed job workspace.
* `ANALYTICS_SCHEDULE_JOBS_DSL_REPO_VERSION`: Optional branch/tagname to checkout for the job DSL repo.
  Default is `master`.
* `ANALYTICS_SCHEDULE_JOBS_DSL_REPO_CREDENTIAL_ID`: Credential id with read access to the job DSL repo.
  Default is `{{ JENKINS_ANALYTICS_GITHUB_CREDENTIAL_ID }}`.
  See [Jenkins Credentials](#jenkins-credentials) below for details.
* `ANALYTICS_SCHEDULE_JOBS_DSL_CLASSPATH`: Optional additional classpath jars
  and dirs required to run the job DSLs.
  Each path must be newline-separated, and relative to the seed job workspace.
  Default is:

        src/main/groovy
        lib/*.jar

* `ANALYTICS_SCHEDULE_JOBS_DSL_TARGET_JOBS`: DSLs for the top-level seed job to run on build.
  Default is `jobs/analytics-edx-jenkins.edx.org/*Jobs.groovy`


* `ANALYTICS_SCHEDULE_<TASK_NAME>`:  `true`|`false`.  Must be set to `true` to create the analytics task.
* `ANALYTICS_SCHEDULE_<TASK_NAME>_FREQUENCY`: Optional string representing how
  often the analytics task should be run.  Uses a modified cron syntax, e.g.
  `@daily`, `@weekly`, see [stackoverflow](http://stackoverflow.com/a/12472740)
  for details.  Set to empty string to disable cron.
  Default is different for each analytics task.
* `ANALYTICS_SCHEDULE_<TASK_NAME>_EXTRA_VARS`: YML @file location to
  override the analytics task parameters.  File locations can be absolute, or
  relative to the seed job workspace.
  You may choose to use raw YAML instead of a @file location, but be aware that
  any changes made in the Jenkins GUI will be overridden if the
  `jenkins_analytics` ansible role is re-run.

  Consult the individual analytics task DSL for details on the options and defaults.

For example:

    ANALYTICS_SCHEDULE_ANSWER_DISTRIBUTION: true
    ANALYTICS_SCHEDULE_ANSWER_DISTRIBUTION_EXTRA_VARS: "@{{ ANALYTICS_SCHEDULE_SECURE_REPO_DEST }}/analytics-tasks/answer-dist.yml"

    ANALYTICS_SCHEDULE_IMPORT_ENROLLMENTS_INTO_MYSQL: true
    ANALYTICS_SCHEDULE_IMPORT_ENROLLMENTS_INTO_MYSQL_EXTRA_VARS:
      TASKS_REPO: "https://github.com/open-craft/edx-analytics-pipeline.git"
      TASKS_BRANCH: "analytics-sandbox"
      CONFIG_REPO: "https://github.com/open-craft/edx-analytics-configuration.git"
      CONFIG_BRANCH: "analytics-sandbox"
      JOB_NAME: "ImportEnrollmentsIntoMysql"
      JOB_FREQUENCY: "@monthly"
      CLUSTER_NAME: "AnswerDistribution"
      EMR_EXTRA_VARS: "@/home/jenkins/emr-vars.yml"  # see [EMR Configuration](#emr-configuration)
      FROM_DATE: "2016-01-01"
      TASK_USER: "hadoop"
      NOTIFY_EMAIL_ADDRESSES: "staff@example.com

##### EMR Configuration

The `EMR_EXTRA_VARS` parameter for each analytics task is passed by the analytics
task shell command to the ansible playbook for provisioning and terminating the
EMR cluster.

Because `EMR_EXTRA_VARS` passes via the shell, it may reference other analytics
task parameters as shell variables, e.g. `$S3_PACKAGE_BUCKET`.

**File path**

The easiest way to modify this parameter is to provide a `@/path/to/file.yml`
or `@/path/to/file.json`.  The file path must be absolute, e.g.,

    ANALYTICS_SCHEDULE_IMPORT_ENROLLMENTS_INTO_MYSQL_EXTRA_VARS:
      EMR_EXTRA_VARS: '@/home/jenkins/emr-vars.yml'

Or relative to the analytics-configuration repo cloned by the analytics task, e.g.,

    ANALYTICS_SCHEDULE_IMPORT_ENROLLMENTS_INTO_MYSQL_EXTRA_VARS:
      EMR_EXTRA_VARS: '@./config/emr-vars.yml'

To use a path relative to the analytics task workspace, build an absolute path
using the `$WORKSPACE` variable provided by Jenkins, e.g.,

    ANALYTICS_SCHEDULE_IMPORT_ENROLLMENTS_INTO_MYSQL_EXTRA_VARS:
      EMR_EXTRA_VARS: '@$WORKSPACE/analytics-secure-config/emr-vars.yml'


**Raw JSON**

The other option, utilised by the DSL `EMR_EXTRA_VARS` default value, is to use a
JSON string.  Take care to use a *JSON string*, not raw JSON itself, as YAML is
a JSON superset, and we don't want the JSON to be parsed by ansible.

Also, because formatting valid JSON is difficult, be sure to run the text
through a JSON validator before deploying.

As with file paths, the JSON text can use analytics task parameters as shell
variables, e.g.,

    ANALYTICS_SCHEDULE_IMPORT_ENROLLMENTS_INTO_MYSQL_EXTRA_VARS:
      AUTOMATION_KEYPAIR_NAME: 'analytics-sandbox'
      VPC_SUBNET_ID: 'subnet-cd1b9c94'
      EMR_LOG_BUCKET: 's3://analytics-sandbox-emr-logs'
      CLUSTER_NAME: 'Analytics EMR Cluster'
      EMR_EXTRA_VARS: |
        {
          "name": "$CLUSTER_NAME",
          "keypair_name": "$AUTOMATION_KEYPAIR_NAME",
          "vpc_subnet_id": "$VPC_SUBNET_ID",
          "log_uri": "$EMR_LOG_BUCKET"
        }

#### Other useful variables

* `JENKINS_ANALYTICS_CONCURRENT_JOBS_COUNT`: Configures number of
  executors (or concurrent jobs this Jenkins instance can
  execute). Defaults to `2`.

### General configuration

Following variables are used by this role:

Variables used by command waiting on Jenkins start-up after running
`jenkins_master` role:

    jenkins_connection_retries: 60
    jenkins_connection_delay: 0.5

#### Auth realm

Jenkins auth realm encapsulates user management in Jenkins, that is:

* What users can log in
* What credentials they use to log in

Realm type stored in `jenkins_auth_realm.name` variable.

In future we will try to enable other auth domains, while
preserving the ability to run cli.

##### Unix Realm

For now only `unix` realm supported -- which requires every Jenkins
user to have a shell account on the server.

Unix realm requires the following settings:

* `service`: Jenkins uses PAM configuration for this service. `su` is
a safe choice as it doesn't require a user to have the ability to login
remotely.
* `plain_password`:  plaintext password, **you must change** default values.

Example realm configuration:

    jenkins_auth_realm:
      name: unix
      service: su
      plain_password: jenkins


#### Seed job configuration

Seed job is configured in `jenkins_seed_job` variable, which has the following
attributes:

* `name`:  Name of the job in Jenkins.
* `time_trigger`: A Jenkins cron entry defining how often this job should run.
* `removed_job_action`: what to do when a job created by a previous run of seed job
  is missing from current run. This can be either `DELETE` or`IGNORE`.
* `removed_view_action`: what to do when a view created by a previous run of seed job
  is missing from current run. This can be either `DELETE` or`IGNORE`.
* `scm`: Scm object is used to define seed job repository and related settings.
  It has the following properties:
  * `scm.type`: It must have value of `git`.
  * `scm.url`: URL for the repository.
  * `scm.credential_id`: Id of a credential to use when authenticating to the
    repository.
    This setting is optional. If it is missing or falsy, credentials will be omitted.
    Please note that when you use ssh repository url, you'll need to set up a key regardless
    of whether the repository is public or private (to establish an ssh connection
    you need a valid public key).
  * `scm.target_jobs`: A shell glob expression relative to repo root selecting
    jobs to import.
  * `scm.additional_classpath`: A path relative to repo root, pointing to a
     directory that contains additional groovy scripts used by the seed jobs.

Example scm configuration:

    jenkins_seed_job:
      name: seed
      time_trigger: "H * * * *"
      removed_job_action: "DELETE"
      removed_view_action: "IGNORE"
      scm:
        type: git
        url: "git@github.com:edx/jenkins-job-dsl-internal.git"
        credential_id: "github-deploy-key"
        target_jobs: "jobs/analytics-edx-jenkins.edx.org/*Jobs.groovy"
        additional_classpath: "src/main/groovy"

Known issues
------------

1. Playbook named `execute_ansible_cli.yaml`, should be converted to an
   Ansible module (it is already used in a module-ish way).
2. Anonymous user has discover and get job permission, as without it
   `get-job`, `build <<job>>` commands wouldn't work.
   Giving anonymous these permissions is a workaround for
   transient Jenkins issue (reported [couple][1] [of][2] [times][3]).
3. We force unix authentication method -- that is, every user that can login
   to Jenkins also needs to have a shell account on master.


Dependencies
------------

- `jenkins_master`

[1]: https://issues.jenkins-ci.org/browse/JENKINS-12543
[2]: https://issues.jenkins-ci.org/browse/JENKINS-11024
[3]: https://issues.jenkins-ci.org/browse/JENKINS-22143
