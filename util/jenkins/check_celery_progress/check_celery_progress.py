import sys
import pickle
import json
import datetime
import base64
import zlib
import redis
import click
import backoff
from opsgenie.swagger_client import AlertApi
from opsgenie.swagger_client import configuration
from opsgenie.swagger_client.models import CreateAlertRequest, CloseAlertRequest
from opsgenie.swagger_client.rest import ApiException
from textwrap import dedent


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
        return self.redis.keys()

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

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=MAX_TRIES)
    def delete(self, key):
        return self.redis.delete(key)

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=MAX_TRIES)
    def hset(self, *args):
        return self.redis.hset(*args)

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=MAX_TRIES)
    def hmset(self, *args):
        return self.redis.hmset(*args)


def pretty_json(obj):
    return json.dumps(obj, indent=4, sort_keys=True)


def pretty_state(state):
    output = {}
    for queue_name, queue_state in state.items():
        output[queue_name] = {}
        for key, value in queue_state.items():
            if key == 'first_occurance_time':
                value = str_from_datetime(value)
            output[queue_name][key] = value
    return pretty_json(output)


def datetime_from_str(string):
    return datetime.datetime.strptime(string, DATE_FORMAT)


def str_from_datetime(dt):
    return dt.strftime(DATE_FORMAT)


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


def pack_state(unpacked_state):
    packed_state = {}
    for queue_name, queue_state in unpacked_state.items():
        dt_str = str_from_datetime(queue_state['first_occurance_time'])
        packed_state[queue_name] = json.dumps({
            'correlation_id': queue_state['correlation_id'],
            'first_occurance_time': dt_str,
            'alert_created': queue_state['alert_created'],
        })
    return packed_state


def build_new_state(old_state, queue_first_items, current_time):
    new_state = {}
    for queue_name, first_item in queue_first_items.items():
        # TODO: Handle keys missing in data
        correlation_id = first_item['properties']['correlation_id']
        first_occurance_time = current_time
        alert_created = False
        if queue_name in old_state:
            old_correlation_id = old_state[queue_name]['correlation_id']
            alert_created = old_state[queue_name]['alert_created']
            if old_correlation_id == correlation_id:
                first_occurance_time = old_state[queue_name]['first_occurance_time']

        new_state[queue_name] = {
            'correlation_id': correlation_id,
            'first_occurance_time': first_occurance_time,
            'alert_created': alert_created,
        }

    return new_state


def should_create_alert(first_occurance_time, current_time, threshold):
    time_delta = current_time - first_occurance_time
    return time_delta.total_seconds() > threshold


def generate_alert_message(environment, deploy, queue_name, threshold):
    return str.format("{}-{} {} queue is stale. Stationary for over {}s", environment, deploy, queue_name, threshold)


def generate_alert_alias(environment, deploy, queue_name):
    return str.format("{}-{} {} stale celery queue", environment, deploy, queue_name)


@backoff.on_exception(backoff.expo,
                      (ApiException),
                      max_tries=MAX_TRIES)
def create_alert(opsgenie_api_key, environment, deploy, queue_name, threshold, info):

    configuration.api_key['Authorization'] = opsgenie_api_key
    configuration.api_key_prefix['Authorization'] = 'GenieKey'

    alert_message = generate_alert_message(environment, deploy, queue_name, threshold)
    alias = generate_alert_alias(environment, deploy, queue_name)

    print("Creating Alert: {}".format(alias))
    response = AlertApi().create_alert(body=CreateAlertRequest(message=alert_message, alias=alias, description=info))
    print('request id: {}'.format(response.request_id))
    print('took: {}'.format(response.took))
    print('result: {}'.format(response.result))


@backoff.on_exception(backoff.expo,
                      (ApiException),
                      max_tries=MAX_TRIES)
def close_alert(opsgenie_api_key, environment, deploy, queue_name):

    configuration.api_key['Authorization'] = opsgenie_api_key
    configuration.api_key_prefix['Authorization'] = 'GenieKey'

    alias = generate_alert_alias(environment, deploy, queue_name)
    print("Closing Alert: {}".format(alias))
    # Need body=CloseAlertRequest(source="") otherwise OpsGenie API complains that bdoy must be a json object
    response = AlertApi().close_alert(identifier=alias, identifier_type='alias', body=CloseAlertRequest(source=""))
    print('request id: {}'.format(response.request_id))
    print('took: {}'.format(response.took))
    print('result: {}'.format(response.result))


def extract_body(task):
    body = base64.b64decode(task['body'])
    body_dict = {}

    if 'headers' in task and 'compression' in task['headers'] and task['headers']['compression'] == 'application/x-gzip':
        body = zlib.decompress(body)

    if task.get('content-type') == 'application/json':
        body_dict = json.loads(body.decode("utf-8"))
    elif task.get('content-type') == 'application/x-python-serialize':
        body_dict = pickle.loads(body, encoding='bytes')
    return body_dict


def generate_info(
    queue_name,
    correlation_id,
    body,
    active_tasks,
    do_alert,
    first_occurance_time,
    current_time,
    threshold,
    default_threshold,
    jenkins_build_url,
):
    time_delta = (current_time - first_occurance_time).seconds
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
            do_alert = {}
            first_occurance_time = {}
            current_time = {}
            time_delta = {} seconds
            threshold = {} seconds
            default_threshold = {} seconds
            jenkins_build_url = {}
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
        do_alert,
        first_occurance_time,
        current_time,
        time_delta,
        threshold,
        default_threshold,
        jenkins_build_url,
        active_tasks,
        next_task,
        args,
        kwargs,
    )
    return output


@click.command()
@click.option('--host', '-h', default='localhost',
              help='Hostname of redis server', required=True)
@click.option('--port', '-p', default=6379, help='Port of redis server')
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
@click.option('--default-threshold', default=300,
              help='Default queue maximum item age in seconds')
@click.option('--queue-threshold', type=(str, int), multiple=True,
              help='Per queue maximum item age (seconds) in format --queue-threshold'
              + ' {queue_name} {threshold}. May be used multiple times.')
@click.option('--opsgenie-api-key', '-k', envvar='OPSGENIE_API_KEY', required=True)
@click.option('--jenkins-build-url', '-j', envvar='BUILD_URL', required=False)
def check_queues(host, port, environment, deploy, default_threshold, queue_threshold, opsgenie_api_key, jenkins_build_url):
    ret_val = 0
    thresholds = dict(queue_threshold)
    print("Default Threshold (seconds): {}".format(default_threshold))
    print("Per Queue Thresholds (seconds):\n{}".format(pretty_json(thresholds)))

    timeout = 1
    redis_client = RedisWrapper(host=host, port=port, socket_timeout=timeout,
                                socket_connect_timeout=timeout)
    queue_names = set([k.decode() for k in redis_client.keys()
                       if (redis_client.type(k) == b'list' and
                           not k.decode().endswith(".pidbox") and
                           not k.decode().startswith("_kombu"))])
    queue_age_hash = redis_client.hgetall(QUEUE_AGE_HASH_NAME)
    old_state = unpack_state(queue_age_hash)
    # Temp debugging
    print("DEBUG: old_state\n{}\n".format(pretty_state(old_state)))
    queue_first_items = {}
    current_time = datetime.datetime.now()

    for queue_name in queue_names:
        queue_first_item = redis_client.lindex(queue_name, 0)
        # Check that queue_first_item is not None which is the case if the queue is empty
        if queue_first_item is not None:
            queue_first_items[queue_name] = json.loads(queue_first_item.decode("utf-8"))

    new_state = build_new_state(old_state, queue_first_items, current_time)

    # Temp debugging
    print("DEBUG: new_state from new_state() function\n{}\n".format(pretty_state(new_state)))
    for queue_name in queue_names:
        redacted_body = ""
        threshold = default_threshold
        if queue_name in thresholds:
            threshold = thresholds[queue_name]

        correlation_id = new_state[queue_name]['correlation_id']
        first_occurance_time = new_state[queue_name]['first_occurance_time']
        body = {}
        try:
            body = extract_body(queue_first_items[queue_name])
        except Exception as error:
            print("ERROR: Unable to extract task body in queue {}, exception {}".format(queue_name, error))
            ret_val = 1
        redacted_body = {'task': body.get('task'), 'args': 'REDACTED', 'kwargs': 'REDACTED'}
        active_tasks, redacted_active_tasks = get_active_tasks(host, port, queue_name)
        do_alert = should_create_alert(first_occurance_time, current_time, threshold)

        info = generate_info(
            queue_name,
            correlation_id,
            body,
            active_tasks,
            do_alert,
            first_occurance_time,
            current_time,
            threshold,
            default_threshold,
            jenkins_build_url,
        )
        redacted_info = generate_info(
            queue_name,
            correlation_id,
            redacted_body,
            redacted_active_tasks,
            do_alert,
            first_occurance_time,
            current_time,
            threshold,
            default_threshold,
            jenkins_build_url,
        )
        print(info)
        if not new_state[queue_name]['alert_created'] and do_alert:
            create_alert(opsgenie_api_key, environment, deploy, queue_name, threshold, redacted_info)
            new_state[queue_name]['alert_created'] = True
        elif new_state[queue_name]['alert_created'] and not do_alert:
            close_alert(opsgenie_api_key, environment, deploy, queue_name)
            new_state[queue_name]['alert_created'] = False

    for queue_name in set(old_state.keys()) - set(new_state.keys()):
        print("DEBUG: Checking cleared queue {}".format(queue_name))
        if old_state[queue_name]['alert_created']:
            close_alert(opsgenie_api_key, environment, deploy, queue_name)

    redis_client.delete(QUEUE_AGE_HASH_NAME)
    if new_state:
        redis_client.hmset(QUEUE_AGE_HASH_NAME, pack_state(new_state))
        # Temp Debugging
        print("DEBUG: new_state pushed to redis\n{}\n".format(pretty_state(new_state)))

    sys.exit(ret_val)

def connection(host, port):
    from celery import Celery
    celery_app = " "
    try:
        broker_url = "redis://" + host + ":" + str(port)
        celery_app = Celery(broker=broker_url)
    except Exception as e:
        print("Exception in connection()", e)
    return celery_app


# Functionality added to get list of currently running tasks
# because Redis returns only the next tasks in the list
def get_active_tasks(host, port, queue, redacted=True):
    active_tasks = dict()
    redacted_active_tasks = dict()
    celery_app = connection(host, port)
    celery_obj = celery_app.control.inspect()
    try:
        for worker, data in celery_obj.active().items():
            if queue in worker.split('@')[1]:
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
        print("Exception in get_active_tasks()", e)
    return (pretty_json(active_tasks), pretty_json(redacted_active_tasks))


if __name__ == '__main__':
    check_queues()
