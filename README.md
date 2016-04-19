# Configuration Management

## Introduction

The goal of the edx/configuration project is to provide a simple, but
flexible, way for anyone to stand up an instance of Open edX that is
fully configured and ready-to-go.

Before getting started, please look at the [Open EdX Installation options](https://open.edx.org/installation-options), to see which method for deploying OpenEdX is right for you.

Building the platform takes place in two phases:

* Infrastructure provisioning
* Service configuration

As much as possible, we have tried to keep a clean distinction between
provisioning and configuration.  You are not obliged to use our tools
and are free to use one, but not the other.  The provisioning phase
stands-up the required resources and tags them with role identifiers
so that the configuration tool can come in and complete the job.

__Note__: The Cloudformation templates used for infrastructure provisioning 
are no longer maintained. We are working to move to a more modern and flexible tool.

The reference platform is provisioned using an Amazon
[CloudFormation](http://aws.amazon.com/cloudformation/) template.
When the stack has been fully created you will have a new AWS Virtual
Private Cloud with hosts for the core Open edX services.  This template
will build quite a number of AWS resources that cost money, so please
consider this before you start.

The configuration phase is managed by [Ansible](http://ansible.com/).
We have provided a number of playbooks that will configure each of
the Open edX services.

__Important__: 
The Open edX configuration scripts need to be run as root on your servers and will make changes to service configurations including, but not limited to, sshd, dhclient, sudo, apparmor and syslogd. Our scripts are made available as we use them and they implement our best practices. We strongly recommend that you review everything that these scripts will do before running them against your servers. We also recommend against running them against servers that are hosting other applications. No warranty is expressed or implied.

For more information including installation instruction please see the [OpenEdX Wiki](https://openedx.atlassian.net/wiki/display/OpenOPS/Open+edX+Operations+Home).

For info on any large recent changes please see the [change log](https://github.com/edx/configuration/blob/master/CHANGELOG.md).
