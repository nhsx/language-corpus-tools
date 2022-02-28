#!/bin/sh

set -e

. ./env-local

docker context use default

make -C ../../scrapers/scraper_conditions image
make -C ../../scrapers/scraper_datadict image
make -C ../../scrapers/scrapers_news image
