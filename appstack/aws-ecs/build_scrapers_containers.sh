#!/bin/sh

set -e

. ./env-ecs

docker context use default
./ecr_login.sh

make -C ../../scrapers/scraper_conditions
make -C ../../scrapers/scraper_datadict
make -C ../../scrapers/scrapers_news
