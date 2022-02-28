#!/bin/sh

set -e

. ./env-ecs

docker context use default
./ecr_login.sh

make -C ../services/db_init

aws ecs run-task --capacity-provider-strategy capacityProvider=FARGATE --cluster ${PROJECT_ID}-scrapers --count 1 --enable-ecs-managed-tags --task-definition arn:aws:ecs:$AWS_REGION:$AWS_ACCOUNT_ID:task-definition/$PROJECT_ID-db_init --network-configuration awsvpcConfiguration={subnets=[$AWS_SUBNETS],securityGroups=[$AWS_SG],assignPublicIp=ENABLED} > /dev/null
