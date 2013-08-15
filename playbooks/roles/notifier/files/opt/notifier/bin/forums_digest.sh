#!/bin/bash

. $HOME/.bashrc

minutes=$1
digest_date=`date --utc '+%Y-%m-%dT%H:%MZ'`

cd /opt/wwc/notifier/src && /opt/wwc/notifier/virtualenvs/notifier/bin/python /opt/wwc/notifier/src/manage.py forums_digest --to_datetime=${digest_date} --minutes=${minutes}
