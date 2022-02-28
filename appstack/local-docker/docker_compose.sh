#!/bin/sh

set -e

. ./env-local

CFG_MEDCAT=""
if [ $ENABLE_MEDCAT_TRAINER = "True" ]; then
    CFG_MEDCAT=" -f ../docker-compose-medcat.yml"
fi


docker-compose -p $PROJECT_ID -f ../docker-compose.yml -f ../docker-compose-local.yml $CFG_MEDCAT "$@"
