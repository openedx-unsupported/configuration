#!/bin/sh
exec /usr/bin/ssh -o StrictHostKeyChecking=no -i /etc/git-identity "$@"
