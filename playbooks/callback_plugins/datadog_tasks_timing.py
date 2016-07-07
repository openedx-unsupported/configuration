import os
import datetime
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


class CallbackModule(object):

    """
    Ansible plugin get the time of each task and total time
    to run the complete playbook
    """
    def __init__(self):
        self.stats = {}
        self.current_task = None
        self.playbook_name = None
        self.datadog_api_key = os.getenv('DATADOG_API_KEY')
        self.datadog_api_initialized = False

        if self.datadog_api_key:
            datadog.initialize(api_key=self.datadog_api_key,
                               app_key=None)
            self.datadog_api_initialized = True

    def clean_tag_value(self, value):
        return value.replace(" | ", ".").replace(" ", "-").lower()

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
        Prints the timing of each task and total time to
        run the complete playbook
        """
        # Record the timing of the very last task, we use it here, because we
        # don't have stop task function by default
        if self.current_task is not None:
            self.stats[self.current_task] = (time.time(), time.time() - self.stats[self.current_task])

        # Sort the tasks by their running time
        results = sorted(self.stats.items(),
                         key=lambda value: value[1][1], reverse=True)

        # Total time to run the complete playbook
        total_seconds = sum([x[1][1] for x in self.stats.items()])
          
        # send the metric to datadog
        if self.datadog_api_initialized:
            datadog_tasks_metrics = []
            for name, points in results:
                datadog_tasks_metrics.append({'metric': 'edx.ansible.task_duration',
                                              'date_happened': points[0],
                                              'points': points[1],
                                              'tags': ['task:{0}'.format(self.clean_tag_value(name)),
                                                       'playbook:{0}'.format(self.clean_tag_value(self.playbook_name))
                                                       ]
                                              }
                                             )
            try:
                datadog.api.Metric.send(datadog_tasks_metrics)
                datadog.api.Metric.send(metric="edx.ansible.playbook_duration",
                                        date_happened=time.time(),
                                        points=total_seconds,
                                        tags=["playbook:{0}".format(self.clean_tag_value(self.playbook_name))]
                                        )
            except Exception as ex:
                logger.error(ex.message)

        # Log the time of each task
        for name, elapsed in results[:10]:
            logger.info(
                "{0:-<80}{1:->8}".format(
                    '{0} '.format(name),
                    ' {0:.02f}s'.format(elapsed[1]),
                )
            )

        logger.info("\nPlaybook {0} finished: {1}, {2} total tasks.  {3} elapsed. \n".format(
                self.playbook_name,
                time.asctime(),
                len(self.stats.items()),
                datetime.timedelta(seconds=(int(total_seconds)))
                )
          )
