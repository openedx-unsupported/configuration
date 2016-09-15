DEFAULT_GOAL: help

.PHONY: deploy-testdrive

EDXCONFIGS_BRANCH=master

## Deploy testdrive
deploy-testdrive:
	$(eval EDXCONFIGS_REPO_LOCAL_BRANCH := $(shell cd ../../edx-configs && git symbolic-ref --short -q HEAD))
	@appsembler/scripts/check_git_is_up2date.sh
	@ansible-playbook --inventory-file=../../edx-configs/appsembler/testdrive/hosts/inventory testdrive.yml --ask-vault-pass

## Show help screen.
help:
	@echo "Please use \`make <target>' where <target> is one of\n\n"
	@awk '/^[a-zA-Z\-\_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "%-30s %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

