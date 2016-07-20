.PHONY = monitoring

.DEFAULT_GOAL = help

## Install monitoring on customer cluster. Example: CUSTOMER=qa ENVIRONMENT=production TIER=basic PLATFORM=azure make monitoring
monitoring:
	@@if test -z "$$CUSTOMER"; then echo "ERROR: CUSTOMER is not defined."; exit 1; fi;
	@@if test -z "$$PLATFORM"; then echo "ERROR: PLATFORM is not defined."; exit 1; fi;
	@@if test -z "$$TIER"; then echo "ERROR: TIER is not defined."; exit 1; fi;
	@@if test -z "$$ENVIRONMENT"; then echo "ERROR: ENVIRONMENT is not defined."; exit 1; fi;
	@ansible-playbook -i inventory monitoring.yml --extra-vars "@../../edx-configs/$$CUSTOMER/$$ENVIRONMENT/server-vars.yml"

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

