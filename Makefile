DOCKER_REGISTRY ?= 
DOCKER_PREFIX ?= catalogicsoftware/

DOCKER_DIR_BASE = images

DOCKER_KUBEDRUTIL_IMAGE_TAG ?= latest
DOCKER_KUBEDRUTIL_IMAGE_NAME_SHORT = kubedrutil
DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG = ${DOCKER_REGISTRY}${DOCKER_KUBEDRUTIL_IMAGE_NAME_SHORT}
DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG_DOCKERHUB = ${DOCKER_PREFIX}${DOCKER_KUBEDRUTIL_IMAGE_NAME_SHORT}

build: docker_build

docker_build:
	cd ${DOCKER_DIR_BASE} && \
		docker build \
			--cache-from ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:latest \
			--tag ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} \
			.

docker_push_latest:
	docker pull ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} || true
	docker tag ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} \
		${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:latest
	docker push ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG}
	docker push ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:latest

docker_push_tags:
ifndef CI_COMMIT_TAG
	$(error The git tag, CI_COMMIT_TAG, is MISSING. This is required for pushing tagged images. Aborting.)
endif
	docker pull ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} || true
	docker tag ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} \
		${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG_DOCKERHUB}:${CI_COMMIT_TAG} 
	docker tag ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} \
		${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG_DOCKERHUB}:latest
	docker push ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG_DOCKERHUB}:${CI_COMMIT_TAG}
	docker push ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG_DOCKERHUB}:latest
