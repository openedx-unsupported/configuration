from fabric.api import task, sudo, runs_once, prefix, hide, abort
from fabric.contrib import console
from fabric.colors import white, green
from .safety import noopable


@task()
@runs_once
def migrate_check(auto_migrate=False):
    """
    Checks to see whether migrations need to be run,
    if they do it will prompt to run them before
    continuing.

    looks for " - Migrating" in the output of
    the dry run

    """

    migration_cmd = "/opt/edx/bin/django-admin.py migrate --noinput " \
                    "--settings=lms.envs.aws --pythonpath=/opt/wwc/edx-platform"

    with prefix("export SERVICE_VARIANT=lms"):
        with hide('running', 'stdout', 'stderr', 'warnings'):
            dryrun_out = sudo(migration_cmd + " --db-dry-run", user="www-data")
        migrate = False
        for chunk in dryrun_out.split('Running migrations for '):
            if 'Migrating' in chunk:
                print "!!! Found Migration !!!\n" + chunk
                migrate = True
        if migrate:
            if auto_migrate or console.confirm(
                    green(migration_cmd) + white('\n') +
                    white('Run migrations? ', bold=True), default=True):
                noopable(sudo)(migration_cmd, user='www-data')
