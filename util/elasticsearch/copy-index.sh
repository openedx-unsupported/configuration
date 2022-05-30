#!/usr/bin/env bash
set -euo pipefail

#
# Thin wrapper around logstash. You will first have to install logstash. Simply
# downloading the tar.gz from their site is sufficient. Note that logstash may have
# different JVM version requiements than what is available on your machine.
#
# https://www.elastic.co/products/logstash
#
# Assumes that logstash is in your path.
#
# Copies an index from an elasticsearch source server to a target server. 
# The target server can be the same as the source.
#
# Usage:
#   copy-index.sh SOURCE_SERVER SOURCE_INDEX TARGET_SERVER TARGET_INDEX [WORKERS]
#
# Example:
#   ./copy-index.sh http://localhost source_index http://localhost target_index
#

SOURCE_SERVER=$1
SOURCE_INDEX=$2
TARGET_SERVER=$3
TARGET_INDEX=$4

WORKERS="${5:-6}"

read -d '' filter <<EOF || true  #read won't find its delimiter and exit with status 1, this is intentional
input {
  elasticsearch {
    hosts => "$SOURCE_SERVER"
    index => "$SOURCE_INDEX"    #content for forums
    scroll => "12h"         #must be as long as the run takes to complete
    scan => true            #scan through all indexes efficiently
    docinfo => true         #necessary to move document_type and document_id over
  }
}
 
output {
  elasticsearch {
    hosts => "$TARGET_SERVER"
    index => "$TARGET_INDEX"    #same as above
    manage_template => false
    document_type => "%{[@metadata][_type]}"
    document_id => "%{[@metadata][_id]}"
  }
  stdout {
    codec => "dots"   #Print a dot when stuff gets moved so we know it's working
  }
}
 
filter {
  mutate {
    remove_field => ["@timestamp", "@version"]  #these fields get added by logstash for some reason
  }
}
EOF

logstash -w "$WORKERS" -e "$filter"
