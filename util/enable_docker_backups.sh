#!/usr/bin/env bash

# Enables backups for selected docker containers. Reads a newline separated list
# of container IDs from the file "container.txt" inside the same folder as this script.
# It randomizes the backup time so all containers don't slow down the server at the same time.
#
# TODO: improve container ID handling, should probably get them from the standard input

EDX_BACKUPS_S3_BUCKET=='xxxxxx'
EDX_BACKUPS_AWS_ACCESS_KEY_ID='xxxxxx'
EDX_BACKUPS_AWS_SECRET_ACCESS_KEY='xxxxx'

while read id; do
    CONTAINER_IP=$(docker inspect --format {{.NetworkSettings.IPAddress}} $id)
    RANDOM_MINUTE=$(shuf -i0-59 -n1)
    ssh -T -i insecure_key root@$CONTAINER_IP << EOF
      curl https://raw.githubusercontent.com/appsembler/configuration/appsembler/master/util/edx_db_backup.py -o /edx/bin/edx_db_backup.py
      chmod +x /edx/bin/edx_db_backup.py
      echo 'EDX_BACKUPS_S3_BUCKET=$EDX_BACKUPS_S3_BUCKET' > /etc/cron.d/edx_backup
      echo 'EDX_BACKUPS_AWS_ACCESS_KEY_ID=$EDX_BACKUPS_AWS_ACCESS_KEY_ID' >> /etc/cron.d/edx_backup
      echo 'EDX_BACKUPS_AWS_SECRET_ACCESS_KEY=$EDX_BACKUPS_AWS_SECRET_ACCESS_KEY' >> /etc/cron.d/edx_backup
      echo '$RANDOM_MINUTE 8 * * * root /edx/bin/edx_db_backup.py backup' >> /etc/cron.d/edx_backup
EOF
done < containers.txt
