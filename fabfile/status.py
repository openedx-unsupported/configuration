from fabric.api import task, sudo, abort, parallel, runs_once, execute
from fabric.api import settings, hide
from fabric.operations import put
from fabric.utils import fastprint
from safety import noopable
from fabric.colors import blue, red
from fabric.contrib import console
from output import unsquelched
from timestamps import no_ts
from choose import multi_choose_with_input
import json
import tempfile

status_file = '/opt/wwc/status_message.json'


@task(default=True)
@runs_once
def status():
    """
    Drops {0} which is a json formatted file that contains a
    status message that will be displayed to all users on the
    on the courseware for a single course or for all courses
    if 'global' is set.

    Message(s) are entered or removed interactively on the console.

    Example usage:

        $ fab groups:prod_edx status

    """.format(status_file)

    with hide('running', 'stdout', 'stderr', 'warnings'):
        env_json = sudo("cat /opt/wwc/lms-xml.env.json")
    course_listings = json.loads(env_json)['COURSE_LISTINGS']
    course_ids = [course_id for course_list in course_listings.itervalues()
                  for course_id in course_list]
    course_ids = ['global'] + course_ids

    with no_ts():

        course_status = None
        with settings(warn_only=True):
            cur_status = noopable(sudo)('cat {0}'.format(status_file))
        try:
            course_status = json.loads(cur_status)
            # add empty entries for courses not in the list
            empty_entries = set(course_ids) - set(course_status.keys())
            course_status.update({entry: '' for entry in list(empty_entries)})

        except ValueError:
            fastprint(red("Not a valid json file, overwritting\n"))
        if course_status is None:
            course_status = {course: '' for course in course_ids}
        new_status = multi_choose_with_input(
                'Set the status message, blank to disable:',
                course_status)

        if new_status is not None:
            # remove empty entries
            new_status = {entry: new_status[entry]
                    for entry in new_status if len(new_status[entry]) > 1}
            with unsquelched():
                if not console.confirm(
                        'Setting new status message:\n{0}'.format(
                            blue(str(new_status), bold=True)),
                            default=False):
                    abort('Operation cancelled by user')

                with tempfile.NamedTemporaryFile(delete=True) as f:
                    f.write(json.dumps(new_status))
                    f.flush()
                    execute(update_status, f.name)
        else:
            abort('Operation cancelled by user')


@task
@runs_once
def remove():
    """
    Removes {0}, a status banner that is displayed to all
    users on the front page.
    """.format(status_file)

    with unsquelched():
        if not console.confirm(
                blue('Remove /opt/wwc/status_message.html?', bold=True)):
            abort('Operation cancelled by user')
        execute(remove_status)


@task
@parallel
def remove_status():
    noopable(sudo)('rm -f {0}'.format(status_file))


@task
@parallel
def update_status(fjson):
    print status_file
    noopable(put)(fjson, status_file, use_sudo=True)
