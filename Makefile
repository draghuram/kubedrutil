DOCKER_REGISTRY ?= docker-registry.devad.catalogic.us:5000

DOCKER_DIR_BASE = images

DOCKER_KUBEDRUTIL_IMAGE_TAG ?= latest
DOCKER_KUBEDRUTIL_IMAGE_NAME_SHORT = kubedrutil
DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG = ${DOCKER_REGISTRY}/${DOCKER_KUBEDRUTIL_IMAGE_NAME_SHORT}

# make >= 3.8.2
# Add special target to have make invoke one instance of shell, regardless of lines
.ONESHELL:

build: docker_build

docker_build:
	cd ${DOCKER_DIR_BASE}
	docker pull ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:latest || true
	docker build \
		--cache-from ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:latest \
		--tag ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} \
		.

docker_push_latest:
	docker pull ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} || true
	docker tag ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:latest
	docker push ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:latest

docker_push_tags:
ifndef CI_COMMIT_TAG
	$(error The git tag, CI_COMMIT_TAG, is MISSING. This is required for pushing tagged images. Aborting.)
endif
	docker pull ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} || true
	docker tag ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${DOCKER_KUBEDRUTIL_IMAGE_TAG} ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${CI_COMMIT_TAG}
	docker push ${DOCKER_KUBEDRUTIL_IMAGE_NAME_LONG}:${CI_COMMIT_TAG}