.PHONY = monitoring deploy-testdrive mysql-init-testdrive mongo-replicaset-testdrive deploy-amc

.DEFAULT_GOAL = help

EDXCONFIGS_BRANCH=master

## Install monitoring on customer cluster. Example: CUSTOMER=qa ENVIRONMENT=prod TIER=basic PLATFORM=azure make monitoring
monitoring:
	@@if test -z "$$CUSTOMER"; then echo "ERROR: CUSTOMER is not defined."; exit 1; fi;
	@@if test -z "$$PLATFORM"; then echo "ERROR: PLATFORM is not defined."; exit 1; fi;
	@@if test -z "$$TIER"; then echo "ERROR: TIER is not defined."; exit 1; fi;
	@@if test -z "$$ENVIRONMENT"; then echo "ERROR: ENVIRONMENT is not defined."; exit 1; fi;
	@ansible-playbook -i inventory monitoring.yml --extra-vars "@../../edx-configs/$$CUSTOMER/$$ENVIRONMENT/server-vars.yml"

## Deploy testdrive. Needs ENVIRONMENT defined. For example. ENVIRONEMT=prod make deploy-testdrive
deploy-testdrive:
	$(eval EDXCONFIGS_REPO_LOCAL_BRANCH := $(shell cd ../../edx-configs && git symbolic-ref --short -q HEAD))
	@@if test -z "$$ENVIRONMENT"; then echo "ERROR: ENVIRONMENT is not defined."; exit 1; fi;
	@appsembler/scripts/check_git_is_up2date.sh
	@ansible-playbook --inventory-file=../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/hosts/inventory testdrive.yml --ask-vault-pass \
		--extra-vars "@../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/files/vault/secrets.yml" \
		--extra-vars "@../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/files/server-vars.yml"

## Deploy AMC. Needs ENVIRONMENT defined. For example. ENVIRONEMT=prod make deploy-amc
deploy-amc:
	$(eval EDXCONFIGS_REPO_LOCAL_BRANCH := $(shell cd ../../edx-configs && git symbolic-ref --short -q HEAD))
	@@if test -z "$$ENVIRONMENT"; then echo "ERROR: ENVIRONMENT is not defined."; exit 1; fi;
	@appsembler/scripts/check_git_is_up2date.sh
	@ansible-playbook --inventory-file=../../edx-configs/appsembler/amc/$$ENVIRONMENT/hosts/inventory amc.yml \
		--extra-vars "@../../edx-configs/appsembler/amc/$$ENVIRONMENT/files/server-vars.yml"

## Run mysql_init.yml playbook for testdrive. Needs ENVIRONMENT defined. For example. ENVIRONEMT=prod make mysql-init-testdrive
mysql-init-testdrive:
	$(eval EDXCONFIGS_REPO_LOCAL_BRANCH := $(shell cd ../../edx-configs && git symbolic-ref --short -q HEAD))
	@@if test -z "$$ENVIRONMENT"; then echo "ERROR: ENVIRONMENT is not defined."; exit 1; fi;
	@appsembler/scripts/check_git_is_up2date.sh
	@ansible-playbook --inventory-file=../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/hosts/inventory mysql_init.yml \
		--ask-vault-pass \
		--extra-vars "@../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/files/vault/secrets.yml" \
		--extra-vars "@../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/files/server-vars.yml" \
		--limit mysql_init

## Run mongo_replicasets.yml playbook for testdrive. Needs ENVIRONMENT defined. For example. ENVIRONEMT=prod make mongo-replicaset-testdrive
mongo-replicaset-testdrive:
	$(eval EDXCONFIGS_REPO_LOCAL_BRANCH := $(shell cd ../../edx-configs && git symbolic-ref --short -q HEAD))
	@@if test -z "$$ENVIRONMENT"; then echo "ERROR: ENVIRONMENT is not defined."; exit 1; fi;
	@appsembler/scripts/check_git_is_up2date.sh
	@ansible-playbook --inventory-file=../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/hosts/inventory mongo_replicaset.yml \
		--ask-vault-pass \
		--extra-vars "@../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/files/vault/secrets.yml" \
		--extra-vars "@../../edx-configs/appsembler/testdrive/$$ENVIRONMENT/files/server-vars.yml" \
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

