.PHONY: image push

all: image push

image:
	docker build -t proxy_nginx -t ${DOCKER_REGISTRY_PREFIX}proxy_nginx .

push:
	docker push ${DOCKER_REGISTRY_PREFIX}proxy_nginx:latest
