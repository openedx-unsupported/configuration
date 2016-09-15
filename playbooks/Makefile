.PHONY = monitoring deploy-testdrive mysql-init-testdrive mongo-replicaset-testdrive

.DEFAULT_GOAL = help

EDXCONFIGS_BRANCH=master

## Install monitoring on customer cluster. Example: CUSTOMER=qa ENVIRONMENT=production TIER=basic PLATFORM=azure make monitoring
monitoring:
	@@if test -z "$$CUSTOMER"; then echo "ERROR: CUSTOMER is not defined."; exit 1; fi;
	@@if test -z "$$PLATFORM"; then echo "ERROR: PLATFORM is not defined."; exit 1; fi;
	@@if test -z "$$TIER"; then echo "ERROR: TIER is not defined."; exit 1; fi;
	@@if test -z "$$ENVIRONMENT"; then echo "ERROR: ENVIRONMENT is not defined."; exit 1; fi;
	@ansible-playbook -i inventory monitoring.yml --extra-vars "@../../edx-configs/$$CUSTOMER/$$ENVIRONMENT/server-vars.yml"

## Deploy testdrive
deploy-testdrive:
	$(eval EDXCONFIGS_REPO_LOCAL_BRANCH := $(shell cd ../../edx-configs && git symbolic-ref --short -q HEAD))
	@appsembler/scripts/check_git_is_up2date.sh
	@ansible-playbook --inventory-file=../../edx-configs/appsembler/testdrive/hosts/inventory testdrive.yml --ask-vault-pass

## Run mysql_init.yml playbook for testdrive
mysql-init-testdrive:
	$(eval EDXCONFIGS_REPO_LOCAL_BRANCH := $(shell cd ../../edx-configs && git symbolic-ref --short -q HEAD))
	@appsembler/scripts/check_git_is_up2date.sh
	@ansible-playbook --inventory-file=../../edx-configs/appsembler/testdrive/hosts/inventory mysql_init.yml \
		--ask-vault-pass \
		--extra-vars "@../../edx-configs/appsembler/testdrive/files/vault/secrets.yml" \
		--extra-vars "@../../edx-configs/appsembler/testdrive/files/server-vars.yml" \
		--limit mysql_init

## Run mongo_replicasets.yml playbook for testdrive
mongo-replicaset-testdrive:
	$(eval EDXCONFIGS_REPO_LOCAL_BRANCH := $(shell cd ../../edx-configs && git symbolic-ref --short -q HEAD))
	@appsembler/scripts/check_git_is_up2date.sh
	@ansible-playbook --inventory-file=../../edx-configs/appsembler/testdrive/hosts/inventory mongo_replicaset.yml \
		--ask-vault-pass \
		--extra-vars "@../../edx-configs/appsembler/testdrive/files/vault/secrets.yml" \
		--extra-vars "@../../edx-configs/appsembler/testdrive/files/server-vars.yml" \
		--limit mongo

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

