# Configuration Management

## Ansible

Ansible is a configuration management tool that edX is evaluating to replace the puppet environment 
that was used for MITx and edX prior to going open source.

http://ansible.cc/docs



## Directory Structure

The directory structure should follow Ansible best practices.

http://ansible.cc/docs/bestpractices.html



* Hosts -  The ec2.py inventory script generates an inventory file where hosts are assigned to groups. 
           Individual hosts can be targeted by the "Name" tag or the instance ID. 
           I don't think there will be a reason to set host specific variables.
* Groups - Groups are created automatically where hosts can be targeted by tags, security groups, region, etc.
           In the edX context a group would be a set of machines that are deployed to that have one or more
           roles. 
* Roles  - A role will map to a single function/service that runs on server.



```

ec2.py                    # inventory script for creating groups from ec2 tags

group_vars/
   all                    # assign any variables that are common to all edX groups
   tag_group_edxapp       # a variable set to true for every group of machines in the 
   tag_group_xserver      # edX infrastructure
   tag_group_worker
   (etc..)

site.yml                  # master playbook, this will include all groups

edxapp.yml                # defines what roles will be configured for a group of machines 
xserver.yml               
worker.yml
(etc..)

roles/
    common/               # tasks that are common to all roles 
        tasks/            #
            main.yml      #  <-- tasks file can include smaller files if warranted
        handlers/         #
            main.yml      #  <-- handlers file
        templates/        #  <-- files for use with the template resource
            ntp.conf.j2   #  <------- templates end in .j2
        files/            #
            bar.txt       #  <-- files for use with the copy resource
        secure/           #  <-- Not checked in, will have secure data that cannot be public
  
    lms/                  # same structure as "common" was above
    xserver/              # ""
    worker/               # ""
    (etc..)
    
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

1. Come up with a scheme to separate sensitive data
2. Create templates for /opt/wwc/lms-{env,auth}.json, these files are read by mitx/lms/envs/aws.py
3. Set up virtualenv (currently configured to by default be in /opt/edx)
4. Setup and configure rsyslog and logrotate
5. Setup and configure nginx/apache
5. Create upstart script for the lms service
6. Setup and configure local mongo/mongoHQ
7. Setup and configure local sqlite/RDS
8. Create deploy playbook for git deploy


  
  
