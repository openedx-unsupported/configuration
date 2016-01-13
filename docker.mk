.PHONY: docker.build docker.test docker.pkg

SHARD=0
SHARDS=1

dockerfiles:=$(shell ls docker/build/*/Dockerfile)
images:=$(patsubst docker/build/%/Dockerfile,%,$(dockerfiles))

docker_build=docker.build.
docker_test=docker.test.
docker_pkg=docker.pkg.
docker_push=docker.push.
docker_lint=docker.lint.

# N.B. / is used as a separator so that % will match the /
# in something like 'edxops/trusty-common:latest'
# Also, make can't handle ':' in filenames, so we instead '@'
# which means the same thing to docker
docker_pull=docker.pull/

build: docker.build

test: docker.test

pkg: docker.pkg

clean:
	rm -rf .build

docker.test.shard: $(foreach image,$(shell echo $(images) | tr ' ' '\n' | sed -n '$(SHARD)~$(SHARDS)p'),$(docker_test)$(image))

docker.build: $(foreach image,$(images),$(docker_build)$(image))
docker.test: $(foreach image,$(images),$(docker_test)$(image))
docker.pkg: $(foreach image,$(images),$(docker_pkg)$(image))
docker.push: $(foreach image,$(images),$(docker_push)$(image))
docker.lint: $(foreach image,$(images),$(docker_lint)$(image))

$(docker_pull)%:
	docker pull $*

$(docker_build)%: docker/build/%/Dockerfile
	docker build -f $< .

$(docker_test)%: .build/%/Dockerfile.test
	docker build -t $*:test -f $< .

$(docker_pkg)%: .build/%/Dockerfile.pkg
	docker build -t $*:latest -f $< .

$(docker_push)%: $(docker_pkg)%
	docker tag -f $*:latest edxops/$*:latest
	docker push edxops/$*:latest

$(docker_lint)%: docker/build/%/Dockerfile $(docker_pull)lukasmartinelli/hadolint
	docker run --rm -i lukasmartinelli/hadolint < $<

.build/%/Dockerfile.d: docker/build/%/Dockerfile Makefile
	@mkdir -p .build/$*
	$(eval FROM=$(shell grep "FROM" $< | sed --regexp-extended "s/FROM //" | sed --regexp-extended "s/:/@/g"))
	$(eval EDXOPS_FROM=$(shell echo "$(FROM)" | sed --regexp-extended "s#edxops/([^@]+)(@.*)?#\1#"))
	@echo "$(docker_build)$*: $(docker_pull)$(FROM)" > $@
	@if [ "$(EDXOPS_FROM)" != "$(FROM)" ]; then \
	echo "$(docker_test)$*: $(docker_test)$(EDXOPS_FROM:@%=)" >> $@; \
	echo "$(docker_pkg)$*: $(docker_pkg)$(EDXOPS_FROM:@%=)" >> $@; \
	else \
	echo "$(docker_test)$*: $(docker_pull)$(FROM)" >> $@; \
	echo "$(docker_pkg)$*: $(docker_pull)$(FROM)" >> $@; \
	fi

.build/%/Dockerfile.test: docker/build/%/Dockerfile Makefile
	@mkdir -p .build/$*
	@sed --regexp-extended "s#FROM edxops/([^:]+)(:\S*)?#FROM \1:test#" $< > $@

.build/%/Dockerfile.pkg: docker/build/%/Dockerfile Makefile
	@mkdir -p .build/$*
	@sed --regexp-extended "s#FROM edxops/([^:]+)(:\S*)?#FROM \1:test#" $< > $@

include $(foreach image,$(images),.build/$(image)/Dockerfile.d)
