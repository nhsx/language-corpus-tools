.PHONY: image push

all: image push

image:
	docker build -t scrapy ../scrapy
	docker build -t scraper_conditions -t ${DOCKER_REGISTRY_PREFIX}scraper_conditions .

push:
	docker push ${DOCKER_REGISTRY_PREFIX}scraper_conditions:latest
