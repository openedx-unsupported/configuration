import collections
from datetime import datetime, timedelta
import json
import logging
import os
from os.path import splitext, basename, exists, dirname
import sys
import time

try:
    from ansible.plugins.callback import CallbackBase
except ImportError:
    # Support Ansible 1.9.x
    CallbackBase = object

import datadog

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("dd").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

"""
Originally written by 'Jharrod LaFon'
#https://github.com/jlafon/ansible-profile/blob/master/callback_plugins/profile_tasks.py

"""

ANSIBLE_TIMER_LOG = os.environ.get('ANSIBLE_TIMER_LOG')


class Timestamp(object):
    """
    A class for capturing start, end and duration for an action.
    """
    def __init__(self):
        self.start = datetime.utcnow()
        self.end = None

    def stop(self):
        """
        Record the end time of the timed period.
        """
        self.end = datetime.utcnow()

    @property
    def duration(self):
        """
        Return the duration that this Timestamp covers.
        """
        return self.end - self.start


# This class only has a single method (which would ordinarily make it a
# candidate to be turned into a function). However, the TimingLoggers are
# instanciated once when ansible starts up, and then called for every play.
class TimingLogger(object):
    """
    Base-class for logging timing about ansible tasks and plays.
    """
    def log_play(self, playbook_name, playbook_timestamp, results):
        """
        Record the timing results of an ansible play.

        Arguments:
            playbook_name: the name of the playbook being logged.
            playbook_timestamp (Timestamp): the timestamps measuring how
                long the play took.
            results (dict(string -> Timestamp)): a dict mapping task names
                to Timestamps that measure how long each task took.
        """
        pass


class DatadogTimingLogger(TimingLogger):
    """
    Record ansible task and play timing to Datadog.

    Requires that the environment variable DATADOG_API_KEY be set in order
    to log any data.
    """
    def __init__(self):
        super(DatadogTimingLogger, self).__init__()

        self.datadog_api_key = os.getenv('DATADOG_API_KEY')
        self.datadog_api_initialized = False

        if self.datadog_api_key:
            datadog.initialize(
                api_key=self.datadog_api_key,
                app_key=None
            )
            self.datadog_api_initialized = True

    def clean_tag_value(self, value):
        """
        Remove any characters that aren't allowed in Datadog tags.

        Arguments:
            value: the string to be cleaned.
        """
        return value.replace(" | ", ".").replace(" ", "-").lower()

    def log_play(self, playbook_name, playbook_timestamp, results):
        if not self.datadog_api_initialized:
            return

        datadog_tasks_metrics = []
        for name, timestamp in results.items():
            datadog_tasks_metrics.append({
                'metric': 'edx.ansible.task_duration',
                'date_happened': time.mktime(timestamp.start.timetuple()),
                'points': timestamp.duration.total_seconds(),
                'tags': [
                    'task:{0}'.format(self.clean_tag_value(name)),
                    'playbook:{0}'.format(self.clean_tag_value(playbook_name))
                ]
            })
        try:
            datadog.api.Metric.send(datadog_tasks_metrics)
            datadog.api.Metric.send(
                metric="edx.ansible.playbook_duration",
                date_happened=time.mktime(playbook_timestamp.start.timetuple()),
                points=playbook_timestamp.duration.total_seconds(),
                tags=["playbook:{0}".format(self.clean_tag_value(playbook_name))]
            )
        except Exception:
            LOGGER.exception("Failed to log timing data to datadog")


class JsonTimingLogger(TimingLogger):
    """
    Record task and play timing to a local file in a JSON format.

    Requires that the environment variable ANSIBLE_TIMER_LOG be set in order
    to log any data. This specifies the file that timing data should be logged
    to. That variable can include strftime interpolation variables,
    which will be replaced with the start time of the play.
    """
    def log_play(self, playbook_name, playbook_timestamp, results):
        # N.B. This is intended to provide a consistent interface and message
        # format across all of Open edX tooling, so it deliberately eschews
        # standard python logging infrastructure.
        if ANSIBLE_TIMER_LOG is None:
            return

        messages = []
        for name, timestamp in results.items():
            messages.append({
                'task': name,
                'playbook': playbook_name,
                'started_at': timestamp.start.isoformat(),
                'ended_at': timestamp.end.isoformat(),
                'duration': timestamp.duration.total_seconds(),
            })

        messages.append({
            'playbook': playbook_name,
            'started_at': playbook_timestamp.start.isoformat(),
            'ended_at': playbook_timestamp.end.isoformat(),
            'duration': playbook_timestamp.duration.total_seconds(),
        })

        log_path = playbook_timestamp.start.strftime(ANSIBLE_TIMER_LOG)

        try:
            log_dir = dirname(log_path)
            if log_dir and not exists(log_dir):
                os.makedirs(log_dir)

            with open(log_path, 'a') as outfile:
                for log_message in messages:
                    json.dump(
                        log_message,
                        outfile,
                        separators=(',', ':'),
                        sort_keys=True,
                    )
                    outfile.write('\n')
        except Exception:
            LOGGER.exception("Unable to write json timing log messages")


class LoggingTimingLogger(TimingLogger):
    """
    Log timing information for the play and the top 10 tasks to stdout.
    """
    def log_play(self, playbook_name, playbook_timestamp, results):

        # Sort the tasks by their running time
        sorted_results = sorted(
            results.items(),
            key=lambda (task, timestamp): timestamp.duration,
            reverse=True
        )

        for name, timestamp in sorted_results[:10]:
            LOGGER.info(
                "{0:-<80}{1:->8}".format(
                    ' {0} '.format(name),
                    ' {0:.02f}s'.format(timestamp.duration.total_seconds()),
                )
            )

        LOGGER.info(
            "\nPlaybook %s finished: %s, %d total tasks.  %s elapsed. \n",
            playbook_name,
            playbook_timestamp.end,
            len(results),
            playbook_timestamp.duration,
        )


class CallbackModule(CallbackBase):

    """
    Ansible plugin get the time of each task and total time
    to run the complete playbook
    """
    def __init__(self):
        self.stats = collections.defaultdict(list)
        self.current_task = None
        self.playbook_name = None
        self.playbook_timestamp = None
        self.play = None

        self.loggers = [
            DatadogTimingLogger(),
            LoggingTimingLogger(),
            JsonTimingLogger(),
        ]

    def v2_playbook_on_play_start(self, play):
        self.play = play
        super(CallbackModule, self).v2_playbook_on_play_start(play)

    def playbook_on_play_start(self, pattern):
        """
        Record the start of a play.
        """
        self.playbook_name, _ = splitext(
            basename(self.play.get_name())
        )
        self.playbook_timestamp = Timestamp()

    def playbook_on_task_start(self, name, is_conditional):
        """
        Logs the start of each task
        """

        if self.current_task is not None:
            # Record the running time of the last executed task
            self.stats[self.current_task][-1].stop()

        # Record the start time of the current task
        self.current_task = name
        self.stats[self.current_task].append(Timestamp())

    def playbook_on_stats(self, stats):
        """
        Prints the timing of each task and total time to
        run the complete playbook
        """
        # Record the timing of the very last task, we use it here, because we
        # don't have stop task function by default
        if self.current_task is not None:
            self.stats[self.current_task][-1].stop()

        self.playbook_timestamp.stop()

        # Flatten the stats so that multiple runs of the same task get listed
        # individually.
        flat_stats = {}
        for task_name, task_runs in self.stats.iteritems():
            if len(task_runs) == 1:
                flat_stats[task_name] = task_runs[0]
            else:
                for i, run in enumerate(task_runs):
                    run_name = "{} [{}]".format(task_name, i)
                    flat_stats[run_name] = run

        for logger in self.loggers:
            logger.log_play(
                self.playbook_name,
                self.playbook_timestamp,
                flat_stats,
            )
