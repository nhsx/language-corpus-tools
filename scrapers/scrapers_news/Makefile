.PHONY: image push

all: image push

image:
	docker build -t scrapy ../scrapy
	docker build -t scrapers_news -t ${DOCKER_REGISTRY_PREFIX}scrapers_news .

push:
	docker push ${DOCKER_REGISTRY_PREFIX}scrapers_news:latest
