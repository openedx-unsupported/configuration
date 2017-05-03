yml_files:=$(shell find . -name "*.yml")
json_files:=$(shell find . -name "*.json")
# $(images) is calculated in the docker.mk file

help: test.help

test.help:
	@echo '    Tests:'
	@echo '        test.syntax                Run all syntax tests'
	@echo '        test.syntax.json           Run syntax tests on .json files'
	@echo '        test.syntax.yml            Run syntax tests on .yml files'
	@echo '        test.syntax.jinja          Run syntax tests on .j2 files'
	@echo '        test.edx_east_roles        Run validation on edx-east roles'
	@echo ''

test: test.syntax test.edx_east_roles

test.syntax: test.syntax.yml test.syntax.json test.syntax.dockerfiles

test.syntax.yml: $(patsubst %,test.syntax.yml/%,$(yml_files))

test.syntax.yml/%:
	python -c "import sys,yaml; yaml.load(open(sys.argv[1]))" $* >/dev/null

test.syntax.json: $(patsubst %,test.syntax.json/%,$(json_files))

test.syntax.json/%:
	jsonlint -v $*

test.syntax.dockerfiles:
	python util/check_dockerfile_coverage.py "$(images)"

test.edx_east_roles:
	tests/test_edx_east_roles.sh

clean: test.clean

test.clean:
	rm -rf playbooks/edx-east/test_output
