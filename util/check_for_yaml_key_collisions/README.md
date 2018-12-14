Finds if there are colliding keys in a set of yaml files that might collide when ansible merges happen

USAGE:
python check_for_yaml_key_collisions/check_for_yaml_key_collisions.py --files configuration/docker/build/edxapp/ansible_overrides.yml --files configuration/docker/build/edxapp/devstack.yml --files configuration/docker/build/devstack/ansible_overrides.yml