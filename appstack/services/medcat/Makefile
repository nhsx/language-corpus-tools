.PHONY: image push

all: update image push

MedCATtrainer:
	git clone https://github.com/CogStack/MedCATtrainer.git

update: MedCATtrainer
	cd MedCATtrainer; git pull

image: MedCATtrainer
	docker build -t medcattrainer -t ${DOCKER_REGISTRY_PREFIX}medcattrainer .

push: image
	docker push ${DOCKER_REGISTRY_PREFIX}medcattrainer:latest
