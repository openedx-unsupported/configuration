import os
from os.path import splitext, basename, exists, dirname
from datetime import datetime, timedelta
import json
import time
import logging
import datadog
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("dd").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

"""
Originally written by 'Jharrod LaFon'
#https://github.com/jlafon/ansible-profile/blob/master/callback_plugins/profile_tasks.py

"""

ANSIBLE_TIMER_LOG = os.environ.get('ANSIBLE_TIMER_LOG')


class Timestamp(object):
    def __init__(self):
        self.start = datetime.utcnow()
        self.end = None

    def stop(self):
        self.end = datetime.utcnow()

    @property
    def duration(self):
        return self.end - self.start


class Formatter(object):
    def __init__(self, callback_module, playbook_timestamp):
        self.callback_module = callback_module
        self.playbook_timestamp = playbook_timestamp


class DatadogFormatter(Formatter):
    def __init__(self, callback_module):
        super(DatadogFormatter, self).__init__(callback_module)

        self.datadog_api_key = os.getenv('DATADOG_API_KEY')
        self.datadog_api_initialized = False

        if self.datadog_api_key:
            datadog.initialize(
                api_key=self.datadog_api_key,
                app_key=None
            )
            self.datadog_api_initialized = True

    def clean_tag_value(self, value):
        return value.replace(" | ", ".").replace(" ", "-").lower()

    def log_tasks(self, playbook_name, results):
        if self.datadog_api_initialized:
            datadog_tasks_metrics = []
            for name, timestamp in results:
                datadog_tasks_metrics.append({
                    'metric': 'edx.ansible.task_duration',
                    'date_happened': timestamp.start,
                    'points': timestamp.duration.total_seconds(),
                    'tags': [
                        'task:{0}'.format(self.clean_tag_value(name)),
                        'playbook:{0}'.format(self.clean_tag_value(playbook_name))
                    ]
                })
            try:
                datadog.api.Metric.send(datadog_tasks_metrics)
            except Exception as ex:
                logger.error(ex.message)

    def log_play(self, playbook_name, task_count):
        if self.datadog_api_initialized:
            try:
                datadog.api.Metric.send(
                    metric="edx.ansible.playbook_duration",
                    date_happened=time.time(),
                    points=self.playbook_timestamp.duration.total_seconds(),
                    tags=["playbook:{0}".format(self.clean_tag_value(playbook_name))]
                )
            except Exception as ex:
                logger.error(ex.message)


class JsonFormatter(Formatter):
    def log_tasks(self, playbook_name, results):
        if ANSIBLE_TIMER_LOG is not None:
            log_path = self.playbook_timestamp.start.strftime(ANSIBLE_TIMER_LOG)

            if not exists(dirname(log_path)):
                os.makedirs(dirname(log_path))

            with open(log_path, 'a') as outfile:
                for name, timestamp in results:
                    log_message = {
                        'task': name,
                        'playbook': playbook_name,
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

    def log_play(self, playbook_name, task_count):
        # N.B. This is intended to provide a consistent interface and message format
        # across all of Open edX tooling, so it deliberately eschews standard
        # python logging infrastructure.
        if ANSIBLE_TIMER_LOG is not None:
            log_path = self.playbook_timestamp.start.strftime(ANSIBLE_TIMER_LOG)

            if not exists(dirname(log_path)):
                os.makedirs(dirname(log_path))

            with open(log_path, 'a') as outfile:
                log_message = {
                    'playbook': playbook_name,
                    'started_at': self.playbook_timestamp.start.isoformat(),
                    'ended_at': self.playbook_timestamp.end.isoformat(),
                    'duration': self.playbook_timestamp,
                }

                json.dump(
                    log_message,
                    outfile,
                    separators=(',', ':'),
                    sort_keys=True,
                )
                outfile.write('\n')


class LoggingFormatter(Formatter):
    def log_tasks(self, playbook_name, results):
        for name, timestamp in results[:10]:
            logger.info(
                "{0:-<80}{1:->8}".format(
                    '{0} '.format(name),
                    ' {0:.02f}s'.format(timestamp.duration.total_seconds()),
                )
            )

    def log_play(self, playbook_name, task_count):
        logger.info("\nPlaybook {0} finished: {1}, {2} total tasks.  {3} elapsed. \n".format(
            playbook_name,
            time.asctime(),
            task_count,
            timedelta(seconds=(int(self.playbook_timestamp.duration.total_seconds())))
        ))


class CallbackModule(object):

    """
    Ansible plugin get the time of each task and total time
    to run the complete playbook
    """
    def __init__(self):
        self.stats = {}
        self.current_task = None
        self.playbook_name = None
        self.playbook_timestamp = None

        self.formatters = [
            DatadogFormatter,
            LoggingFormatter,
            JsonFormatter,
        ]


    def playbook_on_play_start(self, pattern):
        self.playbook_name, _ = splitext(
            basename(self.play.playbook.filename)
        )
        self.playbook_timestamp = Timestamp()

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

        self.playbook_timestamp.stop()

        # Sort the tasks by their running time
        results = sorted(
            self.stats.items(),
            key=lambda (task, timestamp): timestamp.duration,
            reverse=True
        )

        for fmt_class in self.formatters:
            formatter = fmt_class(self, playbook_timestamp)
            formatter.log_tasks(self.playbook_name, results)
            formatter.log_play(self.playbook_name, len(self.stats))
