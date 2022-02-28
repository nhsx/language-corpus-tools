#!/bin/bash

if [ -z "$DOCKER_REGISTRY" ]; then
  . ./env-ecs
fi

aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin $DOCKER_REGISTRY
