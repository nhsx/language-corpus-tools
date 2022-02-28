#!/bin/bash

set -e

. ./env-ecs

CFG_MEDCAT=""
if [ $ENABLE_MEDCAT_TRAINER = "True" ]; then
    CFG_MEDCAT=" -f ../docker-compose-medcat.yml -f ../docker-compose-medcat-ecs.yml"
fi

./ecr_login.sh

docker context use NHS
docker compose -p ${DOCKER_CLUSTER} -f ../docker-compose.yml -f ../docker-compose-ecs.yml $CFG_MEDCAT "$@"
