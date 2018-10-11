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
        }

    return unpacked_state


def pack_state(unpacked_state):
    packed_state = {}
    for queue_name, queue_state in unpacked_state.items():
        dt_str = str_from_datetime(queue_state['first_occurance_time'])
        packed_state[queue_name] = json.dumps({
            'correlation_id': queue_state['correlation_id'],
            'first_occurance_time': dt_str,
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
            if old_correlation_id == correlation_id:
                first_occurance_time = old_state[queue_name]['first_occurance_time']
            if 'alert_created' in old_state[queue_name]:
                alert_created = old_state[queue_name]['alert_created']

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
def create_alert(opsgenie_api_key, environment, deploy, queue_name, threshold):

    configuration.api_key['Authorization'] = opsgenie_api_key
    configuration.api_key_prefix['Authorization'] = 'GenieKey'

    alert_message = generate_alert_message(environment, deploy, queue_name, threshold)
    alias = generate_alert_alias(environment, deploy, queue_name)

    print("Creating Alert: {}".format(alias))
    response = AlertApi().create_alert(body=CreateAlertRequest(message=alert_message, alias=alias))
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

    if 'headers' in task and 'compression' in task['headers'] and task['headers']['compression'] == 'application/x-gzip':
        body = zlib.decompress(body)

    try:
        body_dict = json.loads(body.decode("utf-8"))
    except:
        body_dict = {}

    return body_dict


def print_info(
    queue_name,
    correlation_id,
    body,
    do_alert,
    first_occurance_time,
    current_time,
    threshold,
    default_threshold,
):
    time_delta = (current_time - first_occurance_time).seconds
    task = "Key missing"
    args = "Key missing"
    kwargs = "Key missing"

    if 'task' in body:
        task = body['task']

    if 'args' in body:
        args = body['args']

    if 'kwargs' in body:
        kwargs = body['kwargs']

    output = str.format(
        """
            ---------------------------------------------
            queue_name = {}
            correlation_id = {}
            task = {}
            args = {}
            kwargs = {}
            do_alert = {}
            first_occurance_time = {}
            current_time = {}
            time_delta = {} seconds
            threshold = {} seconds
            default_threshold = {} seconds
        """,
        queue_name,
        correlation_id,
        task,
        args,
        kwargs,
        do_alert,
        first_occurance_time,
        current_time,
        time_delta,
        threshold,
        default_threshold,
    )
    print(dedent(output))


@click.command()
@click.option('--host', '-h', default='localhost',
              help='Hostname of redis server', required=True)
@click.option('--port', '-p', default=6379, help='Port of redis server')
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
@click.option('--default-threshold', default=60,
              help='Default queue maximum item age in seconds')
@click.option('--queue-threshold', type=(str, int), multiple=True,
              help='Per queue maximum item age (seconds) in format --queue-threshold'
              + ' {queue_name} {threshold}. May be used multiple times.')
@click.option('--opsgenie-api-key', '-k', envvar='OPSGENIE_API_KEY', required=True)
def check_queues(host, port, environment, deploy, default_threshold, queue_threshold, opsgenie_api_key):

    thresholds = dict(queue_threshold)

    timeout = 1
    redis_client = RedisWrapper(host=host, port=port, socket_timeout=timeout,
                                socket_connect_timeout=timeout)
    queue_names = set([k.decode() for k in redis_client.keys()
                       if (redis_client.type(k) == b'list' and
                           not k.decode().endswith(".pidbox") and
                           not k.decode().startswith("_kombu"))])

    queue_age_hash = redis_client.hgetall(QUEUE_AGE_HASH_NAME)
    old_state = unpack_state(queue_age_hash)

    queue_first_items = {}
    current_time = datetime.datetime.now()
    for queue_name in queue_names:
        queue_first_items[queue_name] = json.loads(redis_client.lindex(queue_name, 0).decode("utf-8"))
    new_state = build_new_state(old_state, queue_first_items, current_time)

    for queue_name in queue_names:
        threshold = default_threshold
        if queue_name in thresholds:
            threshold = thresholds[queue_name]

        correlation_id = new_state[queue_name]['correlation_id']
        first_occurance_time = new_state[queue_name]['first_occurance_time']
        body = extract_body(queue_first_items[queue_name])
        do_alert = should_create_alert(first_occurance_time, current_time, threshold)

        print_info(queue_name, correlation_id, body, do_alert, first_occurance_time, current_time, threshold, default_threshold)
        if not new_state[queue_name]['alert_created'] and do_alert:
            create_alert(opsgenie_api_key, environment, deploy, queue_name, threshold)
            new_state[queue_name]['alert_created'] = True
        elif new_state[queue_name]['alert_created']:
            close_alert(opsgenie_api_key, environment, deploy, queue_name)
            new_state[queue_name]['alert_created'] = False

    for queue_name in set(old_state.keys()) - set(new_state.keys()):
        if 'alert_created' in old_state[queue_name] and old_state[queue_name]['alert_created']:
            close_alert(opsgenie_api_key, environment, deploy, queue_name)

    redis_client.delete(QUEUE_AGE_HASH_NAME)
    if new_state:
        redis_client.hmset(QUEUE_AGE_HASH_NAME, pack_state(new_state))


if __name__ == '__main__':
    check_queues()
