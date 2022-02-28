#!/bin/sh

set -e

. ./env-ecs

docker context use default
./ecr_login.sh

#make -C ../services/nginx
make -C ../services/caddy

if [ $ENABLE_MEDCAT_TRAINER = "True" ]; then
    make -C ../services/medcat
fi
