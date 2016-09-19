# Docker Support

## Introduction

Docker support for edX services is volatile and experimental.
We welcome interested testers and contributors. If you are
interested in participating, please join us on Slack at
https://openedx.slack.com/messages/docker.

We do not and may never run run these images in production.
They are not currently suitable for production use.

## Tooling

`Dockerfile`s for individual services should be placed in
`docker/build/<service>`. There should be an accompanying `ansible_overrides.yml`
which specifies any docker-specific configuration values.

Once the `Dockerfile` has been created, it can be built and published
using a set of make commands.

```shell
make docker.build.<service>  # Build the service container (but don't tag it)
                             # By convention, this will build the container using
                             # the currently checked-out configuration repository,
                             # and will build on top of the most-recently available
                             # base container image from dockerhub.

make docker.test.<service>   # Test that the Dockerfile for <service> will build.
                             # This will rebuild any edx-specific containers that
                             # the Dockerfile depends on as well, in case there
                             # are failures as a result of changes to the base image.

make docker.pkg.<service>    # Package <service> for publishing to Dockerhub. This
                             # will also package and tag pre-requisite service containers.

make docker.push.<service>   # Push <service> to Dockerhub as latest.
```

## Conventions

In order to facilitate development, Dockerfiles should be based on
one of the `edxops/<ubuntu version>-common` base images, and should
`COPY . /edx/app/edx_ansible/edx_ansible` in order to load your local
ansible plays into the image. The actual work of configuring the image
should be done by executing ansible (rather than explicit steps in the
Dockerfile), unless those steps are docker specific. Devstack-specific
steps can be tagged with the `devstack:install` tag in order that they
only run when building a devstack image.

The user used in the `Dockerfile` should be `root`.
