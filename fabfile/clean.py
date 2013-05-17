from fabric.api import sudo, task, parallel
from safety import noopable
from modifiers import rolling

@task
@parallel
def apt_get_clean():
    """ Runs apt-get clean on a remote server """
    noopable(sudo)('apt-get clean')   

@task
@rolling
def mako_template_cache():
    noopable(sudo)('service gunicorn stop')
    noopable(sudo)('rm -rf /tmp/tmp*mako')
    noopable(sudo)('service gunicorn start')
