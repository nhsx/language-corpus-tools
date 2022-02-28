#!/usr/bin/python3

import random
import string


def gen_password(length=20):
    return "".join(
        random.choice(string.ascii_letters + string.digits)
        for i in range(length)
    )


template = f"""
# This is the name of the main cluster. Must be unique within a AWS account. Must be lowercase.
export PROJECT_ID=""

# Public DNS domain name under which the project will be exposed on the Internet.
# When using local-docker deployment this can be unset. In this case the services will be exposed on separate ports (8080 onwards). See
# local-docker/README.md for details.
# When using aws-ecs deployment this must be set.
#export EXT_DOMAIN=""

# Password to access Doccano (as user admin)
export DOCCANO_PASSWORD=""

export MEDCAT_USERNAME=admin
export MEDCAT_PASSWORD=""

# Create (or import) an SSL certificate in AWS (see https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html for details)
# This should be a wildcard certificate for the chosen domain (which will be a part of the public URL, for instance *.c250.example.com"
# The certificate is installed by docker compose into a Load Balancer to create a public HTTPS endpoint.
# Only applicable for aws-ecs deployments.
export CERT_ARN=

export SQLPAD_ADMIN=admin
export SQLPAD_ADMIN_PASSWORD=""

# Needed for scraper_conditions
export NHS_API_KEY=""

# Uncomment and set this if you want to use an existing PostgreSQL instance. Note that the security group must be set up to allow access from this
# project's VPC.
#export CREATE_POSTGRES=False
#export PG_HOST=
#export PG_PORT=
## These are only needed to run the db-init task. The user must be able to create users and databases. If you want to create those yourself
## do not set these and use scripts from ../services/db-init as a guide.
#export PG_USER=
#export PG_PASSWORD=

# Change this to False to disable medcattrainer. The service won't be built or deployed, the scrapers won't attempt to send the data to medcattrainer.
# The database will stil be created in Postgres.
export ENABLE_MEDCAT_TRAINER=True

# Note, BRAT is only supported in local-docker mode. Setting these in aws-ecs mode has no effect.
# Directory to store BRAT documents. When set the scraper framework will populate the folder with the ingested documents.
export BRAT_DATA_PATH=$HOME/brat-data
# Used to provide HTTP authentication for BRAT as an additional security feature.
export BRAT_HTTP_USERNAME=brat
# Can be generated using `docker run -it caddy caddy hash-password -plaintext <password>`
export BRAT_HTTP_PASSWORD=

# You normally don't need to change the rest.

export DOCKER_CLUSTER=${{PROJECT_ID}}-docker
export LOCAL_DOMAIN=.${{DOCKER_CLUSTER}}.local

export DOCCANO_USERNAME=admin
export DOCCANO_API_URL=http://doccano:8000

export MEDCAT_API_URL=http://medcattrainer:8000

if [ "$CREATE_POSTGRES" != "False" ]; then
    export PG_PASSWORD="{gen_password()}"
fi

export SCRAPY_DB_HOST=$PG_HOST
export SCRAPY_DB_PORT=$PG_PORT
export SCRAPY_DB_NAME=scrapy
export SCRAPY_DB_USER=scrapy
export SCRAPY_DB_PASSWORD="{gen_password()}"

export DOCCANO_DB_HOST=$PG_HOST
export DOCCANO_DB_PORT=$PG_PORT
export DOCCANO_DB_NAME=doccano
export DOCCANO_DB_USER=doccano
export DOCCANO_DB_PASSWORD="{gen_password()}"

export MEDCAT_DB_HOST=$PG_HOST
export MEDCAT_DB_PORT=$PG_PORT
export MEDCAT_DB_NAME=medcat
export MEDCAT_DB_USER=medcat
export MEDCAT_DB_PASSWORD="{gen_password()}"
export MEDCAT_DATASET_ID=2

export DATADICT_DB_HOST=$PG_HOST
export DATADICT_DB_PORT=$PG_PORT
export DATADICT_DB_NAME=datadict
export DATADICT_DB_USER=datadict
export DATADICT_DB_PASSWORD="{gen_password()}"

export SCRAPY_HTTPCACHE_ENABLED=False

if [ -z "$PROJECT_ID" ]; then
    echo "Please set PROJECT_ID"
    exit 1
fi

if [ -z "$DOCCANO_PASSWORD" ]; then
    echo "Please set DOCCANO_PASSWORD"
    exit 1
fi

if [ -z "$MEDCAT_PASSWORD" ]; then
    echo "Please set MEDCAT_PASSWORD"
    exit 1
fi

if [ -z "$SQLPAD_ADMIN_PASSWORD" ]; then
    echo "Please set SQLPAD_ADMIN_PASSWORD"
    exit 1
fi

if [ -z "$NHS_API_KEY" ]; then
    echo "Please set NHS_API_KEY"
    exit 1
fi

"""

try:
    with open("env", "x") as fout:
        fout.write(template)
except FileExistsError:
    print("env already exists, not overwriting")
