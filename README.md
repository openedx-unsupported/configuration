# Configuration Management

## Ansible

Ansible is a configuration management tool that edX is evaluating to replace the puppet environment 
that was used for MITx and edX prior to going open source.

http://ansible.cc/docs



## Organization

The directory structure should follow Ansible best practices.

http://ansible.cc/docs/bestpractices.html

Because the directory structure changes in v1.2 we are using the dev version
of the official v1.1 release.


* Hosts -  The ec2.py inventory script generates an inventory file where hosts are assigned to groups. Individual hosts can be targeted by the "Name" tag or the instance ID. I don't think there will be a reason to set host specific variables.
* Groups - Groups are created automatically where hosts can be targeted by tags, security groups, region, etc.  In the edX context a group would be a set of machines that are deployed to that have one or more roles. 
* Roles  - A role will map to a single function/service that runs on server.


* At the top level there are yml files for every group and environment combination.
* The standard environments are _stage_ and _production_.
* Additional environments can be named as well, below an example is given called _custom_.


### Variables

The ansible.cfg that is checked into the playbook directory has hash merging turned on, this allows
us to to merge secure and custom data into the default variable definitions for every role.

For example `vars/lms_vars.yml` sets the `env_config` hash whose keys can be overridden
by `vars/secure/lms_vars.yml` for setting passwords and hostnames.  
In addition the `vars/secure/custom_vars.yml` can selectively override a subset of keys if
there is a custom environment that differs slightly from either prod or stage.


### Users and Groups

There are two classes of users, admins and environment users.

* The *admin_users* hash will be added to every server and will be put into a group that has admin bits.
* The *env_users* hash are the class of users that can be optionally included in one of the group-environment playbooks.


Example users are in the vars/secure directory:

* `/vars/secure/edxapp_stage_users.yml` <-- *env_users* for the edxapp staging environment  
* `/vars/secure/users.yml` <-- *admin_users* will be realized on every server



```
edxapp_prod.yml <-- [ example production environment playbook ]
edxapp_stage.yml <-- [ example stage environment playbook ]
edxapp_custom.yml <-- [ example custom environment playbook ]
├── files  <-- [ edX cloudformation templates ]
│   └── examples  <-- [ example cloudformation templates ]
├── group_vars <-- [ var files that correspond to ansible group names (mapped to AWS tags) ]
├── keys <-- [ public keys ]
├── roles <-- [ edX services ]
│   ├── common  <-- [ tasks that are run for all roles ]
│   │   └── tasks
│   └── lms 
│       ├── tasks <-- [ tasks that are run to setup an LMS ]
│       └── templates
└── vars <-- [ public variable definitions ]
    └── secure <-- [ secure variables (example) ]

```
    

### Installation

```
  mkvirtualenv ansible
  pip install -r ansible-requirements.txt
```

### Launching example cloudformation stack

Change the following in playbooks/cloudformation.yaml to suit your environment:

```
    args:
      template_parameters:
        KeyName: deployment
        InstanceType: m1.small
        NameTag: edx-ec2
        GroupTag: edx-group
```

And run:

  ```
  cd playbooks
  ansible-playbook cloudformation.yaml -i inventory.ini
  ```


While this is running you see the cloudformation events in the AWS console as the stack is brought up.
Loads the playbooks/cloudformation.yaml template which creates a single small EBS backed EC2 instance.
See files/examples for adding other components to the stack.


### Test EC2 tag discovery

This should return a list of tags, assumes you have a `~/.boto` file:

  `python playbooks/ec2.py`
  
  
### Running the test playbook

Create a user

  ```
  cd playbooks
  ansible-playbook test.yaml -i /path/to/ec2.py --private-key=/path/to/deployment.pem
  ```
### CloudFormation TODO for mongo backed LMS stack

1. Add ElasticCache and RDS configuration to the template
2. Update cloudformation.yaml with new params, keep sensitive data separate
3. Come up with a better tagging scheme
4. Add ELB, SSL setup

### Ansible TODO for mongo backed LMS stack

1. <s>Come up with a scheme to separate sensitive data</s>
2. <s>Create templates for /opt/wwc/lms-{env,auth}.json, these files are read by mitx/lms/envs/aws.py</s>
3. Set up virtualenv (currently configured to by default be in /opt/edx)
4. Setup and configure rsyslog and logrotate
5. Setup and configure nginx/apache
5. Create upstart script for the lms service
6. Setup and configure local mongo/mongoHQ
7. Setup and configure local sqlite/RDS
8. Create deploy playbook for git deploy


  
  
