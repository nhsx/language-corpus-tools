#!/bin/sh

set -e

scraper=$1
if [ -z "$scraper" ]; then
    echo "Usage: $0 <scraper>"
    exit 1
fi

. ./env-local

make -C ../../scrapers/$scraper image

./docker_compose.sh run $scraper ./run.py
