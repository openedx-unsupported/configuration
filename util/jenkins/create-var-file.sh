cat << EOF > $extra_vars
---
ansible_ssh_private_key_file: /var/lib/jenkins/${keypair}.pem
EDXAPP_PREVIEW_LMS_BASE: preview.${deploy_host}
EDXAPP_LMS_BASE: ${deploy_host}
EDXAPP_LMS_NGINX_PORT: 80
EDXAPP_LMS_PREVIEW_NGINX_PORT: 80
EDXAPP_CMS_NGINX_PORT: 80
COMMON_PYPI_MIRROR_URL: 'https://pypi.edx.org/root/pypi/+simple/'
COMMON_GIT_MIRROR: 'git.edx.org'
XSERVER_GRADER_DIR: "{{ xserver_data_dir }}/data/content-mit-600x~2012_Fall"
XSERVER_GRADER_SOURCE: "git@github.com:/MITx/6.00x.git"
XSERVER_LOCAL_GIT_IDENTITY: /var/lib/jenkins/git-identity-edx-pull
CERTS_LOCAL_GIT_IDENTITY: /var/lib/jenkins/git-identity-edx-pull
CERTS_AWS_KEY: $(cat /var/lib/jenkins/certs-aws-key)
CERTS_AWS_ID: $(cat /var/lib/jenkins/certs-aws-id) 
CERTS_BUCKET: "verify-test.edx.org"
migrate_db: "yes"
openid_workaround: True
EOF

cat $extra_vars


