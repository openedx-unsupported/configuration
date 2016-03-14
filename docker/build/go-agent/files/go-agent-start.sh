#!/bin/bash

GO_SERVER=${GO_SERVER:-go-server}
GO_SERVER_PORT=${GO_SERVER_PORT:-go-server-port}


COLOR_START="[01;34m"
COLOR_END="[00m"

echo -e "${COLOR_START}Starting Go Agent to connect to server $GO_SERVER:$GO_SERVER_PORT ...${COLOR_END}"
sed -i -e 's/GO_SERVER=.*/GO_SERVER='$GO_SERVER'/' /etc/default/go-agent
sed -i -e 's/GO_SERVER_PORT=.*/GO_SERVER_PORT='$GO_SERVER_PORT'/' /etc/default/go-agent
sed -i -e 's/GO_SERVER_SSL_PORT=.*/GO_SERVER_SSL_PORT='$GO_SERVER_SSL_PORT'/' /etc/default/go-agent

mkdir -p /var/lib/go-agent/config
/bin/rm -f /var/lib/go-agent/config/autoregister.properties

AGENT_KEY="${AGENT_KEY:-123456789abcdef}"
echo "agent.auto.register.key=$AGENT_KEY" >/var/lib/go-agent/config/autoregister.properties
if [ -n "$AGENT_RESOURCES" ]; then echo "agent.auto.register.resources=$AGENT_RESOURCES" >>/var/lib/go-agent/config/autoregister.properties; fi
if [ -n "$AGENT_ENVIRONMENTS" ]; then echo "agent.auto.register.environments=$AGENT_ENVIRONMENTS" >>/var/lib/go-agent/config/autoregister.properties; fi

/sbin/setuser go /etc/init.d/go-agent start