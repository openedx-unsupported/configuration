# Docker Support

## Introduction

Docker support for edX services is volatile and experimental.
We welcome interested testers and contributors. If you are
interested in paticipating, please join us on Slack at
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

make docker.test.<service>   # Test that the Dockerfile for <service> will build.
                             # This will rebuild any edx-specific containers that
                             # the Dockerfile depends on as well, in case there
                             # are failures as a result of changes to the base image.

make docker.pkg.<service>    # Package <service> for publishing to Dockerhub. This
                             # will also package and tag pre-requisite service containers.

make docker.push.<service>   # Push <service> to Dockerhub as latest.
```

