#!/usr/bin/python3

import os
import string
import time

import jinja2

import boto3
import botocore.exceptions

stack_name = os.environ["PROJECT_ID"]

if os.environ.get("EXT_DOMAIN") is None:
    raise Exception("EXT_DOMAIN must be set in the env file")

scraper_tasks = [
    {"name": "scraper_conditions"},
    {"name": "scraper_datadict"},
    {"name": "scrapers_news"},
]

all_env = [
    {
        "name": "SCRAPY_DB_NAME",
        "type": "String",
    },
    {
        "name": "SCRAPY_DB_USER",
        "type": "String",
    },
    {
        "name": "SCRAPY_DB_PASSWORD",
        "type": "String",
        "password": True,
    },
    {
        "name": "DOCCANO_DB_NAME",
        "type": "String",
    },
    {
        "name": "DOCCANO_DB_USER",
        "type": "String",
    },
    {
        "name": "DOCCANO_DB_PASSWORD",
        "type": "String",
        "password": True,
    },
    {
        "name": "MEDCAT_DB_NAME",
        "type": "String",
    },
    {
        "name": "MEDCAT_DB_USER",
        "type": "String",
    },
    {
        "name": "MEDCAT_DB_PASSWORD",
        "type": "String",
        "password": True,
    },
    {
        "name": "DATADICT_DB_NAME",
        "type": "String",
    },
    {
        "name": "DATADICT_DB_USER",
        "type": "String",
    },
    {
        "name": "DATADICT_DB_PASSWORD",
        "type": "String",
        "password": True,
    },
    {
        "name": "MEDCAT_API_URL",
        "type": "String",
    },
    {
        "name": "MEDCAT_USERNAME",
        "type": "String",
    },
    {
        "name": "MEDCAT_PASSWORD",
        "type": "String",
        "password": True,
    },
    {
        "name": "DOCCANO_API_URL",
        "type": "String",
    },
    {
        "name": "DOCCANO_USERNAME",
        "type": "String",
    },
    {
        "name": "DOCCANO_PASSWORD",
        "type": "String",
        "password": True,
    },
    {
        "name": "MEDCAT_DATASET_ID_COND",
        "type": "String",
    },
    {
        "name": "DOCCANO_PROJECT_ID_COND",
        "type": "String",
    },
    {
        "name": "MEDCAT_DATASET_ID_NEWS",
        "type": "String",
    },
    {
        "name": "DOCCANO_PROJECT_ID_NEWS",
        "type": "String",
    },
    {
        "name": "NHS_API_KEY",
        "type": "String",
        "password": True,
    },
    {
        "name": "SCRAPY_HTTPCACHE_ENABLED",
        "type": "String",
    },
    {
        "name": "ENABLE_MEDCAT_TRAINER",
        "type": "String",
    },
]


def get_output(outputs, key):
    return next(obj["OutputValue"] for obj in outputs if obj["OutputKey"] == key)


def to_camel_case(s):
    s = s.lower()
    return string.capwords(s, sep="_").replace("_", "") if s else s


for env in all_env:
    env["camel_name"] = to_camel_case(env["name"])

for task in scraper_tasks:
    task["camel_name"] = to_camel_case(task["name"])

params = [
    {
        "ParameterKey": "EnvironmentName",
        "ParameterValue": stack_name,
    },
]

create_postgres = os.environ.get("CREATE_POSTGRES", "True") == "True"
if not create_postgres:
    pg_host = os.environ.get("PG_HOST")
    pg_port = os.environ.get("PG_PORT", "5432")
    params.append({"ParameterKey": "PgHost", "ParameterValue": pg_host})
    params.append({"ParameterKey": "PgPort", "ParameterValue": pg_port})

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
templ = templateEnv.get_template("vpc.yml.jinja2")
template = templ.render(
    {
        "all_env": all_env,
        "scraper_tasks": scraper_tasks,
        "create_postgres": create_postgres,
    }
)


for env in all_env:
    params.append(
        {"ParameterKey": env["camel_name"], "ParameterValue": os.environ[env["name"]]}
    )

cloudformation = boto3.resource("cloudformation")
client = boto3.client("cloudformation")

stack = cloudformation.Stack(os.environ["PROJECT_ID"])

try:
    if create_postgres:
        params.append(
            {
                "ParameterKey": "PostgresPassword",
                "UsePreviousValue": True,
            }
        )
    stack.update(
        TemplateBody=template,
        Parameters=params,
        Capabilities=["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"],
    )
except botocore.exceptions.ClientError as e:
    code = e.response["Error"]["Code"]
    message = e.response["Error"]["Message"]
    if code == "ValidationError" and message.endswith(" does not exist"):
        if create_postgres:
            params.append(
                {
                    "ParameterKey": "PostgresPassword",
                    "ParameterValue": os.environ["PG_PASSWORD"],
                }
            )

        cloudformation.create_stack(
            StackName=stack_name,
            TemplateBody=template,
            Parameters=params,
            Capabilities=["CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"],
        )
        waiter = client.get_waiter("stack_exists")
        print("Waiting for the stack...")
        waiter.wait(StackName=stack_name)
        print("Stack creation initiated. This may take up to 10 min...")

    elif code == "ValidationError" and message.endswith(
        "No updates are to be performed."
    ):
        print("Stack is up-to-date")
        pass
    else:
        raise e

cur_state = None
while True:
    res = client.describe_stacks(StackName=stack_name)["Stacks"][0]
    new_state = res["StackStatus"]
    if new_state != cur_state:
        print(f"New state: {new_state}")
        cur_state = new_state
        if (
            new_state == "CREATE_COMPLETE"
            or new_state == "UPDATE_COMPLETE"
            or new_state == "UPDATE_ROLLBACK_COMPLETE"
            or new_state == "ROLLBACK_FAILED"
            or new_state == "ROLLBACK_COMPLETE"
        ):
            break
    time.sleep(30)

stack.reload()
outputs = stack.outputs
if create_postgres:
    pg_instance_id = get_output(outputs, "PostgresDB")

    rds = boto3.client("rds")
    resp = rds.describe_db_instances(
        DBInstanceIdentifier=pg_instance_id,
    )

out = open("env-ecs", "w")
out.write(
    "# This file was automaticaly generated by vpc-deploy.py. All changes will be lost. Do not edit.\n\n"
)
if create_postgres:
    endpoint = resp["DBInstances"][0]["Endpoint"]
    out.write(f"export PG_HOST={endpoint['Address']}\n")
    out.write(f"export PG_PORT={endpoint['Port']}\n")

vpc_id = get_output(outputs, "VPC")
out.write(f"export VPC={vpc_id}\n")

sg_id = get_output(outputs, "DefaultSecurityGroup")
out.write(f"export AWS_SG={sg_id}\n")

subnets = get_output(outputs, "PublicSubnets")
out.write(f"export AWS_SUBNETS={subnets}\n")

out.write(f"export AWS_REGION={client.meta.region_name}\n")

account_id = boto3.client("sts").get_caller_identity().get("Account")
out.write(f"export AWS_ACCOUNT_ID={account_id}\n")

out.write(
    f"export DOCKER_REGISTRY={account_id}.dkr.ecr.{client.meta.region_name}.amazonaws.com\n"
)
out.write(". ./env\n")
out.write("export DOCKER_REGISTRY_PREFIX=$DOCKER_REGISTRY/$PROJECT_ID/\n")
out.write("export DOCCANO_ACCESS_URL=https://doccano.$EXT_DOMAIN\n")
out.write("export MEDCAT_ACCESS_URL=https://medcattrainer.$EXT_DOMAIN\n")

out.write("export DOCCANO_CADDY_HOSTS=http://doccano.$EXT_DOMAIN\n")
out.write("export MEDCAT_CADDY_HOSTS=http://medcattrainer.$EXT_DOMAIN\n")
out.write("export SQLPAD_CADDY_HOSTS=http://sqlpad.$EXT_DOMAIN\n")
out.write("export BRAT_CADDY_HOSTS=http://brat.$EXT_DOMAIN\n")

out.close()
