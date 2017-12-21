FROM edxops/go-agent

# Install necessary modules for running make requirements in edx-mktg
# Using rvm so we can control the ruby version installed. This also installs gem 2.6.12
RUN apt-add-repository -y ppa:rael-gc/rvm && apt-get update && \
    apt-get install -y rvm && source /usr/share/rvm/scripts/rvm && \
    rvm install ruby-2.4.1 && gem install bundler -v 1.16.0
# Installs node 8.9.3 and npm 5.5.1 as of 12/13/17. Unlikely to change much since node 9 is a stable version for other OS
RUN curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash - && \
    apt-get update && apt-get install -y nodejs

# Install php
RUN apt-get update && apt-get install -y \
    php5-common \
    php5-cli

# Install drush (drupal shell) for access to Drupal commands/Acquia
RUN php -r "readfile('http://files.drush.org/drush.phar');" > drush && \
    chmod +x drush && \
    sudo mv drush /usr/local/bin
