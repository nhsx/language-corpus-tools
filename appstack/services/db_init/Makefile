.PHONY: image push

all: image push

image:
	docker build -t db_init -t ${DOCKER_REGISTRY_PREFIX}db_init .

push:
	docker push ${DOCKER_REGISTRY_PREFIX}db_init:latest
