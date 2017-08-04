# To build this Dockerfile:
#
# From the root of the edx-e2e-tests repository:
#
# docker build -f Dockerfile . -t edxops/e2e:latest

FROM edxops/python:2.7
MAINTAINER edxops

# Install system libraries needed for lxml
RUN apt-get update -qqy \
    && apt-get -qqy install \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

ADD . /edx-e2e-tests
WORKDIR /edx-e2e-tests

# Set up the virtualenv
# Deletes the edx-platform checkout afterwards, it will be mapped in from the host
RUN pip install -r requirements/base.txt \
    && paver install_pages \
    && rm -rf /edx-e2e-tests/lib

CMD ["paver", "e2e_test", "--exclude=whitelabel"]
