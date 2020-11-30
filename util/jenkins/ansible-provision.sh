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

extra_vars_file="/var/tmp/extra-vars-$$.yml"
sandbox_secure_vars_file="${WORKSPACE}/configuration-secure/ansible/vars/developer-sandbox.yml"
sandbox_internal_vars_file="${WORKSPACE}/configuration-internal/ansible/vars/developer-sandbox.yml"
extra_var_arg="-e@${extra_vars_file}"
program_console="false"

if [[ $edx_internal == "true" ]]; then
    # if this is a an edx server include
    # the secret var file
    extra_var_arg="-e@${sandbox_internal_vars_file} -e@${sandbox_secure_vars_file} -e@${extra_vars_file} -e DECRYPT_CONFIG_PRIVATE_KEY=$WORKSPACE/configuration-secure/ansible/keys/sandbox-remote-config/sandbox/private.key -e ENCRYPTED_CFG_DIR=$WORKSPACE/configuration-internal/sandbox-remote-config/sandbox -e UNENCRYPTED_CFG_DIR=$WORKSPACE"
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
    ami="ami-0c9c19b09d5dbaf26"
  elif [[ $server_type == "ubuntu_18.04" ]]; then
    ami="ami-07ebfd5b3428b6f4d"
  elif [[ $server_type == "ubuntu_20.04" ]]; then
    ami="ami-05cf2c352da0bfb2e"
    # Ansible will always use Python3 interpreter on Ubuntu 20.04 hosts to execute modules
    extra_var_arg+=' -e ansible_python_interpreter=auto'
  elif [[ $server_type == "ubuntu_16.04" || $server_type == "full_edx_installation_from_scratch" ]]; then
    ami="ami-092546daafcc8bc0d"
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

if [[ -z $registrar ]]; then
  registrar="false"
fi

if [[ -z $registrar_version ]]; then
  REGISTRAR_VERSION="master"
fi

if [[ -z $learner_portal ]]; then
  learner_portal="false"
fi

if [[ -z $learner_portal_version ]]; then
  LEARNER_PORTAL_VERSION="master"
fi

if [[ -z $prospectus ]]; then
  prospectus="false"
fi

if [[ -z $prospectus_version ]]; then
  PROSPECTUS_VERSION="master"
fi

if [[ $registrar == 'true' ]]; then
  program_console="true"
fi

if [[ -z $logistration ]]; then
  logistration="false"
fi

if [[ -z $logistration_version ]]; then
  LOGISTRATION_MFE_VERSION="master"
fi

if [[ -z $payment ]]; then
  payment="false"
fi

if [[ -z $payment_version ]]; then
  PAYMENT_MFE_VERSION="master"
fi

# Lowercase the dns name to deal with an ansible bug
dns_name="${dns_name,,}"

deploy_host="${dns_name}.${dns_zone}"
ssh-keygen -f "/var/lib/jenkins/.ssh/known_hosts" -R "$deploy_host"

cd playbooks

cat << EOF > $extra_vars_file
EDX_PLATFORM_VERSION: $edxapp_version
FORUM_VERSION: $forum_version
XQUEUE_VERSION: $xqueue_version
CERTS_VERSION: $certs_version
CONFIGURATION_VERSION: $configuration_version
DEMO_VERSION: $demo_version
THEMES_VERSION: $themes_version
REGISTRAR_VERSION: $registrar_version
LEARNER_PORTAL_VERSION: $learner_portal_version
PROGRAM_CONSOLE_VERSION: $program_console_version
PROSPECTUS_VERSION: $prospectus_version

edx_ansible_source_repo: ${configuration_source_repo}
edx_platform_repo: ${edx_platform_repo}

EDXAPP_PLATFORM_NAME: $sandbox_platform_name
SANDBOX_CONFIG: True
CONFIGURE_JWTS: True

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

REGISTRAR_NGINX_PORT: 80
REGISTRAR_SSL_NGINX_PORT: 443
REGISTRAR_VERSION: $registrar_version
REGISTRAR_ENABLED: $registrar

LEARNER_PORTAL_NGINX_PORT: 80
LEARNER_PORTAL_SSL_NGINX_PORT: 443
LEARNER_PORTAL_VERSION: $learner_portal_version
LEARNER_PORTAL_ENABLED: $learner_portal
LEARNER_PORTAL_SANDBOX_BUILD: True

PROGRAM_CONSOLE_NGINX_PORT: 80
PROGRAM_CONSOLE_SSL_NGINX_PORT: 443
PROGRAM_CONSOLE_VERSION: $program_console_version
PROGRAM_CONSOLE_ENABLED: $program_console
PROGRAM_CONSOLE_SANDBOX_BUILD: True

PROSPECTUS_NGINX_PORT: 80
PROSPECTUS_SSL_NGINX_PORT: 443
PROSPECTUS_VERSION: $prospectus_version
PROSPECTUS_ENABLED: $prospectus
PROSPECTUS_SANDBOX_BUILD: True

LOGISTRATION_NGINX_PORT: 80
LOGISTRATION_SSL_NGINX_PORT: 443
LOGISTRATION_MFE_VERSION: $logistration_version
LOGISTRATION_ENABLED: $logistration
LOGISTRATION_SANDBOX_BUILD: True

PAYMENT_NGINX_PORT: 80
PAYMENT_SSL_NGINX_PORT: 443
PAYMENT_MFE_VERSION: $payment_version
PAYMENT_MFE_ENABLED: $payment
PAYMENT_SANDBOX_BUILD: True

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
COMMON_DEPLOY_HOSTNAME: ${deploy_host}
COMMON_DEPLOYMENT: edx
COMMON_ENVIRONMENT: sandbox
COMMON_LMS_BASE_URL: https://${deploy_host}

nginx_default_sites:
  - lms

mysql_server_version_5_7: True

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
    cat << EOF >> $extra_vars_file
EDXAPP_PREVIEW_LMS_BASE: preview-${deploy_host}
EDXAPP_LMS_BASE: ${deploy_host}
EDXAPP_CMS_BASE: studio-${deploy_host}
EDXAPP_SITE_NAME: ${deploy_host}
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

DISCOVERY_URL_ROOT: "https://discovery-${deploy_host}"
DISCOVERY_SOCIAL_AUTH_REDIRECT_IS_HTTPS: true

REGISTRAR_URL_ROOT: "https://registrar-${deploy_host}"
REGISTRAR_API_ROOT: "https://registrar-${deploy_host}/api"
REGISTRAR_DISCOVERY_BASE_URL: "https://discovery-${deploy_host}"
REGISTRAR_LMS_BASE_URL: "https://${deploy_host}"
REGISTRAR_SOCIAL_AUTH_REDIRECT_IS_HTTPS: true

LEARNER_PORTAL_URL_ROOT: "https://learner-portal-${deploy_host}"
LEARNER_PORTAL_DISCOVERY_BASE_URL: "https://discovery-${deploy_host}"
LEARNER_PORTAL_LMS_BASE_URL: "https://${deploy_host}"

PROGRAM_CONSOLE_URL_ROOT: "https://program-console-${deploy_host}"
PROGRAM_CONSOLE_DISCOVERY_BASE_URL: "https://discovery-${deploy_host}"
PROGRAM_CONSOLE_LMS_BASE_URL: "https://${deploy_host}"
PROGRAM_CONSOLE_REGISTRAR_API_BASE_URL: "https://registrar-${deploy_host}/api"

PROSPECTUS_URL_ROOT: "https://prospectus-${deploy_host}"
OAUTH_ID: "{{ PROSPECTUS_OAUTH_ID }}"
OAUTH_SECRET: "{{ PROSPECTUS_OAUTH_SECRET }}"

LOGISTRATION_URL_ROOT: "https://logistration-${deploy_host}"
PAYMENT_URL_ROOT: "https://payment-${deploy_host}"
PAYMENT_ECOMMERCE_BASE_URL: "https://ecommerce-${deploy_host}"
PAYMENT_LMS_BASE_URL: "https://${deploy_host}"

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

encrypted_config_apps=(edxapp ecommerce ecommerce_worker analytics_api insights discovery credentials registrar edx_notes_api)

for app in ${encrypted_config_apps[@]}; do
     eval app_decrypt_and_copy_config_enabled=\${${app}_decrypt_and_copy_config_enabled}
     if [[ ${app_decrypt_and_copy_config_enabled} == "true" ]]; then
         cat << EOF >> $extra_vars_file
${app^^}_DECRYPT_CONFIG_ENABLED: true
${app^^}_COPY_CONFIG_ENABLED: true
EOF
     fi
done

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

# ansible overrides for master's integration environment setup
if [[ $registrar == "true" ]]; then
    cat << EOF >> $extra_vars_file
COMMON_ENABLE_SPLUNKFORWARDER: true,
EDXAPP_ENABLE_ENROLLMENT_RESET: true,
EOF
fi

declare -A deploy
plays="prospectus edxapp forum ecommerce credentials discovery analyticsapi veda_web_frontend veda_pipeline_worker veda_encode_worker video_pipeline_integration xqueue certs demo testcourses registrar program_console learner_portal"

for play in $plays; do
    deploy[$play]=${!play}
done

# If reconfigure was selected or if starting from an ubuntu 16.04 AMI
# run non-deploy tasks for all plays
if [[ $reconfigure == "true" || $server_type == "full_edx_installation_from_scratch" || $server_type == "ubuntu_20.04" ]]; then
    cat $extra_vars_file
    run_ansible edx_continuous_integration.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
fi

if [[ $reconfigure != "true" && $server_type == "full_edx_installation" ]]; then
    # Run deploy tasks for the plays selected
    for i in $plays; do
        if [[ ${deploy[$i]} == "true" ]]; then
            cat $extra_vars_file
            run_ansible ${i}.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
            if [[ ${i} == "edxapp" ]]; then
                run_ansible worker.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
            fi
        fi
    done
fi

# deploy the edx_ansible play
run_ansible edx_ansible.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
cat $sandbox_secure_vars_file $sandbox_internal_vars_file $extra_vars_file | grep -v -E "_version|migrate_db" > ${extra_vars_file}_clean
ansible -c ssh -i "${deploy_host}," $deploy_host -m copy -a "src=${extra_vars_file}_clean dest=/edx/app/edx_ansible/server-vars.yml" -u ubuntu -b
ret=$?
if [[ $ret -ne 0 ]]; then
  exit $ret
fi

if [[ $run_oauth == "true" ]]; then
    # Setup the OAuth2 clients
    run_ansible oauth_client_setup.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
fi

# set the hostname
run_ansible set_hostname.yml -i "${deploy_host}," -e hostname_fqdn=${deploy_host} --user ubuntu

# master's integration environment setup
if [[ $registrar == "true" ]]; then
  # vars specific to master's integration environment
  cat << EOF >> $extra_vars_file
username: $registrar_user_email
email: $registrar_user_email
organization_key: $registrar_org_key
registrar_role: "organization_read_write_enrollments"
EOF
  run_ansible masters_sandbox.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
fi

# prospectus sandbox
if [[ $prospectus == "true" ]]; then
   run_ansible prospectus_sandbox.yml -i "${deploy_host}," $extra_var_arg --user ubuntu
fi

if [[ $enable_newrelic == "true" ]]; then
    run_ansible run_role.yml -i "${deploy_host}," -e role=newrelic_infrastructure $extra_var_arg  --user ubuntu
fi

rm -f "$extra_vars_file"
rm -f ${extra_vars_file}_clean
