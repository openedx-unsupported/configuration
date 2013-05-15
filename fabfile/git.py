import itertools
import os
import re
import socket

from functools import partial
from dogapi import dog_stats_api
from fabric.api import task, sudo, runs_once, execute
from fabric.api import cd, env, abort, parallel, prefix
from fabric.colors import white, green, red
from fabric.contrib import console, files
from fabric.operations import put
from fabric.utils import fastprint
from multiprocessing import Manager

from .choose import multi_choose
from .metrics import instance_tags_for_current_host
from .modifiers import rolling
from .output import notify
from .packages import PackageInfo
from .safety import noopable
from .timestamps import no_ts

REPO_URL = 'git@github.com:{}/{}'
REPO_DIRNAME = '/opt/wwc'
GIT_USER = "www-data"


@task(default=True, aliases=['deploy'])
@runs_once
def default_deploy(**pkg_revs):
    """
    Deploys the cached or specified packages to the
    specified hosts

    Packages are installed while the server is out of the
    loadbalancer pool
    """

    if pkg_revs:
        execute('cache.from_strings', **pkg_revs)
    if socket.gethostname() != 'buildmaster-001':
        execute('git.confirm')
    execute('git.deploy')
    execute('locks.remove_all_locks')


def diff_link(pkg_org, pkg_name, old_revision, new_revision):
    if '~' in pkg_name:
        pkg_name = re.sub('~.*', '', pkg_name)

    return 'Show on github: https://github.com/{org}/{pkg}/compare/{old}' \
           '...{new}'.format(org=pkg_org,
                             pkg=pkg_name,
                             old=old_revision,
                             new=new_revision)


@task
@parallel
def diff_installed_packages(results):
    pkg_info = PackageInfo()
    # { basename(repo_dir): PackageDescriptor()) ... }
    old_pkgs = {pkg.name: pkg
                for pkg in pkg_info.installed_packages()}
    change_list = []
    for new_pkg in env.package_descriptors:
        if new_pkg.name in old_pkgs:
            old = old_pkgs[new_pkg.name].revision
            new = new_pkg.revision
            change_list.append((new_pkg.name, old, new))
        else:
            change_list.append((new_pkg.name, None, new_pkg.revision))
    results.append((tuple(change_list), env.host))


@task
@runs_once
def confirm():
    """
    Generate diffs comparing what's installed to what's about to be installed,
    and ask the user to confirm to continue.

    Answering no aborts the entire operation
    """
    execute('locks.wait_for_all_locks')
    # turn off timestamps for the confirm prompt
    with no_ts():
        manager = Manager()
        diffs = manager.list()
        execute(diff_installed_packages, diffs)

        local_diffs = list(diffs)

        def sort_key(diff):
            return diff[0]

        local_diffs.sort(key=sort_key)

        if not local_diffs:
            execute('locks.remove_all_locks')
            abort("Nothing to deploy")

        choices = set()
        pkg_info = PackageInfo()
        servers_to_update = []
        for key, group in itertools.groupby(local_diffs, key=sort_key):
            servers = [d[1] for d in group]
            servers_to_update.extend(servers)
            for pkg, old, new in key:
                choices.add(pkg)
                notify(
                    "    {name}: {diff}".format(
                        name=pkg,
                        old=old,
                        new=new,
                        diff=diff_link(pkg_info.org_from_name(pkg),
                                       pkg_info.repo_from_name(pkg), old, new),
                    ),
                    show_prefix=False
                )

        choices = list(choices)

        if len(choices) > 1:
            selection = multi_choose("Select one or more item numbers to mark"
                                     "them with a '*' for deployment.\n"
                                     "Note: none are selected by default.\n"
                                     "Select 'c' to deploy "
                                     "the items that are marked with a '*'.",
                                     choices)
        else:
            selection = choices

        if not selection:
            notify('Removing all locks and aborting')
            execute('locks.remove_all_locks')
            abort('Operation cancelled by user')

        pre_post = display_pre_post(selection)
        env.pre_post = pre_post
        notify("{noop}Updating servers [{servers}]:".format(
            servers=", ".join(servers_to_update),
            noop="[noop] " if env.noop else ''
        ), show_prefix=False)

        if not console.confirm(
                white('Please confirm the pre and post actions above',
                      bold=True),
                default=True):
            execute('locks.remove_all_locks')
            abort('Operation cancelled by user')

        env.package_descriptors = [
            pkg for pkg in env.package_descriptors if pkg.name in selection]


def display_pre_post(choices):

    """
    Displays list of pre and post checkout commands,
    returns the list of commands in a dictionary

        return({
                'pre': [ 'cmd1', 'cmd2', ... ],
                'post': [ 'cmd1', 'cmd2', ... ]
            })

    """

    pkg_info = PackageInfo()
    pre_post = pkg_info.pre_post_actions(choices)

    for stage in ['pre', 'post']:
        if pre_post[stage]:
            fastprint(green('{0}-checkout commands:\n'.format(stage),
                      bold=True) + green('  -> ') + green('\n  -> '.join(
                      pre_post[stage])) + white('\n\n'))
        else:
            fastprint(green('WARNING', bold=True) +
                      green(' - no {0}-checkout commands for this set '
                      'of packages : '.format(stage, choices)) +
                      white('\n\n'))
    return pre_post


@task
@rolling
def deploy(auto_migrate=False):
    """
    Deploys the cached packages to the specified hosts.
    Packages are installed while the server is out of the loadbalancer pool
    """

    packages = env.package_descriptors

    # If these are not defined it means that the confirm
    # step was skipped, in this case we figure out pre and
    # post steps here
    if not hasattr(env, 'pre_post'):
        pkg_config = PackageInfo()
        env.pre_post = pkg_config.pre_post_actions([pkg.name
                                                   for pkg in packages])

    contains_content = any(pkg.name.startswith('content') for pkg in packages)
    contains_code = not all(pkg.name.startswith('content') for pkg in packages)

    base_tags = [
        'deploying_to_host:' + env.host,
    ] + instance_tags_for_current_host()

    if contains_content:
        base_tags.append('type:content')
    if contains_code:
        base_tags.append('type:code')

    package_tags = base_tags + ['package:' + pkg.name for pkg in packages]
    metric_name = 'fabric.deployment'

    # pre checkout commands
    with dog_stats_api.timer(metric_name, tags=package_tags +
                             ['step:pre_commands']):
        with prefix("export GIT_SSH=/tmp/git.sh"):
            for cmd in env.pre_post['pre']:
                noopable(sudo)(cmd)

    put(os.path.join(os.path.dirname(__file__), 'git.sh'),
        '/tmp/git.sh', mode=0755, use_sudo=True)
    for pkg in packages:
        existing_repo = files.exists(pkg.repo_root, use_sudo=True)

        repo_tags = base_tags + [
            'package:' + pkg.name,
            'existance:' + 'existing' if existing_repo else 'absent',
        ]

        with dog_stats_api.timer(metric_name, tags=repo_tags + ['step:clone']):
            if existing_repo:
                if not files.exists(os.path.join(pkg.repo_root, '.git'),
                                    use_sudo=True):
                    raise Exception("Repo root not a git repo - {0}".format(
                        os.path.join(pkg.repo_root, '.git')))
                with cd(pkg.repo_root):
                    if pkg.revision == 'absent':
                        noopable(sudo)('rm -rf {0}'.format(pkg.repo_root))
                    else:
                        checkout(pkg.revision)
            else:
                with cd(os.path.dirname(pkg.repo_root)):
                    if pkg.revision != 'absent':
                        clone(pkg.repo_org, pkg.repo_name, pkg.name, pkg.revision)
            if '~' in pkg.name:
                _update_course_xml(pkg, pkg.name.split('~')[1])

        with dog_stats_api.timer(metric_name, tags=repo_tags +
                                 ['step:requirements']):
            _install_requirements(pkg)
            _install_gemfile(pkg)
            _install_npm_package(pkg)

        with dog_stats_api.timer(metric_name, tags=repo_tags + ['step:fact']):
            # drop a file for puppet so it knows that
            # code is installed for the service
            with cd('/etc/facter/facts.d'):
                pkg_config = PackageInfo()
                if pkg.repo_name in pkg_config.service_repos:
                    # facts can't have dashes so they are converted
                    # to underscores
                    noopable(sudo)(
                        'echo "{0}_installed=true" > {0}_installed.txt'.format(
                        pkg.repo_name.replace("-", "_")))

    with dog_stats_api.timer(metric_name, tags=package_tags +
                             ['step:pkg_version']):
        pkg_version()

    with dog_stats_api.timer(metric_name, tags=package_tags +
                             ['step:post_commands']):
        # post checkout commands
        with prefix("export GIT_SSH=/tmp/git.sh"):
            for cmd in env.pre_post['post']:
                noopable(sudo)(cmd)

    if 'mitx' in [pkg.name for pkg in packages]:
        # do not slow down content deploys by checking
        # for migrations
        execute('migrate_check.migrate_check', auto_migrate)


@task
def pkg_version():
    """
    Drops an html/json version file on the remote system
    """
    path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(path, '../version-script/version.py')) as f:
        put(f, '/tmp/version.py', use_sudo=True)

    noopable(sudo)('/usr/bin/python /tmp/version.py')


@task
def clone(repo_org, repo_name, name, revision):
    """
    Parameters:
        repo_name: github organization
        repo_name: github repo name
        name: basename(repo_dir) ex: content-mit-600x~Fall_2012
        revision: commit hash
    """

    with no_ts():
        with prefix("export GIT_SSH=/tmp/git.sh"):
            noopable(sudo)("git clone {} {}".format(
                REPO_URL.format(repo_org, repo_name), name))
            with cd(name):
                noopable(sudo)("git reset --hard {0}".format(revision))
                if files.exists('.gitmodules', use_sudo=True):
                    noopable(sudo)("git submodule update --init")
                noopable(sudo)("chown -R {0}:{0} .".format(GIT_USER))


@task
def checkout(revision):
    """
    Parameters:
        revision: commit hash
    """

    with no_ts():
        with prefix("export GIT_SSH=/tmp/git.sh"):
            noopable(sudo)("git remote prune origin")
            noopable(sudo)("git fetch origin")
            noopable(sudo)("git reset --hard {0}".format(revision))
            if files.exists('.gitmodules', use_sudo=True):
                noopable(sudo)("git submodule update --init")
            noopable(sudo)("chown -R {0}:{0} .".format(GIT_USER))


def _update_course_xml(pkg, root):
    """
    Parameters:
        pkg: a single package descriptor
        root: a root that must exist in the roots/ folder
    """
    with cd(pkg.repo_root):
        if files.exists(
                os.path.join(pkg.repo_root, 'roots/{0}.xml'.format(root)),
                use_sudo=True):
            noopable(sudo)('rm -f course.xml && '
                           'ln -s roots/{0}.xml course.xml'.format(root))
        else:
            abort(red("There is a '~' in {0} but there is no roots/{1}.xml "
                      "file in the repo!".format(pkg.name, root)))


def _install_requirements(pkg):
    """
    Parameters:
        pkg: single package descriptor

    install pre-requirements and requirements
    if they exists for the repo.
    will not run pip install if the requirements file
    has not changed since the last run
    """

    def pip_install(file):
        with prefix("export GIT_SSH=/tmp/git.sh"):
            with prefix('source /opt/edx/bin/activate'):
                with prefix('export PIP_DOWNLOAD_CACHE=/tmp/pip_download_cache'):
                    noopable(sudo)('pip install --exists-action w -r {0}'.format(file))

    # Run old-style requirements
    _run_if_changed(pkg, 'pre-requirements.txt', partial(
                    pip_install, 'pre-requirements.txt'))
    _run_if_changed(pkg, 'requirements.txt', partial(
                    pip_install, 'requirements.txt'), 'cat *requirements.txt')

    # Run new-style requirements
    _run_if_changed(pkg, 'requirements/base.txt', partial(
                    pip_install, 'requirements/base.txt'), 'cat requirements/*.txt')
    _run_if_changed(pkg, 'requirements/post.txt', partial(
                    pip_install, 'requirements/post.txt'))


@task
@runs_once
def deploy_with_puppet():
    execute('git.confirm')
    execute(_deploy_with_puppet)
    execute('locks.remove_all_locks')


@task
@rolling
def _deploy_with_puppet():
    execute('puppet')
    execute('git.deploy')


def _install_gemfile(pkg):
    """
    Parameters:
        pkg: single package descriptor

    Installs the Gemfile from the repo, if it exists.
    Will not run if the Gemfile
    has not changed since the last run
    """
    def bundle_install():
        with prefix('export PATH=/opt/www/.rbenv/bin:$PATH'):
            with prefix('RBENV_ROOT=/opt/www/.rbenv'):
                with prefix('which rbenv'):
                    with prefix('eval "$(rbenv init -)"'):
                        noopable(sudo)('gem install bundler')
                        noopable(sudo)('bundle install --binstubs')

    _run_if_changed(pkg, 'Gemfile', bundle_install)


def _install_npm_package(pkg):
    """
    Parameters:
        pkg: single package descriptor

    Installs the package.json from the repo, if it exists.
    Will not run if the package.json has not changed since
    the last run
    """
    def package_install():
        noopable(sudo)('npm install')

    _run_if_changed(pkg, 'package.json', package_install)


def _run_if_changed(pkg, file, command, contents_command=None):
    """
    Runs command if the contents of file
    inside pkg have changed since the last time the command was run.
    Commands are executed inside pkg.repo_root
    """
    if contents_command is None:
        contents_command = 'cat ' + file

    with cd(pkg.repo_root):
        path = os.path.join(pkg.repo_root, file)
        if files.exists(path, use_sudo=True):
            prev_md5_file = '/var/tmp/{0}-{1}.md5'.format(
                pkg.repo_name.replace('/', '-'), file.replace('/', '-'))
            md5_command = '{} | /usr/bin/md5sum'.format(contents_command)
            if files.exists(prev_md5_file, use_sudo=True):
                cur_md5 = sudo(md5_command)
                prev_md5 = sudo('cat {0}'.format(prev_md5_file))
                if cur_md5 == prev_md5:
                    return

            command()
            noopable(sudo)('{} > {}'.format(md5_command, prev_md5_file))
