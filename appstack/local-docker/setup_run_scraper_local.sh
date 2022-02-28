#!/bin/sh

# This script installs the necessary python dependencies to be able to use the run_scraper_local.sh
# Requires python3 and pip.

PYTHON=`which python3`
if [ -z "$PYTHON" ]; then
    PYTHON=`which python`
fi

if [ -z "$PYTHON" ]; then
    echo "python 3 is missing"
fi

VER=`$PYTHON -c 'import sys; version=sys.version_info[:3]; print("{0}{1}".format(*version))'`

if [ $VER -lt 37 ]; then
    echo "Invalid python version ($VER). Need at least 3.7"
    exit 1
fi

PIP=`which pip3`
if [ -z "$PIP" ]; then
    PIP=`which pip`
fi

if [ -z "$PIP" ]; then
    echo "Missing pip for python3"
    exit 1
fi

VENV=$HOME/corpus_scrapers_venv

$PYTHON -m venv $VENV

PIP=$VENV/bin/pip

$PIP install --upgrade pip

$PIP install scrapy psycopg2-binary txpostgres python-dateutil treq atoma
