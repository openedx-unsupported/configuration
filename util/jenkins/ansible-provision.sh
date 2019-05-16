#!/usr/bin/env bash

# Ansible provisioning wrapper script that
# assumes the following parameters set
# as environment variables
#
# - github_username
# - server_type
# - instance_type
# - region
# - aws_account
# - keypair
# - ami
# - root_ebs_size
# - security_group
# - dns_zone
# - dns_name
# - environment
# - name_tag
set -x

# Seeing the environment is fine, spewing secrets to the log isn't ok
env | grep -v AWS | grep -v ARN
#export ssh_key=
export PYTHONUNBUFFERED=1
export BOTO_CONFIG=/var/lib/jenkins/${aws_account}.boto

# docker on OS-X includes your Mac's home directory in the socket path
# that SSH/Ansible uses for the control socket, pushing you over
# the 108 character limit.
if [ -f /.dockerenv ]; then
    export ANSIBLE_SSH_CONTROL_PATH=/tmp/%%C
fi

run_ansible() {
  if [[ "$VERBOSE" == "true" ]]; then
    verbose_arg='-vvv'
  else
    verbose_arg=''
  fi

  ansible-playbook $verbose_arg $@
  ret=$?
  if [[ $ret -ne 0 ]]; then
    echo "Exiting RET"
    exit $ret
  fi
}

# This DATE_TIME will be used as instance launch time tag
if [[ ! -n ${sandbox_life//[0-9]/} ]]  && [[ ${sandbox_life} -le 30 ]]; then
    TERMINATION_DATE_TIME=`date +"%m-%d-%Y %T" --date "${sandbox_life=7} days"`
else
   echo "Please enter the valid value for the sandbox_life(between 1 to 30)"
   exit 1
fi


if [[ -z $BUILD_USER ]]; then
    BUILD_USER=jenkins
fi

if [[ -z $BUILD_USER_ID ]]; then
    BUILD_USER_ID=edx-sandbox
fi


if [[ -z $WORKSPACE ]]; then
    dir=$(dirname $0)
    source "$dir/ascii-convert.sh"
else
    source "$WORKSPACE/configuration/util/jenkins/ascii-convert.sh"
fi

if [[ -z $static_url_base ]]; then
  static_url_base="/static"
fi

if [[ -z $github_username  ]]; then
  github_username=$BUILD_USER_ID
fi

# Having access keys OR a boto config allows sandboxes to be built.
if [[ ( -z $AWS_ACCESS_KEY_ID || -z $AWS_SECRET_ACCESS_KEY ) && (! -f $BOTO_CONFIG) ]]; then
  echo "AWS credentials not found for $aws_account"
  exit 1
fi

############### MCKa ############
AWS_DEFAULT_REGION=$region
InstanceNameTag=$dns_name
ForumConfigurationVersion="yonkers-ginkgo"
cd $WORKSPACE/configuration
pip install -r requirements.txt

cd $WORKSPACE
chmod -R 0777 private_vars/
rm -rf private_vars/
git clone https://hamzamunir7300:hamza123@github.com/hamzamunir7300/private_vars.git
chmod -R 0777 private_vars/
private_vars_file="${WORKSPACE}/private_vars/top_secret.yml"

cd $WORKSPACE/configuration
declare -A sso=("saml-idp-mckinsey")
declare -A langs
langs["en"]="English"
##### end MCKa ################################
extra_vars_file="/var/tmp/extra-vars-$$.yml"
sandbox_secure_vars_file="${WORKSPACE}/configuration-secure/ansible/vars/developer-sandbox.yml"
sandbox_internal_vars_file="${WORKSPACE}/configuration-internal/ansible/vars/developer-sandbox.yml"
extra_var_arg="-e@${extra_vars_file}"



if [[ $edx_internal == "true" ]]; then
    # if this is a an edx server include
    # the secret var file
    extra_var_arg="-e@${sandbox_internal_vars_file} -e@${sandbox_secure_vars_file} -e@${extra_vars_file}"
    extra_var_arg+=" -e@${private_vars_file}"
fi

if [[ -z $region ]]; then
  region="us-east-1"
fi

# edX has reservations for sandboxes in this zone, don't change without updating reservations.
if [[ -z $zone ]]; then
  zone="us-east-1c"
fi

if [[ -z $vpc_subnet_id ]]; then
  vpc_subnet_id="subnet-cd867aba"
fi

if [[ -z $elb ]]; then
  elb="false"
fi

if [[ -z $dns_name ]]; then
  dns_name=${github_username}
fi

if [[ -z $name_tag ]]; then
  name_tag=${github_username}-${environment}
fi

if [[ -z $sandbox_platform_name ]]; then
    sandbox_platform_name=$dns_name
fi

if [[ -z $ami ]]; then
  if [[ $server_type == "full_edx_installation" ]]; then
    ami="ami-0b7431fd58e78be07"
  elif [[ $server_type == "ubuntu_16.04" || $server_type == "full_edx_installation_from_scratch" ]]; then
    ami="ami-04169656fea786776"
  fi
fi

if [[ -z $instance_type ]]; then
  instance_type="r5.large"
fi

if [[ -z $instance_initiated_shutdown_behavior ]]; then
  instance_initiated_shutdown_behavior="terminate"
fi

if [[ -z $enable_newrelic ]]; then
  enable_newrelic="false"
fi

if [[ -z $enable_datadog ]]; then
  enable_datadog="false"
fi

if [[ -z $performance_course ]]; then
  performance_course="false"
fi

if [[ -z $demo_test_course ]]; then
  demo_test_course="false"
fi

if [[ -z $edx_demo_course ]]; then
  edx_demo_course="false"
fi

if [[ -z $enable_automatic_auth_for_testing ]]; then
  enable_automatic_auth_for_testing="false"
fi

if [[ -z $enable_client_profiling ]]; then
  enable_client_profiling="false"
fi

if [[ -z $set_whitelabel ]]; then
  set_whitelabel="true"
fi

if [[ -z $journals ]]; then
  journals="false"
fi

if [[ -z $journals_version ]]; then
  journals_version="master"
fi


# Lowercase the dns name to deal with an ansible bug
dns_name="${dns_name,,}"
deploy_host="${dns_name}.${dns_zone}"
ssh-keygen -f "/var/lib/jenkins/.ssh/known_hosts" -R "$deploy_host"

cd playbooks

cat << EOF > $extra_vars_file
edx_platform_version: $edxapp_version
forum_version: $forum_version
forum_ruby_version: '2.3.7'
rbenv_bundler_version: '1.16.0'
mcka_apros_ruby_version: '2.3.7'
forum_source_repo: 'https://github.com/edx-solutions/cs_comments_service.git'
ansible_distribution: 'Ubuntu'
ansible_distribution_release: 'xenial'
notifier_version: $notifier_version
XQUEUE_VERSION: $xqueue_version
xserver_version: $xserver_version
certs_version: $certs_version
configuration_version: $configuration_version
demo_version: $demo_version
THEMES_VERSION: $themes_version
journals_version: $journals_version
edxapp_user_shell: '/bin/bash'
edxapp_user_createhome: 'yes'
migrate_db: false
mongo_enable_journal: false
service_variants_enabled: []
testing_requirements_file: "{{ edxapp_code_dir }}/requirements/edx/testing.txt"
edx_ansible_source_repo: ${configuration_source_repo}
edx_platform_repo: ${edx_platform_repo}

edx_platform_repo: "git@github.com:edx-solutions/edx-platform.git"
edx_platform_version: "master"

edxapp_theme_version: "development"


mcka_apros_source_repo: "git@github.com:mckinseyacademy/mcka_apros.git"
mcka_apros_version: "development"


forum_source_repo: "https://github.com/edx-solutions/cs_comments_service.git"
forum_version: "master"


EDXAPP_PLATFORM_NAME: $sandbox_platform_name

EDXAPP_STATIC_URL_BASE: $static_url_base
EDXAPP_LMS_NGINX_PORT: 80
EDXAPP_CMS_NGINX_PORT: 80

ECOMMERCE_NGINX_PORT: 80
ECOMMERCE_SSL_NGINX_PORT: 443
ECOMMERCE_VERSION: $ecommerce_version

CREDENTIALS_NGINX_PORT: 80
CREDENTIALS_SSL_NGINX_PORT: 443
CREDENTIALS_VERSION: $credentials_version

ANALYTICS_API_NGINX_PORT: 80
ANALYTICS_API_SSL_NGINX_PORT: 443
ANALYTICS_API_VERSION: $analytics_api_version

JOURNALS_NGINX_PORT: 80
JOURNALS_SSL_NGINX_PORT: 443
JOURNALS_VERSION: $journals_version
JOURNALS_ENABLED: $journals
JOURNALS_SANDBOX_BUILD: True

VIDEO_PIPELINE_BASE_NGINX_PORT: 80
VIDEO_PIPELINE_BASE_SSL_NGINX_PORT: 443

DISCOVERY_NGINX_PORT: 80
DISCOVERY_SSL_NGINX_PORT: 443
DISCOVERY_VERSION: $discovery_version
NGINX_SET_X_FORWARDED_HEADERS: True
NGINX_REDIRECT_TO_HTTPS: True
EDX_ANSIBLE_DUMP_VARS: true
migrate_db: "yes"
dns_name: $dns_name
COMMON_HOSTNAME: $dns_name
COMMON_DEPLOYMENT: edx
COMMON_ENVIRONMENT: sandbox

# Todo: Uncomment these temp if found any related error otherwise, remove these below after testing
#NGINX_ENABLE_SSL: false
#_local_git_identity: $ssh_key
#EDXAPP_USE_GIT_IDENTITY: true
EDXAPP_ENABLE_COMPREHENSIVE_THEMING: false

#EDXAPP_EDXAPP_SECRET_KEY: "DUMMY KEY CHANGE BEFORE GOING TO PRODUCTION"
COMMON_EDXAPP_SETTINGS: 'aws'
EDXAPP_SETTINGS: 'aws'

#mcka_apros_git_ssh:
MCKA_APROS_AWS_STORAGE_BUCKET_NAME: 'qa-group-work'
MCKA_APROS_SSO_AUTOPROVISION_PROVIDERS: $sso
MCKA_APROS_SUPPORTED_LANGUAGES:
    en: English
HEAP_APP_ID: 123123432
MCKA_APROS_MILESTONES_ENABLED: false
MCKA_APROS_API_KEY: "edx-api-key"
BASE_DOMAIN: $deploy_host
EDXAPP_BASE: $deploy_host
EDXAPP_LMS_SUBDOMAIN: "apros"
EDXAPP_LMS_BASE: "{{EDXAPP_LMS_SUBDOMAIN}}.{{EDXAPP_BASE}}"
EDXAPP_CORS_ORIGIN_WHITELIST:
  - "{{ EDXAPP_LMS_BASE }}"
EDXAPP_SESSION_COOKIE_DOMAIN: ".{{EDXAPP_LMS_SUBDOMAIN}}.{{EDXAPP_BASE}}"
EDXAPP_PREVIEW_LMS_BASE: "preview.{{EDXAPP_LMS_BASE}}"
EDXAPP_SITE_NAME: "{{EDXAPP_LMS_BASE}}"
LMS_ELB: "courses.{{BASE_DOMAIN}}"
CMS_ELB: "studio.{{BASE_DOMAIN}}"
CMS_HOSTNAME: "studio.{{BASE_DOMAIN}}"
APROS_ELB: "{{BASE_DOMAIN}}"
APROS_WORKER_LMS_BASE: "https://{{ LMS_ELB }}/"
APROS_WORKER_CMS_BASE: "https://{{ CMS_ELB }}/"
MCKA_APROS_USE_GIT_IDENTITY: true
MCKA_APROS_AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
MCKA_APROS_AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
MCKA_APROS_DJANGO_SECRET_KEY: "DUMMY KEY"
#MMCKA_APROS_MYSQL_DB_NAME: "mcka_apros"
MCKINSEY_APROS_MYSQL_DB_NAME: "mcka_apros"
MCKA_APROS_MYSQL_USER: "apros"
MCKA_APROS_THIRD_PARTY_AUTH_API_SECRET: "third_party_secret"
MCKA_APROS_MYSQL_PORT:  "{{ EDXAPP_MYSQL_PORT }}"
#MCKA_APROS_MYSQL_HOST: "localhost"
MCKINSEY_APROS_MYSQL_HOST: "localhost"
MCKA_APROS_MYSQL_PASSWORD: "apros"
MCKINSEY_APROS_MYSQL_PASSWORD: "apros"
MCKINSEY_APROS_MYSQL_USER: "apros"
db_root_user: "root"
DBPassword: ""
MCKA_APROS_WORKERS: 6
WORKER_DEFAULT_CONCURRENCY: 1
WORKER_HIGH_CONCURRENCY: 5
#CELERY_HEARTBEAT_ENABLED: false
#CREATE_SERVICE_WORKER_USERS: true
#EDXAPP_REINDEX_ALL_COURSES: false
#SIMPLETHEME_ENABLE_DEPLOY: false
EDXAPP_CELERY_BROKER_HOSTNAME: 'localhost'
EDXAPP_CELERY_BROKER_TRANSPORT: 'redis'
EDXAPP_CELERY_USER: ''
EDXAPP_CELERY_BROKER_VHOST: 0
celery_worker: false
EDXAPP_CELERY_WORKERS:
    - concurrency: 3
      monitor: true
      queue: default
      service_variant: cms
      max_tasks_per_child: 5000
    - concurrency: 1
      monitor: true
      queue: high
      service_variant: cms
      max_tasks_per_child: 5000
    - concurrency: 2
      monitor: true
      queue: default
      service_variant: lms
      max_tasks_per_child: 5000
    - concurrency: 2
      monitor: true
      queue: high
      service_variant: lms
      max_tasks_per_child: 5000
    - concurrency: 1
      max_tasks_per_child: 1
      monitor: false
      queue: high_mem
      service_variant: lms
      max_tasks_per_child: 5000
    - concurrency: 2
      monitor: true
      queue: completion_aggregator
      service_variant: lms
      max_tasks_per_child: 10000
mcka_apros_version: "development"
mcka_apros_gunicorn_port: 3000
MCKA_APROS_GUNICORN_EXTRA_CONF: 'preload_app = True'
MCKA_APROS_GUNICORN_MAX_REQUESTS: 1000
nginx_default_sites:
  - lms

# User provided extra vars
$extra_vars
EOF

if [[ $basic_auth == "true" ]]; then
    # vars specific to provisioning added to $extra-vars
    cat << EOF_AUTH >> $extra_vars_file
COMMON_ENABLE_BASIC_AUTH: True
COMMON_HTPASSWD_USER: $auth_user
COMMON_HTPASSWD_PASS: $auth_pass
XQUEUE_BASIC_AUTH_USER: $auth_user
XQUEUE_BASIC_AUTH_PASSWORD: $auth_pass
EOF_AUTH

else
    cat << EOF_AUTH >> $extra_vars_file
COMMON_ENABLE_BASIC_AUTH: False
EOF_AUTH

fi

if [[ -n $nginx_users ]]; then
   cat << EOF_AUTH >> $extra_vars_file
NGINX_USERS: $nginx_users
EOF_AUTH
fi

if [[ $enable_client_profiling == "true" ]]; then
    cat << EOF_PROFILING >> $extra_vars_file
EDXAPP_SESSION_SAVE_EVERY_REQUEST: True
EOF_PROFILING
fi

if [[ $edx_internal == "true" ]]; then
    # if this isn't a public server add the github
    # user and set edx_internal to True so that
    # xserver is installed
    cat << EOF >> $extra_vars_file
EDXAPP_PREVIEW_LMS_BASE: preview-${deploy_host}
#EDXAPP_LMS_BASE: ${deploy_host}
EDXAPP_CMS_BASE: "{{ CMS_ELB }}"
#EDXAPP_SITE_NAME: ${deploy_host}
CERTS_DOWNLOAD_URL: "http://${deploy_host}:18090"
CERTS_VERIFY_URL: "http://${deploy_host}:18090"
edx_internal: True
COMMON_USER_INFO:
  - name: ${github_username}
    github: true
    type: admin
USER_CMD_PROMPT: '[$name_tag] '
COMMON_ENABLE_NEWRELIC_APP: $enable_newrelic
COMMON_ENABLE_DATADOG: $enable_datadog
COMMON_OAUTH_BASE_URL: "https://${deploy_host}"
FORUM_NEW_RELIC_ENABLE: $enable_newrelic
ENABLE_PERFORMANCE_COURSE: $performance_course
ENABLE_DEMO_TEST_COURSE: $demo_test_course
ENABLE_EDX_DEMO_COURSE: $edx_demo_course
EDXAPP_ENABLE_AUTO_AUTH: $enable_automatic_auth_for_testing
EDXAPP_NEWRELIC_LMS_APPNAME: sandbox-${dns_name}-edxapp-lms
EDXAPP_NEWRELIC_CMS_APPNAME: sandbox-${dns_name}-edxapp-cms
EDXAPP_NEWRELIC_WORKERS_APPNAME: sandbox-${dns_name}-edxapp-workers
XQUEUE_NEWRELIC_APPNAME: sandbox-${dns_name}-xqueue
XQUEUE_CONSUMER_NEWRELIC_APPNAME: sandbox-${dns_name}-xqueue_consumer
FORUM_NEW_RELIC_APP_NAME: sandbox-${dns_name}-forums
SANDBOX_USERNAME: $github_username
EDXAPP_ECOMMERCE_PUBLIC_URL_ROOT: "https://ecommerce-${deploy_host}"
EDXAPP_ECOMMERCE_API_URL: "https://ecommerce-${deploy_host}/api/v2"
EDXAPP_DISCOVERY_API_URL: "https://discovery-${deploy_host}/api/v1"
EDXAPP_COURSE_CATALOG_API_URL: "{{ EDXAPP_DISCOVERY_API_URL }}"

ANALYTICS_API_LMS_BASE_URL: "https://{{ EDXAPP_LMS_BASE }}/"

# NOTE: This is the same as DISCOVERY_URL_ROOT below
ECOMMERCE_DISCOVERY_SERVICE_URL: "https://discovery-${deploy_host}"
ECOMMERCE_ECOMMERCE_URL_ROOT: "https://ecommerce-${deploy_host}"
ECOMMERCE_LMS_URL_ROOT: "https://${deploy_host}"
ECOMMERCE_SOCIAL_AUTH_REDIRECT_IS_HTTPS: true
ecommerce_create_demo_data: true

JOURNALS_URL_ROOT: "https://journals-{{ EDXAPP_LMS_BASE }}"
JOURNALS_FRONTEND_URL: "https://journalsapp-{{ EDXAPP_LMS_BASE }}"
JOURNALS_API_URL: "https://journals-{{ EDXAPP_LMS_BASE }}/api/v1/"
JOURNALS_DISCOVERY_SERVICE_URL: "https://discovery-{{ EDXAPP_LMS_BASE }}"
JOURNALS_LMS_URL_ROOT: "https://{{ EDXAPP_LMS_BASE }}"
JOURNALS_SOCIAL_AUTH_REDIRECT_IS_HTTPS: true
JOURNALS_DISCOVERY_API_URL: "{{ JOURNALS_DISCOVERY_SERVICE_URL }}/api/v1/"
JOURNALS_DISCOVERY_JOURNALS_API_URL: "{{ JOURNALS_DISCOVERY_SERVICE_URL }}/journal/api/v1/"
JOURNALS_ECOMMERCE_BASE_URL: "{{ ECOMMERCE_ECOMMERCE_URL_ROOT }}"
JOURNALS_ECOMMERCE_API_URL: "{{ JOURNALS_ECOMMERCE_BASE_URL }}/api/v2/"
JOURNALS_ECOMMERCE_JOURNALS_API_URL: "{{ JOURNALS_ECOMMERCE_BASE_URL }}/journal/api/v1"
journals_create_demo_data: true

DISCOVERY_URL_ROOT: "https://discovery-${deploy_host}"
DISCOVERY_SOCIAL_AUTH_REDIRECT_IS_HTTPS: true

credentials_create_demo_data: true
CREDENTIALS_LMS_URL_ROOT: "https://${deploy_host}"
CREDENTIALS_DOMAIN: "credentials-${deploy_host}"
CREDENTIALS_URL_ROOT: "https://{{ CREDENTIALS_DOMAIN }}"
CREDENTIALS_SOCIAL_AUTH_REDIRECT_IS_HTTPS: true
CREDENTIALS_DISCOVERY_API_URL: "{{ DISCOVERY_URL_ROOT }}/api/v1/"

VIDEO_PIPELINE_DOMAIN: "veda-${deploy_host}"
VIDEO_PIPELINE_BASE_URL_ROOT: "https://{{ VIDEO_PIPELINE_DOMAIN }}"
VIDEO_PIPELINE_BASE_LMS_BASE_URL: "https://{{ EDXAPP_LMS_BASE }}"

VEDA_WEB_FRONTEND_VERSION: ${video_pipeline_version:-master}
VEDA_PIPELINE_WORKER_VERSION: ${video_pipeline_version:-master}
VEDA_ENCODE_WORKER_VERSION: ${video_encode_worker_version:-master}

EOF
fi


if [[ $recreate == "true" ]]; then
    # vars specific to provisioning added to $extra-vars
    cat << EOF >> $extra_vars_file
dns_name: $dns_name
keypair: $keypair
instance_type: $instance_type
security_group: $security_group
ami: $ami
region: $region
zone: $zone
instance_initiated_shutdown_behavior: $instance_initiated_shutdown_behavior
instance_tags:
    environment: $environment
    github_username: $github_username
    Name: $name_tag
    source: jenkins
    owner: $BUILD_USER
    instance_termination_time: $TERMINATION_DATE_TIME
    datadog: monitored
root_ebs_size: $root_ebs_size
name_tag: $name_tag
dns_zone: $dns_zone
elb: $elb
EOF


    if [[ $server_type == "full_edx_installation" ]]; then
        extra_var_arg+=' -e instance_userdata="" -e launch_wait_time=0 -e elb_pre_post=false'
    fi
    # run the tasks to launch an ec2 instance from AMI
    cat $extra_vars_file
    cd $WORKSPACE/configuration/playbooks/edx-east
    run_ansible edx_provision.yml -i inventory.ini $extra_var_arg --user ubuntu

    if [[ $server_type == "full_edx_installation" ]]; then
        # additional tasks that need to be run if the
        # entire edx stack is brought up from an AMI
        run_ansible redis.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
        run_ansible restart_supervisor.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
    fi
fi

veda_web_frontend=${video_pipeline:-false}
veda_pipeline_worker=${video_pipeline:-false}
veda_encode_worker=${video_encode_worker:-false}
video_pipeline_integration=${video_pipeline:-false}

#declare -A deploy

#plays="edxapp forum ecommerce credentials discovery journals analyticsapi veda_web_frontend veda_pipeline_worker veda_encode_worker video_pipeline_integration notifier xqueue xserver certs demo testcourses"
# ToDO: Below list is temp, remove it and use above after testing.
#plays="edxapp forum certs demo testcourses"

#for play in $plays; do
#    deploy[$play]=${!play}
#done

# If reconfigure was selected or if starting from an ubuntu 16.04 AMI
# run non-deploy tasks for all plays
if [[ $reconfigure == "true" || $server_type == "full_edx_installation_from_scratch" ]]; then
    cat $extra_vars_file
    #run_ansible edx_continuous_integration.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
fi

#TODO: remove this
#if [[ $reconfigure != "true" && $server_type == "full_edx_installation" ]]; then
#    # Run deploy tasks for the plays selected
#    for i in $plays; do
#        if [[ ${deploy[$i]} == "true" ]]; then
#            cat $extra_vars_file
#            run_ansible ${i}.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
#            if [[ ${i} == "edxapp" ]]; then
#                run_ansible worker.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
#            fi
#        fi
#    done
#fi

# deploy the edx_ansible play
run_ansible edx_ansible.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
cat $sandbox_secure_vars_file $sandbox_internal_vars_file $extra_vars_file | grep -v -E "_version|migrate_db" > ${extra_vars_file}_clean
ansible -c ssh -i "${deploy_host}," $deploy_host -m copy -a "src=${extra_vars_file}_clean dest=/edx/app/edx_ansible/server-vars.yml" -u ubuntu -b
ret=$?
if [[ $ret -ne 0 ]]; then
  echo "Exiting RET 2"
  exit $ret
fi

extra_var_arg+=' -e edx_platform_version="development" -e forum_version="master" -e migrate_db="no"'
cd $WORKSPACE/ansible-private

#IpAddress=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=$InstanceNameTag" --output text --query 'Reservations[*].Instances[*].[PrivateIpAddress]')

run_ansible -i "${deploy_host}," mckinsey-create-dbs.yml $extra_var_arg --user ubuntu

run_ansible -i "${deploy_host}," mckinseyapros.yml $extra_var_arg --user ubuntu


cd $WORKSPACE/configuration/playbooks/edx-east

git checkout $ForumConfigurationVersion

run_ansible -i "${deploy_host}," forum.yml $extra_var_arg --user ubuntu

PATTERN='all'
ansible ${PATTERN} -i "${deploy_host}," -u ubuntu -m shell -a 'sudo -u www-data /edx/app/edxapp/venvs/edxapp/bin/python /edx/app/edxapp/edx-platform/manage.py lms migrate --settings aws --noinput'
ansible ${PATTERN} -i "${deploy_host}," -u ubuntu -m shell -a 'sudo -u www-data /edx/app/edxapp/venvs/edxapp/bin/python /edx/app/edxapp/edx-platform/manage.py cms migrate --settings aws --noinput'
ansible ${PATTERN} -i "${deploy_host}," -u ubuntu -m shell -a 'sudo -u mcka_apros /edx/app/mcka_apros/venvs/mcka_apros/bin/python /edx/app/mcka_apros/mcka_apros/manage.py migrate --noinput'



if [[ $run_oauth == "true" ]]; then
    # Setup the OAuth2 clients
    run_ansible oauth_client_setup.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
fi

# set the hostname
run_ansible set_hostname.yml -i "${deploy_host}," -e hostname_fqdn=${deploy_host} --user ubuntu

if [[ $set_whitelabel == "true" ]]; then
    # Setup Whitelabel themes
    run_ansible whitelabel.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
fi

if [[ $enable_newrelic == "true" ]]; then
    run_ansible ../run_role.yml -i "${deploy_host}," -e role=newrelic_infrastructure $extra_var_arg  --user ubuntu
fi

rm -f "$extra_vars_file"
rm -f ${extra_vars_file}_clean
