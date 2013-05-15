import os
from fabric.api import run, settings, hide, sudo
from collections import defaultdict
import yaml
import re

MIN_REVISION_LENGTH = 7


class PackageInfo:

    def __init__(self):
        path = os.path.abspath(__file__)
        with open(os.path.join(
                os.path.dirname(path), '../package_data.yaml')) as f:
            package_data = yaml.load(f)
        # exhaustive list of MITx repos
        self.repo_dirs = package_data['repo_dirs']
        self.cmd_list = {
                'pre': package_data['pre_checkout_regex'],
                'post': package_data['post_checkout_regex']}
        self.service_repos = package_data['service_repos']

    def repo_from_name(self, name):
        repos = []
        for repo_root in self.repo_dirs:
            if os.path.basename(repo_root) == name:
                repos.append(self.repo_dirs[repo_root])

        if len(repos) > 1:
            raise Exception['Multiple repos found for name']
        elif len(repos) == 0:
            raise Exception['Repo not found for name']
        else:
            return repos[0].split('/')[1]

    def org_from_name(self, name):
        repos = []
        for repo_root in self.repo_dirs:
            if os.path.basename(repo_root) == name:
                repos.append(self.repo_dirs[repo_root])

        if len(repos) > 1:
            raise Exception['Multiple repos found for name']
        elif len(repos) == 0:
            raise Exception['Repo not found for name']
        else:
            return repos[0].split('/')[0]



    def pre_post_actions(self, pkgs):
        """
        Returns a dictionary containing a list of
        commands that need to be executed
        pre and post checkout for one or more package names.

        return({
                'pre': [ 'cmd1', 'cmd2', ... ],
                'post': [ 'cmd1', 'cmd2', ... ]
            })

        """

        cmds = defaultdict(list)
        for stage in ['pre', 'post']:
            for regex, cmd_templates in self.cmd_list[stage]:
                for pkg in pkgs:
                    match = re.match(regex, pkg)
                    if match is None:
                        continue

                    cmds[stage].extend(
                        cmd.format(*match.groups(), **match.groupdict())
                        for cmd in cmd_templates
                        if cmd not in cmds[stage]
                    )
        return(cmds)

    def installed_packages(self):
        """
        Returns the list of PackageDescriptors for the packages
        installed on the system.

        This is determined by looking at every package directory
        we know about and checking its revision.
        """

        with settings(hide('running'), warn_only=True):
            revisions = sudo(
            """
            for path in {0}; do
                if [[ -d "$path/.git" ]]; then
                    echo $path $(cd $path && git rev-parse HEAD 2>/dev/null)
                fi
            done
            """.format(' '.join(self.repo_dirs))).split('\n')
        packages = [revline.strip().split(' ') for revline in revisions
                if ' ' in revline.strip()]

        return [PackageDescriptor(os.path.basename(path), revision)
                        for path, revision in packages]


class PackageDescriptor(object):

    def __init__(self, name, revision):

        if revision != 'absent' and len(revision) < MIN_REVISION_LENGTH:
            raise Exception("Must use at least {0} characters "
            "in revision to pseudo-guarantee uniqueness".format(
                MIN_REVISION_LENGTH))

        self.name = name

        # Find the repo_root by name
        # This assumes that basename(repo_root) is unique
        # for all repo_roots.  If this is not true an exception
        # will be raised

        pkg_info = PackageInfo()
        repo_roots = []
        for repo_dir in pkg_info.repo_dirs.keys():
            if os.path.basename(repo_dir) == name:
                repo_roots.append(repo_dir)
        if len(repo_roots) != 1:
            raise Exception("Unable to look up directory for repo")

        self.repo_root = repo_roots[0]
        self.repo_name = pkg_info.repo_dirs[self.repo_root].split('/')[1]
        self.repo_org = pkg_info.repo_dirs[self.repo_root].split('/')[0]
        self.revision = revision
