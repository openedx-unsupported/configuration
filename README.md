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
  ansible-playbook test.yaml -i ec2.py --private-key=/path/to/deployment.pem
  ```




  
  
