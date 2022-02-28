.PHONY: image push

all: update image push

image:
	docker build -t brat -t ${DOCKER_REGISTRY_PREFIX}brat .

push: image
	docker push ${DOCKER_REGISTRY_PREFIX}brat:latest
