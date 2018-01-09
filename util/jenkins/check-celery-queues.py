import redis
import click
import boto3
import botocore
import backoff

max_tries = 5


class RedisWrapper(object):
    def __init__(self, *args, **kwargs):
        self.redis = redis.StrictRedis(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=max_tries)
    def keys(self):
        return self.redis.keys()

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=max_tries)
    def type(self, key):
        return self.redis.type(key)

    @backoff.on_exception(backoff.expo,
                          (redis.exceptions.TimeoutError,
                           redis.exceptions.ConnectionError),
                          max_tries=max_tries)
    def llen(self, key):
        return self.redis.llen(key)


class CwBotoWrapper(object):
    def __init__(self):
        self.cw = boto3.client('cloudwatch')

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=max_tries)
    def list_metrics(self, *args, **kwargs):
        return self.cw.list_metrics(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=max_tries)
    def put_metric_data(self, *args, **kwargs):
        return self.cw.put_metric_data(*args, **kwargs)

@click.command()
@click.option('--host', '-h', default='localhost',
              help='Hostname of redis server')
@click.option('--port', '-p', default=6379, help='Port of redis server')
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
@click.option('--max-metrics', default=30,
              help='Maximum number of CloudWatch metrics to publish')
def check_queues(host, port, environment, deploy, max_metrics):
    timeout = 1
    namespace = "celery/{}-{}".format(environment, deploy)
    r = RedisWrapper(host=host, port=port, socket_timeout=timeout,
                     socket_connect_timeout=timeout)
    cw = CwBotoWrapper()
    metric_name = 'queue_length'
    dimension = 'queue'
    response = cw.list_metrics(Namespace=namespace, MetricName=metric_name,
                               Dimensions=[{'Name': dimension}])
    existing_queues = []
    for m in response["Metrics"]:
        existing_queues.extend(
            [d['Value'] for d in m["Dimensions"] if d['Name'] == dimension])

    redis_queues = set([k.decode() for k in r.keys() if r.type(k) == b'list'])

    all_queues = existing_queues + list(
        set(redis_queues).difference(existing_queues)
    )

    if len(all_queues) > max_metrics:
        # TODO: Use proper logging framework
        print("Warning! Too many metrics, refusing to publish more than {}".format(max_metrics))

    # Take first max_metrics number of queues from all_queues and remove
    # queues that aren't in redis
    queues = [q for q in all_queues[:max_metrics] if q in redis_queues]

    metric_data = []
    for queue in queues:
        metric_data.append({
            'MetricName': metric_name,
            'Dimensions': [{
                "Name": dimension,
                "Value": queue
            }],
            'Value': r.llen(queue)
        })

    cw.put_metric_data(Namespace=namespace, MetricData=metric_data)


if __name__ == '__main__':
    check_queues()
