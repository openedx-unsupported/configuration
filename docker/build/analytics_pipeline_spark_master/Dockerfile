FROM bde2020/spark-base:2.1.0-hadoop2.7
MAINTAINER edxops

ADD docker/build/analytics_pipeline_spark_master/master.sh /
ENV SPARK_MASTER_PORT=7077 \
    SPARK_MASTER_WEBUI_PORT=8080 \
    SPARK_MASTER_LOG=/spark/logs \
    HADOOP_USER_NAME=hadoop \
    SPARK_HOME=/spark \
    PATH=$PATH:/spark/bin

RUN apt-get -y update && apt-get -y install --reinstall python-pkg-resources \
    && echo 'spark.master  spark://sparkmaster:7077\nspark.eventLog.enabled  true\nspark.eventLog.dir  hdfs://namenode:8020/tmp/spark-events\nspark.history.fs.logDirectory  hdfs://namenode:8020/tmp/spark-events' > /spark/conf/spark-defaults.conf

CMD ["/bin/bash", "/master.sh"]
# 18080: spark history server port
# 4040: spark UI port
# 6066: spark api port
EXPOSE 8080 7077 6066 18080 4040
