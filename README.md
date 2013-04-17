# Configuration Management

## Ansible

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


  
  
