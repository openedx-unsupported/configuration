import os
import datetime
import time
import logging
import datadog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
Originally written by 'Jharrod LaFon'
#https://github.com/jlafon/ansible-profile/blob/master/callback_plugins/profile_tasks.py

"""


class CallbackModule(object):

    """

    Ansible plugin get the time of each task and total time to run the complete playbook

    """
    def __init__(self):
        self.stats = {}
        self.current_task = None

    def playbook_on_task_start(self, name, is_conditional):

        """
        Logs the start of each task 
        """

        if self.current_task is not None:
            # Record the running time of the last executed task
            self.stats[self.current_task] = (time.time(), time.time() - self.stats[self.current_task])

        # Record the start time of the current task
        self.current_task = name
        self.stats[self.current_task] = time.time()

    def playbook_on_stats(self, stats):

        """
        Prints the timing of each task and total time to run the complete playbook
        """

        # Record the timing of the very last task, we use it here, because we don't have stop task function by default
        if self.current_task is not None:
            self.stats[self.current_task] = (time.time(), time.time() - self.stats[self.current_task])

        # Sort the tasks by their running time
        results = sorted(self.stats.items(), key=lambda value: value[1][1], reverse=True)

        datadog_api_key = os.getenv('DATADOG_API_KEY')
        datadog_app_key = os.getenv('DATADOG_APP_KEY')
        datadog_api_initialized = True

        if datadog_api_key and datadog_app_key:
                datadog.initialize(api_key=datadog_api_key,
                                   app_key=datadog_app_key)
        else:
            datadog_api_initialized = False

        # send the metric to datadog
        if datadog_api_initialized:
            for name, points in results:
                datadog.api.Metric.send(
                    metric="edx.ansible.{0}.task_duration".format(name.replace(" | ", ".").replace(" ", "-").lower()),
                    points=points,
                )

        # Log the time of each task
        for name, elapsed in results:
            logger.info(
                "{0:-<80}{1:->8}".format(
                    '{0} '.format(name),
                    ' {0:.02f}s'.format(elapsed[1]),
                )
            )

        # Total time to run the complete playbook
        total_seconds = sum([x[1][1] for x in self.stats.items()])
        logger.info("\nPlaybook finished: {0}, {1} total tasks.  {2} elapsed. \n".format(
                time.asctime(),
                len(self.stats.items()),
                datetime.timedelta(seconds=(int(total_seconds)))
                )
          )
