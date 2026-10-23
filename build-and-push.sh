#!/usr/bin/env bash
# Build the Xyberah image (linux/amd64) and push it to your registry.
# Usage: ./build-and-push.sh <registry/namespace>   e.g. ./build-and-push.sh registry.example.com/security
set -euo pipefail
REPO="${1:?usage: $0 <registry/namespace>}"
VERSION="${PROMPTFOO_VERSION:-0.124.1}"
IMAGE="${REPO%/}/xyberah"

docker buildx build \
  --platform linux/amd64 \
  --build-arg PROMPTFOO_VERSION="$VERSION" \
  -t "$IMAGE:$VERSION" -t "$IMAGE:latest" \
  --push .

echo "Pushed $IMAGE:$VERSION and $IMAGE:latest"
