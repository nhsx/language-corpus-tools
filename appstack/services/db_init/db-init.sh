#!/bin/sh

for i in $(seq 0 10); do
    PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -p $PG_PORT --user postgres -e <<EOF

CREATE USER $SCRAPY_DB_USER PASSWORD '$SCRAPY_DB_PASSWORD';
CREATE DATABASE $SCRAPY_DB_NAME;

CREATE USER $DOCCANO_DB_USER PASSWORD '$DOCCANO_DB_PASSWORD';
CREATE DATABASE $DOCCANO_DB_NAME;

CREATE USER $MEDCAT_DB_USER PASSWORD '$MEDCAT_DB_PASSWORD';
CREATE DATABASE $MEDCAT_DB_NAME;

CREATE USER $DATADICT_DB_USER PASSWORD '$DATADICT_DB_PASSWORD';
CREATE DATABASE $DATADICT_DB_NAME;
EOF
    if [ $? -eq 0 ]; then
        break
    fi
    sleep 3
done

PGPASSWORD=$DATADICT_DB_PASSWORD psql -h $PG_HOST -p $PG_PORT  --user $DATADICT_DB_USER -f scripts/datadict.sql $DATADICT_DB_NAME 
