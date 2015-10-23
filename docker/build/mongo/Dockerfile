FROM edxops/precise-common:v1
MAINTAINER arbabnazar
RUN sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
RUN echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list
RUN sudo apt-get update && sudo apt-get install -y mongodb-org
RUN sudo sed -i -e 's/127.0.0.1/0.0.0.0/' /etc/mongod.conf
RUN sudo mkdir -p /data/db && sudo chown -R mongodb:mongodb /data/db
USER root
EXPOSE 27017/tcp 27018/tcp 27019/tcp
CMD ["/usr/bin/mongod" "--smallfiles" "--config" "/etc/mongod.conf" "--logpath" "/var/log/mongodb/mongodb.log"]
