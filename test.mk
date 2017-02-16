
yml_files:=$(shell find . -name "*.yml")
json_files:=$(shell find . -name "*.json")
jinja_files:=$(shell find . -name "*.j2")

test: test.syntax test.edx_east_roles

test.syntax: test.syntax.yml test.syntax.json test.syntax.jinja

test.syntax.yml: $(patsubst %,test.syntax.yml/%,$(yml_files))

test.syntax.yml/%:
	python -c "import sys,yaml; yaml.load(open(sys.argv[1]))" $* >/dev/null

test.syntax.json: $(patsubst %,test.syntax.json/%,$(json_files))

test.syntax.json/%:
	jsonlint -v $*

test.syntax.jinja: $(patsubst %,test.syntax.jinja/%,$(jinja_files))

test.syntax.jinja/%:
	cd playbooks && python ../tests/jinja_check.py ../$*

test.edx_east_roles:
	tests/test_edx_east_roles.sh
