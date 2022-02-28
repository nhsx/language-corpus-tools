#!/bin/sh

# Note that this requires public access to the RDS instance and an access from the current IP allowed.

. ./env-ecs

PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST --user postgres "$@"
