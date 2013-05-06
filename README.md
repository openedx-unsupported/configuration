# Configuration Management
## AWS

### Tagging

Every AWS EC2 instance will have a *Group* tag that corresponds to a group of
machines that need to be deployed/targetted to as a group of servers. 

**Example:**
* `Group`: `edxapp_stage`
* `Group`: `edxapp_prod`
* `Group`: `edxapp_some_other_environment`
 
Additional tags can be added to AWS resources in the stack but they should not
be made necessary deployment or configuration.

## Ansible

Ansible is a configuration management tool that edX is evaluating to replace
the puppet environment that is currently being used for edX servers.

http://ansible.cc/docs

_Note: Because the directory structure changes in v1.2 we are using the dev
version instead of the official v1.1 release._


* __Hosts__ -  The ec2.py inventory script generates an inventory file where
  hosts are assigned to groups. Individual hosts can be targeted by the "Name"
  tag or the instance ID. I don't think there will be a reason to set host
  specific variables.
* __Groups__ - A Group name is an identifier that corresponds to a group of
  roles plus an identifier for the environment.  Example: *edxapp_stage*,
  *edxapp_prod*, *xserver_stage*, etc.  For the purpose of targetting servers
  for deployment groups are created automatically by the `ec2.py` inventory
  sript since these group names will map to the _Group_ AWS tag. 
* __Roles__  - A role will map to a single function/service that runs on
  server.

## Organization

### Secure vs. Insecure data

As a general policy we want to protect the following data:

* Usernames
* Public keys (keys are ok to be public, but can be used to figure out usernames)
* Hostnames
* Passwords, api keys

The following yml files and examples serve as templates that should be overridden with your own
environment specific configuration:

* vars in `secure_example/vars` 
* files in `secure_example/files` 

Directory structure for the secure repo:

```

ansible
├── files
├── keys
└── vars

```

The same directory structure, required yml files and files are 
in the secure_example dir:

```
secure_example/
├── files
├── keys
└── vars
```

The default `secure_dir` is set in `group_vars/all` and can be overridden by
adding another file in group_vars that corresponds to a deploy group name.


The directory structure should follow Ansible best practices.

http://ansible.cc/docs/bestpractices.html

* At the top level there are yml files for every group where a group name is an
  identifier that corresponds to a set of roles plus an environment.  
* The standard environments are _stage_ and _production_.
* Additional environments can be named as well, below an example is given
  called _custom_.


### Variables

* The ansible.cfg that is checked into the playbook directory has hash merging
  turned on, this allows us to to merge secure and custom data into the default
  variable definitions for every role.
* For example, `vars/lms_vars.yml` (variables needed for the lms role) sets the
  `env_config` which has keys that can be overridden by
  `vars/secure/edxapp_stage_vars.yml` for setting passwords and hostnames.  
* If needed, additional configuration can be layered, in the example
  `vars/secure/custom_vars.yml` changes some paramters that are set in
  `vars/secure/edxapp_stage_vars.yml`.

__TODO__: _The secure/ directories are checked into the public repo for now as an
example, these will need to be moved to a private repo or maintained outside of
github._

### Users and Groups

There are two classes of users, admins and environment users.

* The *admin_users* hash will be added to every server and will be put into a
  group that has admin bits.
* The *env_users* hash are the class of users that can be optionally included
  in one of the group-environment playbooks.


Example users are in the `vars/secure` directory:

* [*env_users* for staging environment](/vars/secure/edxapp_stage_users.yml)
* [*admin_users* will be realized on every server](/vars/secure/users.yml)


```
cloudformation_templates  <-- official edX cloudformation templates
    └── examples          <-- example templates
playbooks
 └──
     edxapp_prod.yml      <-- example production environment playbook
     edxapp_stage.yml     <-- example stage environment playbook
     edxapp_custom.yml    <-- example custom environment playbook
    ├── files             <-- edX cloudformation templates
    │   └── examples      <-- example cloudformation templates
    ├── group_vars        <-- var files that correspond to ansible group names (mapped to AWS tags)
    ├── keys              <-- public keys
    ├── roles             <-- edX services
    │   ├── common        <-- tasks that are run for all roles
    │   │   └── tasks
    │   ├── lms
    │   │   ├── tasks     <-- tasks that are run to setup an LMS
    │   │   ├── templates
    │   │   └── vars      <-- main.yml in this directory is auto-loaded when the role is included
    │   │
    │   └── nginx
    │       ├── handlers 
    │       ├── tasks
    │       ├── vars
    │       └── templates 
    │   (etc)
    └── vars             <-- public variable definitions
    └── secure_example   <-- secure variables (example)

```


### Installation

```
  mkvirtualenv ansible
  pip install -r ansible-requirements.txt
  util/sync_hooks.sh
```

### Launching example cloudformation stack - Working example

#### Provision the stack

  ```
  cd playbooks
  ansible-playbook  -vvv cloudformation.yml -i inventory.ini  -e 'region=<aws_region> key=<key_name> name=<stack_name> group=<group_name>'
  ```
  
* _aws_region_: example: `us-east-1`. Which AWS EC2 region to build stack in.
* _key_name_: example: `deploy`. SSH key name configured in AWS for the region
* _stack_name_: example: `EdxAppCustom`. Name of the stack, must not contain
  underscores or cloudformation will complain. Must be an unused name or
  otherwise the existing stack will update.
* _group_name_: example: `edxapp_stage`. The group name should correspond to
  one of the yml files in the `playbooks/`. Used for grouping hosts.

While this is running you see the cloudformation events in the AWS console as
the stack is brought up.  Loads the `playbooks/cloudformation.yml` template
which creates a single small EBS backed EC2 instance.  

_Note: You should read the output from ansible and not necessarily trust the
'ok'; failures in cloudformation provisioning (for example, in creating the
security group), may not cause ansible-playbook to fail._

See files/examples for
adding other components to the stack.

##### If ansible-playbook gives you import errors

Ansible really wants to call /usr/bin/python and if you have good virtualenv
hygeine, this may lead to ansible being unable to import critical libraries
like cloudfront. If you run into this problem, try exporting PYTHONPATH inside
your virtualenv and see if it runs better that way. E.g.:

  ```
  export PYTHONPATH=$VIRTUAL_ENV/lib/python2.7/site-packages/ 
  ansible-playbook playbooks/cloudformation.yml -i playbooks/inventory.ini
  ```

If that works fine, then you can add an export of PYTHONPATH to
`$VIRTUAL_ENV/bin/postactivate` so that you no longer have to think about it.
  
### Configure the stack

* Creates admin and env users
* Creates base directories
* Creates the lms json configuration files

Because the reference architecture makes use of an Amazon VPC, you will not be able
to address the hosts in the private subnets directly.  However, you can easily set 
up a transparent "jumpbox" so that for all hosts in your vpc, connections are 
tunneled.

Add something like the following to your `~/.ssh/config` file.

```
Host *.us-west-1.compute-internal
  ProxyCommand ssh -W %h:%p vpc-00000000-jumpbox
  IdentityFile /path/to/aws/key.pem
  ForwardAgent yes
  User ubuntu

Host vpc-00000000-jumpbox
  HostName 54.236.224.226
  IdentityFile /path/to/aws/key.pem
  ForwardAgent yes
  User ubuntu
```

This assumes that you only have one VPC in the ```us-west-1``` region
that you're trying to ssh into.  Internal DNS names aren't qualified
any further than that, so to support multiple VPC's you'd have to get
creative with subnets, for example ip-10-1 and ip-10-2...

Test this by typing `ssh ip-10-0-10-1.us-west-1.compute.internal`, 
(of course using a hostname exists in your environment.)  If things 
are configured correctly you will ssh to 10.0.10.1, jumping 
transparently via your basion host.

Assuming that the edxapp_stage.yml playbook targets hosts in your vpc
for which there are entiries in your `.ssh/config`, do the 
following to run your playbook.

```
  cd playbooks
  ansible-playbook -v --user=ubuntu edxapp_stage.yml -i ./ec2.py -c ssh
```

*Note: this assumes the group used for the edx stack was "edxapp_stage"*

