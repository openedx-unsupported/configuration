.PHONY: help \
	build clean clean-all publish \
	_validate-repo _validate-registry _validate-version _login \
	_remove-dangling-images

# Target Docker Registry
REGISTRY_HOST?=
REGISTRY_USERNAME?=
REGISTRY_PASSWORD?=

# Service component
REPO:=bigdatauniversity
IMAGE:=portal.forum
VERSION?=$(shell cat VERSION)

# Terminal coloring
RED:=$$(which tput > /dev/null && tput -T xterm setaf 1)
GREEN:=$$(which tput > /dev/null && tput -T xterm setaf 2)
CLEAR:=$$(which tput > /dev/null && tput -T xterm sgr 0)
BOLD:=$$(which tput > /dev/null && tput -T xterm bold)

## Global commands
help:
	@echo "$(BOLD)Global commands:$(CLEAR)"
	@echo "  $(BOLD)$(GREEN)help$(CLEAR)    Display this menu."
	@echo
	@echo "$(BOLD)Workstation commands:$(CLEAR)"
	@echo "  $(BOLD)$(GREEN)build$(CLEAR)        Build component image."
	@echo "  $(BOLD)$(GREEN)clean$(CLEAR)        Delete local component image (VERSION=$(VERSION))."
	@echo "  $(BOLD)$(GREEN)clean-all$(CLEAR)    Delete local component images (all versions)."
	@echo
	@echo "  $(BOLD)$(GREEN)publish$(CLEAR)    Push component image to registry."
	@echo

## Workstation commands
build:
	@echo "$(BOLD)$(GREEN)Building $(IMAGE):$(VERSION) image...$(CLEAR)"
	@docker build -f Dockerfile.bdu --rm -t $(IMAGE):$(VERSION) ../../../
	@make _remove-dangling-images
	@echo "$(BOLD)$(GREEN)Image $(IMAGE):$(VERSION) was built.$(CLEAR)"

clean:
	@echo "$(BOLD)$(GREEN)Removing $(IMAGE):$(VERSION) image...$(CLEAR)"
	@docker rmi $(IMAGE):$(VERSION)
	@echo "$(BOLD)$(GREEN)Image $(IMAGE):$(VERSION) removed.$(CLEAR)"
	@make _remove-dangling-images

clean-all:
	@\
		IMAGES=$$(docker images --format="{{.Repository}}:{{.Tag}}" | grep $(IMAGE)); \
		if [ -z "$$IMAGES" ]; then \
			echo "No images found, skipping." && exit 0; \
		fi && \
		echo && \
		echo "$(BOLD)$(RED)WARNING$(CLEAR): $(BOLD)This will remove all images below:$(CLEAR)" && \
		echo && \
		echo "$$IMAGES" && \
		echo && \
		printf "Would you like to proceed (yes/no)? " && \
		read ANSWER && \
		if ! echo "$$ANSWER" | grep -q "^yes"; then \
			echo "Aborting." && exit 0; \
		fi && \
		echo "$(BOLD)$(GREEN)Removing all versions of all $(IMAGE) images...$(CLEAR)" && \
		docker rmi $$IMAGES && \
		make _remove-dangling-images

publish: _validate-repo _login
	@echo "$(BOLD)$(GREEN)Publishing $(IMAGE):$(VERSION) to $(REGISTRY_HOST)/$(REPO)...$(CLEAR)"
	@\
		if [ "$REGISTRY_HOST" = "index.docker.io" ]; then \
			REMOTE_IMAGE="$(REPO)/$(IMAGE):$(VERSION)"; \
		else \
			REMOTE_IMAGE="$(REGISTRY_HOST)/$(REPO)/$(IMAGE):$(VERSION)"; \
		fi && \
		docker tag $(IMAGE):$(VERSION) $$REMOTE_IMAGE && \
		docker push $$REMOTE_IMAGE && \
		echo "$(BOLD)$(GREEN)Image $$REMOTE_IMAGE published.$(CLEAR)"

## Private
_validate-repo:
ifndef REPO
	$(error REPO is undefined)
endif

_validate-registry:
ifndef REGISTRY_USERNAME
	$(error REGISTRY_USERNAME is undefined)
endif
ifndef REGISTRY_PASSWORD
	$(error REGISTRY_PASSWORD is undefined)
endif
ifndef REGISTRY_HOST
	$(error REGISTRY_HOST is undefined)
endif

_validate-version: _validate-registry _validate-repo
ifndef VERSION
	$(error VERSION is undefined)
endif
ifeq ($(shell which docker && docker images $(IMAGE) | grep $(VERSION) > /dev/null && echo 0 || echo 1), 1)
	$(error Image $(IMAGE):$(VERSION) not found)
endif
ifeq ($(filter $(VERSION), latest),)
	@\
		if [ "$(REGISTRY_HOST)" = "index.docker.io" ]; then \
			CHECK_URL="https://$(REGISTRY_USERNAME):$(REGISTRY_PASSWORD)@index.docker.io/v1/repositories/$(REPO)/$(IMAGE)/tags/$(VERSION)"; \
		else \
			CHECK_URL="https://$(REGISTRY_USERNAME):$(REGISTRY_PASSWORD)@$(REGISTRY_HOST)/v2/$(REPO)/$(IMAGE)/manifests/$(VERSION)"; \
		fi && \
		CODE=$$(curl -s -H "Accept: application/json" -w "%{http_code}" -o /dev/null $$CHECK_URL) && \
		if [ "$$CODE" = "200" ]; then \
			echo "Version '$(VERSION)' already exists ($(REGISTRY_HOST)/$(REPO)/$(IMAGE):$(VERSION))"; \
			echo "Aborting."; \
			exit 1; \
		fi
else
	@echo "Using 'latest' version, skipping registry verification."
endif
	@echo 'Working with version "$(VERSION)"...'

_login: _validate-registry
	@docker login -u "$(REGISTRY_USERNAME)" -p "$(REGISTRY_PASSWORD)" "$(REGISTRY_HOST)"

_remove-dangling-images:
	@echo "$(BOLD)$(GREEN)Cleaning up dangling images...$(CLEAR)"
	@-\
		IMAGES=$$(docker images --filter="dangling=true" --quiet) && \
		if [ -n "$$IMAGES" ]; then \
			docker rmi $$IMAGES; \
		else \
			echo "No dangling images found, skipping."; \
		fi
