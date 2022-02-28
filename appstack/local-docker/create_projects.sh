#!/bin/sh

set -e

. ./env-local

if [ -z "$DOCCANO_PROJECT_ID_COND" ]; then
    ../scripts/create_projects.py >> ./env
fi
