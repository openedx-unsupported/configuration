This doc is a useful place to keep commands in a handy place.  Keep
in mind that this is a public repo so we shouldn't store anything
confidential in here.

Other install docs:

- Giulio's install doc [here][1].

  [1]: https://docs.google.com/document/d/1ZDx51Jxa-zffyeKvHmTp_tIskLW9D9NRg9NytPTbnrA/edit#heading=h.iggugvghbcpf


Ansible Commands - Prod
-----------------------

Generally we do installs as the "ubuntu" user.  You want to make
sure that the stanford-deploy-20130415 ssh key is in your ssh agent.

    ANSIBLE_EC2_INI=ec2.ini ansible-playbook prod-log.yml -u ubuntu -c ssh -i ./ec2.py


Ansible Commands - Stage
------------------------

Verify that you're doing something reasonable:

    ANSIBLE_CONFIG=stage-ansible.cfg ANSIBLE_EC2_INI=ec2.ini ansible-playbook stage-app.yml -u ubuntu -c ssh -i ./ec2.py --list-hosts

Verify that you're doing something reasonable:

    ANSIBLE_CONFIG=stage-ansible.cfg ANSIBLE_EC2_INI=ec2.ini ansible-playbook stage-app.yml -u ubuntu -c ssh -i ./ec2.py



