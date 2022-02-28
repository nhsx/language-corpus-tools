#!/bin/sh

set -e

. ./env-local

#make -C ../services/nginx image
make -C ../services/caddy image
make -C ../services/db_init image
make -C ../services/brat image

if [ $ENABLE_MEDCAT_TRAINER = "True" ]; then
    make -C ../services/medcat image
fi
