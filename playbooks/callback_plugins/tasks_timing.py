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
            self.stats[self.current_task] = time.time() - self.stats[self.current_task]

        # Record the start time of the current task
        self.current_task = name
        self.stats[self.current_task] = time.time()

    def playbook_on_stats(self, stats):

        """
        Prints the timing of each task and total time to run the complete playbook
        """

        # Record the timing of the very last task, we use it here, because we don't have stop task function by default
        if self.current_task is not None:
            self.stats[self.current_task] = time.time() - self.stats[self.current_task]

        # Sort the tasks by their running time
        results = sorted(self.stats.items(), key=lambda value: value[1], reverse=True)

        datadog.initialize(api_key='9775a026f1ca7d1c6c5af9d94d9595a4',
                           app_key='87ce4a24b5553d2e482ea8a8500e71b8ad4554ff')

        # Print the timing of each task
        for name, elapsed in results:
            # send the metric to datadog
            datadog.api.Metric.send(
                metric="edx.jenkins.{0}".format(name.replace(" | ", ".").replace(" ", "-").lower()),
                points=elapsed,
                host='jenkins',
            )
            # log the time
            # logger.info(
            #     "{0:-<80}{1:->8}".format(
            #         '{0} '.format(name),
            #         ' {0:.02f}s'.format(elapsed),
            #     )
            # )

        # Total time to run the complete playbook
        total_seconds = sum([x[1] for x in self.stats.items()])
        logger.info("\nPlaybook finished: {0}, {1} total tasks.  {2} elapsed. \n".format(
                time.asctime(),
                len(self.stats.items()),
                datetime.timedelta(seconds=(int(total_seconds)))
                )
          )
