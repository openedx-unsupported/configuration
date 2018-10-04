import redis
import json
import datetime
import click
import backoff
from itertools import zip_longest

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
    decoded_state = {k.decode("utf-8"): v for k, v in packed_state.items()}
    packed_state = {}

    for key, value in decoded_state.items():
        decoded_value = json.loads(value)
        packed_state[key] = {
            'correlation_id': decoded_value['correlation_id'],
            'first_occurance_time': datetime_from_str(decoded_value['first_occurance_time']),
        } 

    return packed_state

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
    for queue_name, first_item_encoded in queue_first_items.items():
        # TODO: Catch/Handle exception if not json
        first_item = json.loads(first_item_encoded)
        # TODO: Handle keys missing in data
        correlation_id = first_item['properties']['correlation_id']
        first_occurance_time = current_time

        if queue_name in old_state:
            old_correlation_id = old_state[queue_name]['correlation_id']
            if old_correlation_id == correlation_id:
                first_occurance_time = old_state[queue_name]['first_occurance_time']

        new_state[queue_name] = {
            'correlation_id': correlation_id,
            'first_occurance_time': first_occurance_time,
        }

    return new_state

@click.command()
@click.option('--host', '-h', default='localhost',
              help='Hostname of redis server')
@click.option('--port', '-p', default=6379, help='Port of redis server')
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
@click.option('--threshold', default=1,
              help='Default queue maximum item age in minutes'
@click.option('--queue-threshold', type=(str, int), multiple=True,
              help='Per queue maximum item age in format --queue-threshold'
              + ' {queue_name} {threshold}. May be used multiple times')
def check_queues(host, port, environment, deploy, max_metrics, threshold,
                 queue_threshold, sns_arn):

    thresholds = dict(queue_threshold)

    timeout = 1
    redis_client = RedisWrapper(host=host, port=port, socket_timeout=timeout,
                                socket_connect_timeout=timeout)
    redis_client2 = RedisWrapper(host='localhost', port=port, socket_timeout=timeout,
                                socket_connect_timeout=timeout)
    queue_names = set([k.decode() for k in redis_client.keys()
                        if (redis_client.type(k) == b'list' and
                            not k.decode().endswith(".pidbox") and
                            not k.decode().startswith("_kombu"))])

    queue_age_hash = redis_client2.hgetall(QUEUE_AGE_HASH_NAME)
    old_state = unpack_state(queue_age_hash)

    queue_first_items = {}
    current_time = datetime.datetime.now()
    for queue_name in queue_names:
        queue_first_items[queue_name] = redis_client.lindex(queue_name, 0)

    print("old state {}".format(old_state))
    print("\n\nqueue_first_items {}\n\n".format(queue_first_items))
    new_state = build_new_state(old_state, queue_first_items, current_time)
    print("new state {}".format(new_state))

    redis_client2.delete(QUEUE_AGE_HASH_NAME)
    redis_client2.hmset(QUEUE_AGE_HASH_NAME, pack_state(new_state))
