#!./run_python.sh

# This script starts previously stopped docker-compose services by setting the desired number of running tasks to 1.

import os
import boto3

cluster = os.environ['DOCKER_CLUSTER']

ecs = boto3.client('ecs')

resp = ecs.list_services(cluster=cluster)

for service in resp['serviceArns']:
  ecs.update_service(cluster=cluster, service=service, desiredCount=1)
