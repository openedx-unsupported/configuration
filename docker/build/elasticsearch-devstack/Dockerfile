# docker build -f docker/build/elasticsearch-devstack/Dockerfile . -t edxops/elasticsearch:devstack

FROM elasticsearch:1.5.2
MAINTAINER edxops

# Install the elastcisearch-head plugin (https://mobz.github.io/elasticsearch-head/)
RUN /usr/share/elasticsearch/bin/plugin -install mobz/elasticsearch-head
