SHELL := /bin/bash
.PHONY: help requirements clean build test pkg

help: main.help

main.help:
	@echo ''
	@echo 'Makefile for the edX Configuration'
	@echo ''
	@echo 'Usage:'
	@echo '    make requirements              install requirements'
	@echo '    make upgrade                   upgrade dependencies in requirements files'
	@echo '    make test                      run all tests'
	@echo '    make build                     build everything'
	@echo '    make pkg                       package everything'
	@echo '    make clean                     remove build by-products'
	@echo ''

requirements:
	pip install -qr pre-requirements.txt --exists-action w
	pip install -qr requirements.txt --exists-action w

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the pip requirements files to use the latest releases satisfying our constraints
	pip install -qr pre-requirements.txt --exists-action w
	pip install -qr requirements/pip-tools.txt
	# Make sure to compile files after any other files they include!
	pip-compile --upgrade -o requirements/pip-tools.txt requirements/pip-tools.in
	pip-compile --upgrade -o requirements.txt requirements/base.in
	pip-compile --upgrade -o playbooks/roles/aws/templates/requirements.txt.j2 requirements/aws.in
	pip-compile --upgrade -o util/elasticsearch/requirements.txt requirements/elasticsearch.in
	pip-compile --upgrade -o util/jenkins/update_celery_monitoring/requirements.txt requirements/celery.in
	pip-compile --upgrade -o util/jenkins/check_celery_progress/requirements.txt requirements/celery_progress.in
	pip-compile --upgrade -o util/jenkins/requirements-cloudflare.txt requirements/cloudflare.in
	pip-compile --upgrade -o util/pingdom/requirements.txt requirements/pingdom.in
	pip-compile --upgrade -o util/vpc-tools/requirements.txt requirements/vpc-tools.in
	# Post process all of the files generated above to work around open pip-tools issues
	util/post-pip-compile.sh \
 	    requirements/pip-tools.txt \
	    requirements.txt \
	    playbooks/roles/aws/templates/requirements.txt.j2 \
	    util/elasticsearch/requirements.txt \
	    util/jenkins/update_celery_monitoring/requirements.txt \
	    util/jenkins/check_celery_progress/requirements.txt \
	    util/jenkins/requirements-cloudflare.txt \
	    util/pingdom/requirements.txt \
	    util/vpc-tools/requirements.txt

include *.mk
