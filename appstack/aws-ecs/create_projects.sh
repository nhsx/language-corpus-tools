#!/bin/sh

set -e

. ./env-ecs

if [ -z "$DOCCANO_PROJECT_ID_COND" ]; then
    ../scripts/create_projects.py >> ./env
    ./vpc_deploy.sh
fi
