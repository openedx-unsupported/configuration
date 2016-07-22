import json
import os
from os.path import exists, dirname, splitext, basename
from datetime import datetime

"""
Originally written by 'Jharrod LaFon'
#https://github.com/jlafon/ansible-profile/blob/master/callback_plugins/profile_tasks.py

"""

ANSIBLE_TIMER_LOG = os.environ.get('ANSIBLE_TIMER_LOG', 'ansible_timing.log')


class Timestamp(object):
    def __init__(self):
        self.start = datetime.utcnow()
        self.end = None

    def stop(self):
        self.end = datetime.utcnow()

    @property
    def duration(self):
        return self.end - self.start


class CallbackModule(object):

    """
    Ansible plugin get the time of each task and total time
    to run the complete playbook
    """
    def __init__(self):
        self.stats = {}
        self.current_task = None
        self.playbook_name = None
        self.playbook_start = None
        self.playbook_end = None

    def playbook_on_play_start(self, pattern):
        self.playbook_name, _ = splitext(
            basename(self.play.playbook.filename)
        )
        self.playbook_start = datetime.utcnow()

    def playbook_on_task_start(self, name, is_conditional):
        """
        Logs the start of each task
        """

        if self.current_task is not None:
            # Record the running time of the last executed task
            self.stats[self.current_task].stop()

        # Record the start time of the current task
        self.current_task = name
        self.stats[self.current_task] = Timestamp()

    def playbook_on_stats(self, stats):
        """
        Prints the timing of each task and total time to
        run the complete playbook
        """
        # Record the timing of the very last task, we use it here, because we
        # don't have stop task function by default
        if self.current_task is not None:
            self.stats[self.current_task].stop()

        self.playbook_end = datetime.utcnow()

        # Sort the tasks by their running time
        results = sorted(
            self.stats.items(),
            key=lambda (task, timestamp): timestamp.duration,
            reverse=True
        )

        # log the stats

        # N.B. This is intended to provide a consistent interface and message format
        # across all of Open edX tooling, so it deliberately eschews standard
        # python logging infrastructure.
        if ANSIBLE_TIMER_LOG is not None:
            log_path = self.playbook_start.strftime(ANSIBLE_TIMER_LOG)
            print('log_path for timing: {}'.format(log_path))
            if not exists(dirname(log_path)):
                print('creating directories: {}'.format(dirname(log_path)))
                os.makedirs(dirname(log_path))

            with open(log_path, 'a') as outfile:
                for name, timestamp in results:
                    log_message = {
                        'task': name,
                        'playbook': self.playbook_name,
                        'started_at': timestamp.start.isoformat(),
                        'ended_at': timestamp.end.isoformat(),
                        'duration': timestamp.duration.total_seconds(),
                    }

                    json.dump(
                        log_message,
                        outfile,
                        separators=(',', ':'),
                        sort_keys=True,
                    )
                    outfile.write('\n')

                log_message = {
                    'playbook': self.playbook_name,
                    'started_at': self.playbook_start.isoformat(),
                    'ended_at': self.playbook_end.isoformat(),
                    'duration': (self.playbook_end - self.playbook_start).total_seconds(),
                }

                json.dump(
                    log_message,
                    outfile,
                    separators=(',', ':'),
                    sort_keys=True,
                )
                outfile.write('\n')

            print('full path to log file: {}'.format(os.path.abspath(log_path)))
            print("contents of log file are: ")
            with open(log_path, 'r') as log_file:
                print log_file.read()
            print("end contents of log file.")
