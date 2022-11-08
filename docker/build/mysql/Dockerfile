FROM debian:buster-slim

# add gosu for easy step-down from root
# https://github.com/tianon/gosu/releases
ENV GOSU_VERSION 1.14

ENV MYSQL_MAJOR 5.7
ENV MYSQL_MINOR ${MYSQL_MAJOR}.39
ENV MYSQL_VERSION 5.7.39-1debian10

RUN set -eux; \
        # add our user and group first to make sure their IDs get assigned consistently, regardless of whatever dependencies get added
        groupadd -r mysql && useradd -r -g mysql mysql; \
        export DEBIAN_FRONTEND=noninteractive; \
        apt-get update && apt-get install -y --no-install-recommends gnupg && rm -rf /var/lib/apt/lists/*; \
        savedAptMark="$(apt-mark showmanual)"; \
        apt-get update; \
        apt-get install -y --no-install-recommends ca-certificates wget; \
        rm -rf /var/lib/apt/lists/*; \
        dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"; \
        wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-$dpkgArch"; \
        wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-$dpkgArch.asc"; \
        export GNUPGHOME="$(mktemp -d)"; \
        gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4; \
        gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu; \
        gpgconf --kill all; \
        rm -rf "$GNUPGHOME" /usr/local/bin/gosu.asc; \
        apt-mark auto '.*' > /dev/null; \
        [ -z "$savedAptMark" ] || apt-mark manual $savedAptMark > /dev/null; \
        apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
        chmod +x /usr/local/bin/gosu; \
        gosu --version; \
        gosu nobody true; \
        mkdir /docker-entrypoint-initdb.d; \
        DEVELOPMENT_PACKAGES="pkg-config libssl-dev dpkg-dev devscripts equivs"; \
        apt-get update; \
        apt-get install -y --no-install-recommends \
                bzip2 \
                openssl \
                # FATAL ERROR: please install the following Perl modules before executing /usr/local/mysql/scripts/mysql_install_db:
                # File::Basename
                # File::Copy
                # Sys::Hostname
                # Data::Dumper
                perl \
                xz-utils \
                zstd \
                ${DEVELOPMENT_PACKAGES}; \
        rm -rf /var/lib/apt/lists/*; \
        # gpg: key 3A79BD29: public key "MySQL Release Engineering <mysql-build@oss.oracle.com>" imported
        key='859BE8D7C586F538430B19C2467B942D3A79BD29'; \
        export GNUPGHOME="$(mktemp -d)"; \
        gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "$key"; \
        mkdir -p /etc/apt/keyrings; \
        gpg --batch --export "$key" > /etc/apt/keyrings/mysql.gpg; \
        gpgconf --kill all; \
        rm -rf "$GNUPGHOME"; \
  # RUN echo 'deb [ signed-by=/etc/apt/keyrings/mysql.gpg ] http://repo.mysql.com/apt/debian/ buster mysql-5.7' > /etc/apt/sources.list.d/mysql.list
        echo 'deb [ signed-by=/etc/apt/keyrings/mysql.gpg ] http://repo.mysql.com/apt/debian/ buster mysql-5.7' > /etc/apt/sources.list.d/mysql.list; \
        echo 'deb-src [ signed-by=/etc/apt/keyrings/mysql.gpg ] http://repo.mysql.com/apt/debian/ buster mysql-5.7' >> /etc/apt/sources.list.d/mysql.list; \
# the "/var/lib/mysql" stuff here is because the mysql-server postinst doesn't have an explicit way to disable the mysql_install_db codepath besides having a database already "configured" (ie, stuff in /var/lib/mysql/mysql)
# also, we set debconf keys to make APT a little quieter
        { \
                echo mysql-community-server mysql-community-server/data-dir select ''; \
                echo mysql-community-server mysql-community-server/root-pass password ''; \
                echo mysql-community-server mysql-community-server/re-root-pass password ''; \
                echo mysql-community-server mysql-community-server/remove-test-db select false; \
        } | debconf-set-selections; \
        apt-get update; \
        mk-build-deps mysql-community-server --install --tool "apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends -y"; \
        mkdir /usr/src/mysql; \
        cd /usr/src/mysql; \
        apt source mysql-community-server; \
        cd mysql-community-*; \
        sed -i -e "s/\-DWITH_BOOST\=\/usr\/global\/share/\-DWITH_BOOST\=\/tmp\/boost \-DDOWNLOAD_BOOST\=1/g" debian/rules; \
        sed -i -e "s/\-DWITH_SSL\=.* /-DWITH_SSL\=system /g" debian/rules; \
        debuild -b -uc -us; \
        cd ~; \
        dpkg --install \
                /usr/src/mysql/mysql-common_*.deb \
                /usr/src/mysql/mysql-community-server_*.deb \
                /usr/src/mysql/mysql-community-client_*.deb \
                /usr/src/mysql/mysql-server_*.deb \
                /usr/src/mysql/mysql-client_*.deb; \
        rm -rf /usr/src/mysql /tmp/boost /mysql-community-build-deps*deb; \
        apt-get remove --purge -y mysql-community-build-deps ${DEVELOPMENT_PACKAGES}; \
        apt-get -y autoremove; \
        apt-get clean all; \
        # comment out a few problematic configuration values
        find /etc/mysql/ -name '*.cnf' -print0 \
                | xargs -0 grep -lZE '^(bind-address|log)' \
                | xargs -rt -0 sed -Ei 's/^(bind-address|log)/#&/'; \
        # don't reverse lookup hostnames, they are usually another container
        echo '[mysqld]\nskip-host-cache\nskip-name-resolve' > /etc/mysql/conf.d/docker.cnf; \
        rm -rf /var/lib/apt/lists/*; \
        rm -rf /var/lib/mysql && mkdir -p /var/lib/mysql /var/run/mysqld; \
        chown -R mysql:mysql /var/lib/mysql /var/run/mysqld; \
        # ensure that /var/run/mysqld (used for socket and lock files) is writable regardless of the UID our mysqld instance ends up having at runtime
        chmod 1777 /var/run/mysqld /var/lib/mysql

VOLUME /var/lib/mysql

COPY docker-entrypoint.sh /usr/local/bin/
RUN ln -s usr/local/bin/docker-entrypoint.sh /entrypoint.sh # backwards compat
ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 3306 33060
CMD ["mysqld"]
