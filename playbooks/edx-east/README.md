This directory contains playbooks used by edx-east
for provisioning

```
ansible-playbook -c ssh -vvv --user=ubuntu <playbook> -i ./ec2.py  -e 'secure_dir=path/to/configuration-secure/ansible'
```

Historical note: "edx-east" represents the edX organization in Cambridge, MA. At one point, an "edx-west" notion existed - a name which represented Stanford edX developers.
