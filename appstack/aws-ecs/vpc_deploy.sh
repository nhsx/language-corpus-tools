#!/bin/sh

. ./env

if [ -z "$DOCCANO_PROJECT_ID_COND" ]; then
    export DOCCANO_PROJECT_ID_COND=""
fi

if [ -z "$DOCCANO_PROJECT_ID_NEWS" ]; then
    export DOCCANO_PROJECT_ID_NEWS=""
fi

if [ -z "$MEDCAT_DATASET_ID_COND" ]; then
    export MEDCAT_DATASET_ID_COND=""
fi

if [ -z "$MEDCAT_DATASET_ID_NEWS" ]; then
    export MEDCAT_DATASET_ID_NEWS=""
fi

./vpc_deploy.py
