# Stanford Ansible Configuration Files

This directory has the live playbooks that we use here at Stanford to
maintain our instance of OpenEdX at [class.stanford.edu][c].  We check
it in to this public repo since we think that others might benefit from
seeing how we are configured.

  [c]: https://class.stanford.edu/

That said, we haven't documented things in here well, so we have no
expectation that others will be able to make enough sense of this to
give us useful contributions back.  Generally a PR affecting files in
here will be ignored / rejected.

This README is a useful proximate place to keep commands.  But it is 
a public repo so we shouldn't store anything confidential in here.

Other install docs:

- Giulio's install doc [here][1].

  [1]: https://docs.google.com/document/d/1ZDx51Jxa-zffyeKvHmTp_tIskLW9D9NRg9NytPTbnrA/edit#heading=h.iggugvghbcpf


## Ansible Commands - Prod

Generally we do installs as the "ubuntu" user.  You want to make
sure that the stanford-deploy-20130415 ssh key is in your ssh agent.

    ANSIBLE_CONFIG=prod-ansible.cfg ANSIBLE_EC2_INI=prod-ec2.ini ansible-playbook prod-app.yml -e "machine=app4" -u ubuntu -c ssh -i ./ec2.py

Some specifics:

* To do database migrations, include this: ```-e "migrate_db=yes"```.  The default
  behavior is to not do migrations.

* To hit multiple machines the use this: ```-e "machine=app(1|2|4)"```.
  Use multiple separate "-e" options to specify multiple vars on the
  command line.

* Usually I do with the ```--list-hosts``` option first to verify that I'm
  doing something sane before actually running.

* To install the utility machines, substitute ```prod-worker.yml```.  Those
  are also parameterized on the take the machine variable (util1, util(1|2),
  and so forth).


## Ansible Commands - Stage

Command is:

    ANSIBLE_CONFIG=stage-ansible.cfg ANSIBLE_EC2_INI=stage-ec2.ini ansible-playbook stage-app.yml -e "machine=app1" -u ubuntu -c ssh -i ./ec2.py


