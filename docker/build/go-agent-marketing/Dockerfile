FROM edxops/go-agent:latest

# Install necessary modules for running make requirements in edx-mktg
# Using rvm so we can control the ruby version installed. This also installs gem 2.6.12
RUN bash -c '\curl -sSL https://get.rvm.io | bash -s -- --ignore-dotfiles && \
    usermod -aG rvm go && source /etc/profile.d/rvm.sh && \
    rvm install ruby-2.4.1 && gem install bundler -v 1.16.0'

# Installs node 12 and npm 6 as of October 2019.
RUN curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash - && \
    apt-get update && apt-get install -y nodejs

# Install php
RUN apt-get update && apt-get install -y \
    php-common \
    php-cli

# Install drush (drupal shell) for access to Drupal commands/Acquia
RUN php -r "readfile('https://github.com/drush-ops/drush/releases/download/8.2.3/drush.phar');" > drush && \
    chmod +x drush && \
    sudo mv drush /usr/local/bin

# !!!!NOTICE!!!! ---- Runner of this pipeline take heed!! You must replace acquia_github_key.pem with the REAL key
# material that can checkout private github repositories used as pipeline materials. The key material here is faked and
# is only used to pass CI!
# setup the acquia github identity
ADD docker/build/go-agent-marketing/files/acquia_github_key.pem /home/go/.ssh/acquia_github_key
RUN chmod 600 /home/go/.ssh/acquia_github_key && \
    chown go:go /home/go/.ssh/acquia_github_key
