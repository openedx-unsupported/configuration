#!/bin/sh
exec /usr/bin/ssh -o StrictHostKeyChecking=no -i /{{certs_home}}/git-identity "$@"
