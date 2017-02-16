This directory contains playbooks used by edx-east
for provisioning

```
ansible-playbook -c ssh -vvv --user=ubuntu <playbook> -i ./ec2.py  -e 'secure_dir=path/to/configuration-secure/ansible'
```
