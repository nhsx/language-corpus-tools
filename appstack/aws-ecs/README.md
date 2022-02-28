Overview
===

This directory contains configuration and scripts required to setup the application stack on Amazon Elastic Container Service from scratch.
The installation is using the [Docker Compose CLI](https://docs.docker.com/cloud/ecs-integration/) which allows to use (almost) standard docker-compose.yml.
It converts the docker-compose.yml file into a CloudFormation template that is subsequently created and updated automatically. The defined services
run on ECS [Fargate](https://aws.amazon.com/fargate).

A separate CloudFormation stack containing the necessary supporting infrastructure (VPC, networks, security group, task definitions and a
Postgres RDS instance) is set up.

The supporting infrastructure also contains task definitions to run the scrapers. These are not part of the docker-compose stack because they are not
really services in a sense that they do not need to run continuously. Instead they can be launched on demand using the `run-scraper*` scripts.

When adding services to docker-container-ecs.yml make sure that they do not expose ports 80 or 443. This is because the security group for the netowrk
is configured to allow connections to these ports from the Internet (this is required for the front-facing Nginx, however it's not possible to limit
this to only some of the hosts in the network).

Prerequisits
===

There must be a public DNS zone that will be used as the access point for the services. The administrator must have ability to add Resource Records to
this DNS zone.

All configuration tasks must be performed from a Linux machine that has the following:

 - Debian 10 or similar (it can be different but this guide assumes Debian 10).
 - [AWS CLI version 2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html)
 - The CLI must be [configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) to allow access to an AWS account
 - python 3.7 or higher (`apt-get install python3`)
 - make (`apt-get install make`)
 - [boto3](https://pypi.org/project/boto3/)
 - [Docker Engine](https://docs.docker.com/engine/install/)
 - [Docker Compose CLI](https://docs.docker.com/cloud/ecs-integration/#install-the-docker-compose-cli-on-linux). Version 1.0.9 was used, but it is recommended
that you try the latest available first. In case of any problems, download version 1.0.9 [here](https://github.com/docker/compose-cli/releases/tag/v1.0.9)

An SSL certificate must be created or imported into [Amazon Certificate Manager](https://aws.amazon.com/certificate-manager/). The certificate should
be a wildcard certificate for the chosen DNS zone. The ARN of this certificate is required during the installation.

Installation
===

 - Make sure that the current user can manage Docker:

```shell
sudo usermod -aG docker ${USER}
```

Then logout and login again.

 - Setup a docker compose context by running `docker context create ecs NHS`. Point it to the AWS account.

 - In the current folder, run `./generate_env.sh`. This will create a skeleton `env` file which contains the required environment variables most of which will
be pre-populated and passwords randomly generated.

 - Review the generated `env` file and fill in the required parameters.

 - Run `./vpc_deploy.sh`. This will create the supporting infrastructure stack (VPC, networks, security group and the PostgreSQL RDS instance). The process
can take up to 10 minutes. This script must be run if the `env` file is changed in order to apply the changes. It is safe to run the script at any time, it
will only apply changes (if any).

```console
admin@host:~/distr/appstack/aws-ecs$ ./vpc_deploy.sh
Waiting for the stack...
Stack creation initiated. This may take up to 10 min...
New state: CREATE_IN_PROGRESS
New state: CREATE_COMPLETE
```

 - Run `./run_db_init.sh`. This will start a task that will create the required databases and schemas in the newly created Postgres instance.

 - Use [AWS CloudWatch](https://aws.amazon.com/cloudwatch/) to review the logs from the task to make sure it ran ok.

 - Run `./build_service_containers.sh`. This will create the Docker images for the containers and push them to the Elastic Container Registry.

 - Deploy the docker-compose stack by running `./docker_compose_up.sh`. This might take a few minutes. Note that even after the script has finished it
still takes a couple of minutes for the services to start (especially MedCATTrainer).

 - As part of the stack an Elastic Load Balancer will be created which will serve as the HTTP/HTTPS entry point for the project. You need to point the
relevant DNS names to that load balancer. Run `aws elbv2 describe-load-balancers` to get the list of the balancers, pick the newly created one and set up
the following CNAMES in your DNS zone:

```
medcattrainer IN 60 CNAME {{ DNSName of the load balancer }}.
doccano IN 60 CNAME {{ DNSName of the load balancer }}.
sqlpad IN 60 CNAME {{ DNSName of the load balancer }}.
```

(don't forget the trailing dots)


 - At this point the services should become accessible at https://medcattrainer.<your DNS zone>/, https://doccano.<your DNS zone>/ and 
https://sqlpad.<your DNS zone>./ Make sure you can login to them. If not use the CloudWatch to check the logs.

 - Run `./create_projects.sh`. This will Create Doccano and MedCAT projects which will serve as the destination point for the imported documents. 

 - Run the scrapers (using `run_scraper.sh` script). This will populate the datasets. These scrapers could be run periodically to ingest any new or
updated document. It is possible to setup a [schedule](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/scheduled_tasks.html)

