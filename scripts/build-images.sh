#!/bin/bash
set -Eeuo pipefail

if [[ -z "${DEPTHAI_BRANCH}" ]]; then
  DEPTHAI_BRANCH="main"
fi
ALPINE_TAG="localhost:5000/luxonis/robothub-base-app:alpine-depthai-${DEPTHAI_BRANCH}"
UBUNTU_TAG="localhost:5000/luxonis/robothub-base-app:ubuntu-depthai-${DEPTHAI_BRANCH}"

echo "Building alpine..."
# Alpine
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder localbuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  -t $ALPINE_TAG \
  --push \
  --file ./robothub_sdk/docker/alpine/Dockerfile \
  ./robothub_sdk

echo "Building ubuntu..."
#Ubuntu
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder localbuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  -t $UBUNTU_TAG \
  --push \
  --file ./robothub_sdk/docker/ubuntu/Dockerfile \
  ./robothub_sdk