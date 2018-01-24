SHELL := /bin/bash
.PHONY: help requirements clean build test pkg

help: main.help

main.help:
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

requirements:
	pip install -qr pre-requirements.txt --exists-action w
	pip install -qr requirements.txt --exists-action w

include *.mk
