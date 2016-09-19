#!/bin/bash
set -e

/usr/sbin/rsyslogd
/edx/app/supervisor/venvs/supervisor/bin/supervisord --nodaemon --configuration /edx/app/supervisor/supervisord.conf
