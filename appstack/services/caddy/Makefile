.PHONY: image push

all: image push

image:
	docker build -t proxy_caddy -t ${DOCKER_REGISTRY_PREFIX}proxy_caddy .

push:
	docker push ${DOCKER_REGISTRY_PREFIX}proxy_caddy:latest
