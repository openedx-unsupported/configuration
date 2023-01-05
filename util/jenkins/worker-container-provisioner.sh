#!/usr/bin/env bash

set -ex

# Install pre-reqs packages
function install_pre_reqs() {
  YQ_VERSION="4.27.5"
  wget https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64 -O /usr/bin/yq
  chmod +x /usr/bin/yq
}

# Render docker-compose file for celery workers
function render_docker_compose() {
  # Set common environment variables and volumes for edxapp celery workers
  if [ "${LC_WORKER_OF}" == "edxapp" ] ; then
    worker_service_volume_mappings=("/edx/var/edxapp:/edx/var/edxapp" "/edx/etc/lms.yml:/edx/etc/lms.yml" "/edx/etc/cms.yml:/edx/etc/cms.yml" "/edx/app/${LC_WORKER_OF}/.boto:/edx/app/${LC_WORKER_OF}/.boto" "/var/run/mysqld/mysqld.sock:/var/run/mysqld/mysqld.sock")
    worker_service_env_mappings=("CONCURRENCY=1" "LOGLEVEL=info" "LANG=en_US.UTF-8" "PYTHONPATH=/edx/app/${LC_WORKER_OF}/${LC_WORKER_SERVICE_REPO}" "BOTO_CONFIG=/edx/app/${LC_WORKER_OF}/.boto" "LMS_CFG=/edx/etc/lms.yml" "STUDIO_CFG=/edx/etc/cms.yml" "CMS_CFG=/edx/etc/cms.yml")
  fi

  worker_celery_path="/edx/app/${LC_WORKER_OF}/venvs/${LC_WORKER_OF}/bin/celery"
  readarray worker_cfg < <(echo "${LC_WORKER_CFG}" | yq e -o=j -I=0 '.worker_cfg[]')

  cat <<EOF > $1
---
version: "3.9"
services:
$(
  for worker_config in "${worker_cfg[@]}"; do
    worker_service_variant=$(echo "${worker_config}" | yq -e '.service_variant' -)
    worker_queue=$(echo "${worker_config}" | yq -e '.queue' -)
    worker_concurrency=$(echo "${worker_config}" | yq -e '.concurrency' -)
    prefetch_optimization=$(echo "${worker_config}" | yq -e '.prefetch_optimization' -)
    worker_service_name="${worker_service_variant}_${worker_queue}_${worker_concurrency}"
    echo -e "  ${worker_service_name}:"
    echo -e "    network_mode: host"
    echo -e "    image: ${LC_WORKER_IMAGE_NAME}:latest"
    echo -e "    container_name: $worker_service_name"
    echo -e "    user: \"www-data:www-data\""
    echo -e "    command: ${worker_celery_path} --app=${worker_service_variant}.celery:APP worker --loglevel=info --queues=edx.${worker_service_variant}.core.${worker_queue} --hostname=edx.${worker_service_variant}.core.${worker_queue}.%%h --concurrency=${worker_concurrency} -O ${prefetch_optimization}"
    echo -e "    volumes:"
    for volume_map in ${worker_service_volume_mappings[@]} ; do
      echo -e "      - ${volume_map}"
    done
      echo -e "    environment:"
      echo -e "      - SERVICE_VARIANT=${worker_service_variant}"
      echo -e "      - DJANGO_SETTINGS_MODULE=${worker_service_variant}.envs.docker-production"
      echo -e "      - EDX_PLATFORM_SETTINGS=docker-production"
      echo -e "      - EDX_REST_API_CLIENT_NAME=edx.${worker_service_variant}.core.${worker_queue}"
    for env_map in ${worker_service_env_mappings[@]} ; do
      echo -e "      - ${env_map}"
    done
  done
)
EOF
}

install_pre_reqs

# checkout git repo
if [ ! -d "/edx/app/${LC_WORKER_OF}" ]; then
  mkdir /edx/app/${LC_WORKER_OF}
fi

if [ ! -d "/edx/app/${LC_WORKER_OF}/${LC_WORKER_SERVICE_REPO}" ]; then
  git clone https://github.com/edx/${LC_WORKER_SERVICE_REPO}.git /edx/app/${LC_WORKER_OF}/${LC_WORKER_SERVICE_REPO}
  cd /edx/app/${LC_WORKER_OF}/${LC_WORKER_SERVICE_REPO} && git checkout ${LC_WORKER_SERVICE_REPO_VERSION}
fi

# Check if docker image already exists. If it doesn't, build it.
if ! $(docker image inspect ${LC_WORKER_IMAGE_NAME}:latest >/dev/null 2>&1 && echo true || echo false) ; then
  cd /edx/app/${LC_WORKER_OF}/${LC_WORKER_SERVICE_REPO}
  time DOCKER_BUILDKIT=1 docker build . -t ${LC_WORKER_IMAGE_NAME}:latest --target base
fi

# Render a docker-compose file for workers
render_docker_compose "/home/$LC_SANDBOX_USER/docker-compose-${LC_WORKER_OF}-workers.yaml"

# Run the docker-compose file
docker-compose -f "/home/$LC_SANDBOX_USER/docker-compose-${LC_WORKER_OF}-workers.yaml" up -d
