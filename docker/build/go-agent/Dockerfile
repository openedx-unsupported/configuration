# Build using: docker build -f Dockerfile.gocd-agent -t gocd-agent .
# FROM edxops/precise-common:latest
FROM gocd/gocd-agent:16.2.1

LABEL version="0.01" \
      description="This custom go-agent docker file installs additional requirements for the edx pipeline"


RUN apt-get update && apt-get install -y -q \
    python \
    python-dev \
    python-distribute \
    python-pip

# TODO: repalce this with a pip install command so we can version this properly
RUN git clone https://github.com/edx/tubular.git /opt/tubular
RUN pip install -r /opt/tubular/requirements.txt
RUN cd /opt/tubular;python setup.py install