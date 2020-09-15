#!/bin/bash

: ${HADOOP_HOME:=/edx/app/hadoop/hadoop}

bash $HADOOP_HOME/etc/hadoop/hadoop-env.sh
. /edx/app/analytics_pipeline/venvs/analytics_pipeline/bin/activate && make develop-local

# installing libraries if any - (resource urls added comma separated to the ACP system variable)
cd $HADOOP_HOME/share/hadoop/common ; for cp in ${ACP//,/ }; do  echo == $cp; curl -LO $cp ; done; cd -


if [[ $1 == "-d" ]]; then
  while true; do sleep 30; done
fi

if [[ $1 == "-bash" ]]; then
  /bin/bash
fi
