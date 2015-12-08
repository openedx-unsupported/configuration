help:
	@echo '													'
	@echo 'Makefile for the edX Configuration                                                               ' 
	@echo '                                                                                     		'
	@echo 'Usage:                                                                               		'
	@echo '    make requirements                 install requirements					'
	@echo '                                                                                     		'

requirements:
	pip install -qr pre-requirements.txt --exists-action w
	pip install -qr requirements.txt --exists-action w

# Targets in a Makefile which do not produce an output file with the same name as the target name
.PHONY: help requirements 
