import yaml
import ConfigParser
import argparse
import os
import glob


__author__ = 'e0d'


class AnsibleDependencyAnalyzer:
    """
    An utility class for ansible roles and playbooks that returns a list of included roles for a given starting
    point or the files associated with those roles.

    For example:

    python ansible-deps.py --playbook ../docker/plays/edxapp.yml --output-role-files

    ./roles/common_vars/tasks/main.yml
    ./roles/user/templates/restricted.sudoers.conf.j2
    ./roles/edxapp_common/defaults/main.yml
    ./roles/edxapp/tasks/service_variant_config.yml
    ./roles/common_vars/defaults/main.yml
    ./roles/common/meta/main.yml
    ...

    """

    def __init__(self):
        self.ansible_config = self._load_ansible_config()

    def get_roles_by_playbook(self, playbook_path):
        """
        Starts from a playbook and finds all roles included in all plays as well as roles
        included via meta/main.yml includes of directly included roles.  Returns the set of roles.

        TODO: make analysis recursive

        :param playbook_path:
        :return:
        """
        roles = set()

        with (open(playbook_path, 'r')) as yaml_file:
            playbook = yaml.load(yaml_file)

        for play in playbook:
            roles |= self.get_roles_by_roles(play['roles'])

        return list(roles)

    def get_roles_by_roles(self, roles):
        _roles = set()

        for role in roles:
            resolved_name = self._get_role_name(role)
            _roles.add(resolved_name)
            _roles |= set(self.get_roles_by_role(resolved_name))

        return _roles

    def get_roles_by_role(self, role_name):
        """
        For a given role_name, finds it's included dependent roles in meta/main.yml. Roles are resolved
        using ansible.cfg and a path relative roles directory, if available.
        :param role_name:
        :return:
        """
        role_dir = self._locate_role_dir(role_name)
        meta_file = role_dir + "/meta/main.yml"

        role_dependencies = []

        if not os.path.exists(meta_file):
            return role_dependencies

        with (open(meta_file, 'r')) as yaml_file:
            role_meta = yaml.load(yaml_file)

        for k in role_meta['dependencies']:
            role_dependencies.append(self._get_role_name(k))

        return role_dependencies

    def role_to_files(self, role_name):
        role_dir = self._locate_role_dir(role_name)
        files = []
        files.extend(glob.iglob(role_dir + "/*/*.y*ml"))
        files.extend(glob.iglob(role_dir + "/*/*.j2"))
        return files

    def _get_role_name(self, role):
        """
        Resolves a role name from either a simple declaration or a dictionary style declaration.

        A simple declaration would look like:
        - foo

        A dictionary style declaration would look like:
        - role: rbenv
          rbenv_user: "{{ forum_user }}"
          rbenv_dir: "{{ forum_app_dir }}"
          rbenv_ruby_version: "{{ forum_ruby_version }}"

        :param role:
        :return:
        """
        if isinstance(role, dict):
            return role['role']
        elif isinstance(role, basestring):
            return role
        return None

    def _locate_role_dir(self, role_name):

        # start with a path relative roles directory
        role_paths = ["./roles"]

        # include path specified in ansible.cfg
        cfg_paths = self.ansible_config.get("defaults", "roles_path")
        role_paths.extend(cfg_paths.split(':'))

        for path in role_paths:
            if os.path.exists(path + "/" + role_name):
                return path + "/" + role_name

    def _load_ansible_config(self):

        ansible_cfg = os.getcwd() + "/ansible.cfg"

        if os.path.exists(ansible_cfg):
            config = ConfigParser.ConfigParser()
            config.read(ansible_cfg)
        else:
            raise EnvironmentError("Cannot find ansible.cfg file for resolve role paths")

        return config


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="List roles included in either an ansible play or an ansible role.")

    target_group = parser.add_mutually_exclusive_group()

    target_group.add_argument("--playbook", default=None,
                              help="The fully qualified or relative path to the playbook to analyze")
    target_group.add_argument("--role", default=None,
                              help="The name of the role to analyze, assumes it is on the role path, "
                                   "defined either via ansible.cfg in the current working directory "
                                   "or a roles directory relative to the current working directory.")

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output-roles", action="store_true", default=None,
                              help="Output the set of role names.")
    output_group.add_argument("--output-role-files", action="store_true", default=None,
                              help="Output the set of role related files.")

    args = parser.parse_args()

    ag = AnsibleDependencyAnalyzer()

    roles = []

    if args.playbook:
        roles = ag.get_roles_by_playbook(args.playbook)
    elif args.role:
        roles = ag.get_roles_by_role(args.role)

    if args.output_roles:
        for role in roles:
            print role
    elif args.output_role_files:
        unique_files = set()
        for role in roles:
            unique_files |= set(ag.role_to_files(role))
        for unique_file in unique_files:
            print unique_file