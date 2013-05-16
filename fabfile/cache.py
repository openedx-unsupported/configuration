from fabric.api import task, runs_once, env, serial, puts, settings
from fabric.utils import fastprint
from fabric.colors import blue, red, white

from output import notify
from packages import PackageDescriptor
from output import unsquelched
from hosts import exemplar
from ssh_tunnel import setup_tunnel
from packages import PackageInfo


@task
@runs_once
def from_exemplar(**tags):
    """
    Cache the set of packages installed on one host from the specified tags.

    """
    host_string = setup_tunnel([exemplar(**tags)])[0]
    with settings(host_string=host_string):
        installed_packages()


@task
@runs_once
def limit_prefix(*prefix_list):
    """
    Limits cached packages to those that
    match one or more prefix strings
    """
    env.package_descriptors = filter(
        lambda pkg: any(pkg.name.startswith(prefix)
                        for prefix in prefix_list), env.package_descriptors)


@task(default=True)
@runs_once
def installed_packages(prefix=None):
    """
    Cache the set of packages installed on the selected host.
    """
    pkg_info = PackageInfo()
    env.package_descriptors = [
        package for package in pkg_info.installed_packages()
        if prefix is None or package.name.startswith(prefix)
    ]


@task
@runs_once
def from_strings(**pkg_revs):
    """
    Cache packages based on strings, that can be either checked with confirm
    or deployed with deploy.

    Each named argument specifies a package by name, and the revision of
    the package to deploy
    """
    packages = []
    for pkg_name, pkg_rev in pkg_revs.items():
        packages.append(PackageDescriptor(pkg_name, pkg_rev))

    env.package_descriptors = packages

    notify(env.package_descriptors)


@task
@runs_once
def from_stdin(prefix=None):
    """
    Cache a list of packages from stdin.
    Package names must start with prefix, if specified (any that don't
    will be skipped). Package names and revisions should be separated
    by = signs, and should be one per line.
    """

    if prefix:
        prefix_msg = white('pkg_name', bold=True) + white(
            ' must start with ') + blue(prefix)
    else:
        prefix_msg = ''
    fastprint('\n')
    fastprint('\n'.join([
        white('Please enter pkg_name=pkg_rev, one per line\n', bold=True),
        white('pkg_rev', bold=True) + white(' is a git revision hash'),
        prefix_msg,
        white('Complete your selections by entering a blank line.'),
    ]))
    fastprint('\n\n')

    packages = {}
    while True:
        line = raw_input("> ")
        if not line:
            break

        if '=' not in line:
            fastprint(red("Expected = in '{line}'. Skipping...".format(
                          line=line)) + white('\n'))
            continue

        pkg_name, _, pkg_rev = line.partition('=')
        pkg_name = pkg_name.strip()
        pkg_rev = pkg_rev.strip()

        if prefix and not pkg_name.startswith(prefix):
            fastprint(red("'{0}' does not start with '{1}'".format(
                          pkg_name, prefix)) + white('\n'))
            continue

        packages[pkg_name] = pkg_rev

    from_strings(**packages)


@task
@serial
@runs_once
def prompt(*pkg_names):
    packages = {}
    with unsquelched():
        puts("Please supply git revisions to "
             "deploy for the following packages:")
        for pkg in pkg_names:
            packages[pkg] = raw_input("{pkg} = ".format(pkg=pkg)).strip()

        from_strings(**packages)
