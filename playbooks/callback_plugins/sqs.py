# Copyright 2013 John Jarvis <john@jarv.org>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# From https://github.com/ansible/ansible/issues/31527#issuecomment-335495855
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os
import sys
import time
import json
import socket
try:
    import boto
except ImportError:
    boto = None
else:
    import boto.sqs
    from boto.exception import NoAuthHandlerFound
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    This Ansible callback plugin sends task events
    to SQS.

    The following vars must be set in the environment:
        ANSIBLE_ENABLE_SQS - enables the callback module
        SQS_REGION - AWS region to connect to
        SQS_MSG_PREFIX - Additional data that will be put
                         on the queue (optional)

    The following events are put on the queue
        - FAILURE events
        - OK events
        - TASK events
        - START events
    """
    def __init__(self):
        self.enable_sqs = 'ANSIBLE_ENABLE_SQS' in os.environ
        if not self.enable_sqs:
            return

        # make sure we got our imports
        if not boto:
            raise ImportError(
                "The sqs callback module requires the boto Python module, "
                "which is not installed or was not found."
            )

        self.start_time = time.time()

        if not 'SQS_REGION' in os.environ:
            print('ANSIBLE_ENABLE_SQS enabled but SQS_REGION ' \
                  'not defined in environment')
            sys.exit(1)
        self.region = os.environ['SQS_REGION']
        try:
            self.sqs = boto.sqs.connect_to_region(self.region)
        except NoAuthHandlerFound:
            print('ANSIBLE_ENABLE_SQS enabled but cannot connect ' \
                  'to AWS due invalid credentials')
            sys.exit(1)
        if not 'SQS_NAME' in os.environ:
            print('ANSIBLE_ENABLE_SQS enabled but SQS_NAME not ' \
                  'defined in environment')
            sys.exit(1)
        self.name = os.environ['SQS_NAME']
        self.queue = self.sqs.create_queue(self.name)
        if 'SQS_MSG_PREFIX' in os.environ:
            self.prefix = os.environ['SQS_MSG_PREFIX']
        else:
            self.prefix = ''

        self.last_seen_ts = {}

    def runner_on_failed(self, host, res, ignore_errors=False):
        if self.enable_sqs:
            if not ignore_errors:
                self._send_queue_message(res, 'FAILURE')

    def runner_on_ok(self, host, res):
        if self.enable_sqs:
            # don't send the setup results
            if 'invocation' in res and 'module_name' in res['invocation'] and res['invocation']['module_name'] != "setup":
                self._send_queue_message(res, 'OK')

    def playbook_on_task_start(self, name, is_conditional):
        if self.enable_sqs:
            self._send_queue_message(name, 'TASK')

    def playbook_on_play_start(self, pattern):
        if self.enable_sqs:
            self._send_queue_message(pattern, 'START')

    def playbook_on_stats(self, stats):
        if self.enable_sqs:
            d = {}
            delta = time.time() - self.start_time
            d['delta'] = delta
            for s in ['changed', 'failures', 'ok', 'processed', 'skipped']:
                d[s] = getattr(stats, s)
            self._send_queue_message(d, 'STATS')

    def _send_queue_message(self, msg, msg_type):
        if self.enable_sqs:
            from_start = time.time() - self.start_time
            payload = {msg_type: msg}
            payload['TS'] = from_start
            payload['PREFIX'] = self.prefix
            # update the last seen timestamp for
            # the message type
            self.last_seen_ts[msg_type] = time.time()
            if msg_type in ['OK', 'FAILURE']:
                # report the delta between the OK/FAILURE and
                # last TASK
                if 'TASK' in self.last_seen_ts:
                    from_task = \
                        self.last_seen_ts[msg_type] - self.last_seen_ts['TASK']
                    payload['delta'] = from_task
                for output in ['stderr', 'stdout']:
                    if output in payload[msg_type]:
                        # only keep the last 1000 characters
                        # of stderr and stdout
                        # Some modules set the value of stdout or stderr to booleans in
                        # which case the len will fail. Check to see if there is content
                        # before trying to clip it.
                        if payload[msg_type][output] and len(payload[msg_type][output]) > 1000:
                            payload[msg_type][output] = "(clipping) ... " \
                                    + payload[msg_type][output][-1000:]
                if 'stdout_lines' in payload[msg_type]:
                    # only keep the last 20 or so lines to avoid payload size errors
                    if len(payload[msg_type]['stdout_lines']) > 20:
                        payload[msg_type]['stdout_lines'] = ['(clipping) ... '] + payload[msg_type]['stdout_lines'][-20:]
            while True:
                try:
                    self.sqs.send_message(self.queue, json.dumps(payload))
                    break
                except socket.gaierror as e:
                    print('socket.gaierror will retry: ' + e)
                    time.sleep(1)
                except Exception as e:
                    raise e
