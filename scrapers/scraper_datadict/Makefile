.PHONY: image push

all: image push

image:
	docker build -t scrapy ../scrapy
	docker build -t scraper_datadict -t ${DOCKER_REGISTRY_PREFIX}scraper_datadict .

push:
	docker push ${DOCKER_REGISTRY_PREFIX}scraper_datadict:latest
