#!/usr/bin/env bash
set -euo pipefail

CARLA_PYTHON_VERSION="${CARLA_PYTHON_VERSION:-0.9.16}"
INSTALL_TORCH="${DRIVERX_FAIL2DRIVE_INSTALL_TORCH:-0}"
IMAGE="${FAIL2DRIVE_CLIENT_DOCKER_IMAGE:-driverx-fail2drive-client:${CARLA_PYTHON_VERSION}}"

docker build \
  --platform linux/amd64 \
  --build-arg "CARLA_PYTHON_VERSION=${CARLA_PYTHON_VERSION}" \
  --build-arg "INSTALL_TORCH=${INSTALL_TORCH}" \
  -f docker/fail2drive-client.Dockerfile \
  -t "${IMAGE}" \
  .
