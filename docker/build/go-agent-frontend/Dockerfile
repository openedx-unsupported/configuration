FROM edxops/go-agent:latest

RUN curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash - && \
    apt-get update && apt-get install -y nodejs

# !!!!NOTICE!!!! ---- Runner of this pipeline take heed!! You must replace go_github_key.pem with the REAL key material
# that can checkout private github repositories used as pipeline materials. The key material here is faked and is only
# used to pass CI!
# setup the github identity
ADD docker/build/go-agent/files/go_github_key.pem /home/go/.ssh/id_rsa
RUN chmod 600 /home/go/.ssh/id_rsa && \
    chown go:go /home/go/.ssh/id_rsa
