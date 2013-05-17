#!/bin/sh
exec ssh -i "/etc/git-identity" -o "StrictHostKeyChecking no" "$@"
