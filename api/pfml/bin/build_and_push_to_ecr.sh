#!/usr/bin/env bash
#
# Build and push the deployment container to AWS Elastic Container Registry (ECR).
#

set -e
export DOCKER_CONTENT_TRUST=1

DOCKER_REGISTRY=302282571580.dkr.ecr.us-east-1.amazonaws.com
DOCKER_REPO=pfml-api

# Generate a unique tag based solely on the git hash.
# This will be the identifier used for deployment via terraform.
HASH=$(git rev-parse HEAD)

# Generate an informational tag so we can see where every image comes from.
DATE=$(date -u '+%Y%m%d.%H%M%S')
INFO_TAG=$DATE.$USER

docker build --tag="$DOCKER_REPO:latest" \
             --tag="$DOCKER_REPO:$INFO_TAG" \
             --tag="$DOCKER_REPO:$HASH" \
             --tag="$DOCKER_REGISTRY/$DOCKER_REPO:$INFO_TAG" \
             --tag="$DOCKER_REGISTRY/$DOCKER_REPO:$HASH" \
             --stream \
             .

#
# Authenticate to the container registry.
#
echo "Authenticating to registry ..."
LOGIN=$(aws ecr get-login --no-include-email --region us-east-1)
$LOGIN
echo "OK"
echo

#
# Push latest images to the registry.
#
echo "Pushing tags to ECR ..."
docker push --disable-content-trust=true "$DOCKER_REGISTRY/$DOCKER_REPO:$HASH"
docker push --disable-content-trust=true "$DOCKER_REGISTRY/$DOCKER_REPO:$INFO_TAG"
echo "OK"
echo
