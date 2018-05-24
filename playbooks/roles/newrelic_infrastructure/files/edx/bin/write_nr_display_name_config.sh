#! /usr/bin/env bash

if command -v ec2metadata >/dev/null 2>&1; then
  INSTANCEID=$(ec2metadata --instance-id);
  HOSTNAME=$(hostname)
  DISPLAY_NAME="$HOSTNAME-$INSTANCEID"
  if [[ -f /etc/newrelic/nrsysmond.cfg ]]; then
      sudo sed -i 's/^hostname=.*//g' /etc/newrelic/nrsysmond.cfg 
      echo "hostname=\"$DISPLAY_NAME\"" | sudo tee -a /etc/newrelic/nrsysmond.cfg
      sudo service newrelic-sysmond restart
  fi
  if [[ -f /etc/newrelic-infra.yml ]]; then
      sudo sed -i 's/^display_name: .*//g' /etc/newrelic-infra.yml
      echo "display_name: \"$DISPLAY_NAME\"" | sudo tee -a /etc/newrelic-infra.yml
      sudo service newrelic-infra restart
  fi
fi

