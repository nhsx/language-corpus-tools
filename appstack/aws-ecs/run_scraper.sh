#!/bin/sh

# This script launches a scraper in AWS Fargate using FARGATE_SPOT capacity provider. See https://aws.amazon.com/blogs/aws/aws-fargate-spot-now-generally-available/
# for more details.
# If you don't want to use regular Fargate instead, specify "nospot" as the second parameter.

set -e

scraper=$1
if [ -z "$scraper" ]; then
    echo "Usage: $0 <scraper> [nospot]"
    echo "<scraper> is the name of the folder under ../../scrapers"
    exit 1
fi

if [ $2 = "nospot" ]; then
    PROVIDER=FARGATE
else
    PROVIDER=FARGATE_SPOT
fi

. ./env-ecs

docker context use default
./ecr_login.sh

make -C ../../scrapers/$scraper

aws ecs run-task --capacity-provider-strategy capacityProvider=$PROVIDER --cluster ${PROJECT_ID}-scrapers --count 1 --enable-ecs-managed-tags \
 --task-definition arn:aws:ecs:$AWS_REGION:$AWS_ACCOUNT_ID:task-definition/$PROJECT_ID-$scraper \
 --network-configuration awsvpcConfiguration={subnets=[$AWS_SUBNETS],securityGroups=[$AWS_SG],assignPublicIp=ENABLED} > /dev/null
