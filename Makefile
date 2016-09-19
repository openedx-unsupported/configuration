SHELL := /bin/bash
.PHONY: help requirements clean build test pkg

include *.mk

help:
	@echo ''
	@echo 'Makefile for the edX Configuration'
	@echo ''
	@echo 'Usage:'
	@echo '    make requirements              install requirements'
	@echo '    make test                      run all tests'
	@echo '    make build                     build everything'
	@echo '    make pkg                       package everything'
	@echo '    make clean                     remove build by-products'
	@echo ''
	@echo '    Docker:'
	@echo '        $$image: any dockerhub image'
	@echo '        $$container: any container defined in docker/build/$$container/Dockerfile'
	@echo ''
	@echo '        make $(docker_pull)$$image        pull $$image from dockerhub'
	@echo ''
	@echo '        make $(docker_build)$$container   build $$container'
	@echo '        make $(docker_test)$$container    test that $$container will build'
	@echo '        make $(docker_pkg)$$container     package $$container for a push to dockerhub'
	@echo '        make $(docker_push)$$container    push $$container to dockerhub '
	@echo ''
	@echo '        make docker.build          build all defined docker containers (based on dockerhub base images)'
	@echo '        make docker.test           test all defined docker containers'
	@echo '        make docker.pkg            package all defined docker containers (using local base images)'
	@echo '        make docker.push           push all defined docker containers'
	@echo ''
	@echo '    Tests:'
	@echo '        test.syntax                Run all syntax tests'
	@echo '        test.syntax.json           Run syntax tests on .json files'
	@echo '        test.syntax.yml            Run syntax tests on .yml files'
	@echo '        test.syntax.jinja          Run syntax tests on .j2 files'
	@echo '        test.edx_east_roles        Run validation on edx-east roles'
	@echo ''

requirements:
	pip install -qr pre-requirements.txt --exists-action w
	pip install -qr requirements.txt --exists-action w
