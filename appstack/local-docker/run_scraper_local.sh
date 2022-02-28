#!/bin/bash

# This script runs a single scraper on the local host (not in Docker). This could be useful for running quick tests when developing scrapers.

set -ex

VENV=$HOME/corpus_scrapers_venv

if [ ! -d $VENV ]; then
    echo "Python virtual environment is missing. Please run ./setup_run_scraper_local.sh"
    exit 1
fi

export PATH=$VENV/bin:$PATH

SCRAPER=$1
DIR="../../scrapers/$SCRAPER"
if [ ! -d "$DIR" ]; then
    echo "Scraper folder '$DIR' does not exist"
    exit 1
fi

# https://stackoverflow.com/questions/31396985/why-is-mktemp-on-os-x-broken-with-a-command-that-worked-on-linux
TMPDIR=`mktemp -d "${TMPDIR:-/tmp}/run_scraper_XXXXXX"`
trap "rm -rf $TMPDIR" EXIT

cp -a ../../scrapers/scrapy $TMPDIR/
cp -a $DIR/*.py $TMPDIR/scrapy/corpus/spiders

. ./env-local
export DOCCANO_DB_HOST=localhost
export SCRAPY_DB_HOST=localhost
export DATADICT_DB_HOST=localhost
export MEDCAT_API_URL=http://localhost:8080
export DOCCANO_API_URL=http://localhost:8081
export SCRAPY_HTTPCACHE_ENABLED=False

cd $TMPDIR/scrapy
./run.py
