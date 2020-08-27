#!/usr/bin/env bash

# unofficial bash strict mode
set -euxo pipefail

openedx_release=${OPENEDX_RELEASE:-master}
tag_name=${TAG_NAME:-latest}
image_tag=edxops/${APP_NAME}:${tag_name}

# build the Dockerfile of the IDA defined by APP_NAME and tag it with its name; don't use cache
docker build -f docker/build/${APP_NAME}/Dockerfile --build-arg BASE_IMAGE_TAG=${tag_name} --build-arg OPENEDX_RELEASE=${openedx_release} -t ${image_tag} --no-cache .

# push built image to DockerHub
echo docker push ${image_tag}
