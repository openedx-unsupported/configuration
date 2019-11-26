from __future__ import absolute_import
from __future__ import print_function
import sys
import pickle
import json
import datetime
import base64
import zlib
import redis
import click
import backoff
from celery import Celery
from textwrap import dedent
from pprint import pprint
from six.moves import range


MAX_TRIES = 5
QUEUE_AGE_HASH_NAME = "queue_age_monitoring"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


class RedisWrapper(object):
    def __init__(self, *args, **kwargs):
        self.redis = redis.StrictRedis(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=MAX_TRIES)
    def keys(self):
        return list(self.redis.keys())

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=MAX_TRIES)
    def type(self, key):
        return self.redis.type(key)

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=MAX_TRIES)
    def llen(self, key):
        return self.redis.llen(key)

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=MAX_TRIES)
    def lindex(self, key, index):
        return self.redis.lindex(key, index)

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=MAX_TRIES)
    def hgetall(self, key):
        return self.redis.hgetall(key)


def pretty_json(obj):
    return json.dumps(obj, indent=4, sort_keys=True)


def unpack_state(packed_state):
    decoded_state = {k.decode("utf-8"): v.decode("utf-8") for k, v in packed_state.items()}
    unpacked_state = {}

    for key, value in decoded_state.items():
        decoded_value = json.loads(value)
        unpacked_state[key] = {
            'correlation_id': decoded_value['correlation_id'],
            'first_occurance_time': datetime_from_str(decoded_value['first_occurance_time']),
            'alert_created': decoded_value['alert_created'],
        }

    return unpacked_state


def extract_body(task):
    body = base64.b64decode(task['body'])
    body_dict = {}

    if 'headers' in task and 'compression' in task['headers'] and task['headers']['compression'] == 'application/x-gzip':
        body = zlib.decompress(body)

    if task.get('content-type') == 'application/json':
        body_dict = json.loads(body.decode("utf-8"))
    elif task.get('content-type') == 'application/x-python-serialize':
        body_dict = {k.decode("utf-8"): v for k, v in pickle.loads(body, encoding='bytes').items()}
    return body_dict


def generate_info(
    queue_name,
    correlation_id,
    body,
    active_tasks,
):
    next_task = "Key missing"
    args = "Key missing"
    kwargs = "Key missing"

    if 'task' in body:
        next_task = body['task']

    if 'args' in body:
        args = body['args']

    if 'kwargs' in body:
        kwargs = body['kwargs']

    output = str.format(
        dedent("""
            =============================================
            queue_name = {}
            correlation_id = {}
            ---------------------------------------------
            active_tasks = {}
            ---------------------------------------------
            next_task = {}
            args = {}
            kwargs = {}
            =============================================
        """),
        queue_name,
        correlation_id,
        active_tasks,
        next_task,
        args,
        kwargs,
    )
    return output


def celery_connection(host, port):
    celery_client = " "
    try:
        broker_url = "redis://" + host + ":" + str(port)
        celery_client = Celery(broker=broker_url)
    except Exception as e:
        print(("Exception in connection():", e))
    return celery_client


# Functionality added to get list of currently running tasks
# because Redis returns only the next tasks in the list
def get_active_tasks(celery_control, queue_workers, queue_name):
    active_tasks = dict()
    redacted_active_tasks = dict()
    if queue_name in queue_workers:
        workers = queue_workers[queue_name]
        try:
            for worker, data in celery_control.inspect(workers).active().items():
                for task in data:
                    active_tasks.setdefault(
                        task["hostname"], []).append([
                            'task: {}'.format(task.get("name")),
                            'args: {}'.format(task.get("args")),
                            'kwargs: {}'.format(task.get("kwargs")),
                        ])
                    redacted_active_tasks.setdefault(
                        task["hostname"], []).append([
                            'task: {}'.format(task.get("name")),
                            'args: REDACTED',
                            'kwargs: REDACTED',
                        ])
        except Exception as e:
            print(("Exception in get_active_tasks():", e))
    return (pretty_json(active_tasks), pretty_json(redacted_active_tasks))


@click.command()
@click.option('--host', '-h', default='localhost',
              help='Hostname of redis server', required=True)
@click.option('--port', '-p', default=6379, help='Port of redis server')
@click.option('--queue', '-q', required=True)
@click.option('--items', '-i', default=1, help='Number of items to print')
@click.option('--body/--no-body', default=False, help='Print full body of tasks')
def check_queues(host, port, queue, items, body):
    queue_name = queue
    ret_val = 0

    timeout = 1
    redis_client = RedisWrapper(host=host, port=port, socket_timeout=timeout,
                                socket_connect_timeout=timeout)
    celery_control = celery_connection(host, port).control

    # key: queue name, value: list of worker nodes for each queue
    queue_workers = {}
    try:
        for worker, data in celery_control.inspect().active_queues().items():
             for queue in data:
                 queue_workers.setdefault(queue['name'], []).append(worker)
    except Exception as e:
        print(("Exception while getting queue to worker mappings:", e))

    for count in range(items):
        print(("Count: {}".format(count)))
        queue_first_item = redis_client.lindex(queue_name, count)
        # Check that queue_first_item is not None which is the case if the queue is empty
        if queue_first_item is not None:
            queue_first_item_decoded = json.loads(queue_first_item.decode("utf-8"))

            correlation_id = queue_first_item_decoded['properties']['correlation_id']

            extracted_body = {}
            try:
                extracted_body = extract_body(queue_first_item_decoded)
            except Exception as error:
                print(("ERROR: Unable to extract task body in queue {}, exception {}".format(queue_name, error)))
                ret_val = 1
            active_tasks, redacted_active_tasks = get_active_tasks(celery_control, queue_workers, queue_name)

            info = generate_info(
                queue_name,
                correlation_id,
                extracted_body,
                active_tasks,
            )
            print(info)
            if body:
                print("BODY")
                pprint(extracted_body)

    sys.exit(ret_val)


if __name__ == '__main__':
    check_queues()
