import redis
import click
import boto3
import botocore
import backoff
from itertools import zip_longest

MAX_TRIES = 5


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


class CwBotoWrapper(object):
    def __init__(self):
        self.client = boto3.client('cloudwatch')

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=MAX_TRIES)
    def list_metrics(self, *args, **kwargs):
        return self.client.list_metrics(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=MAX_TRIES)
    def put_metric_data(self, *args, **kwargs):
        return self.client.put_metric_data(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=MAX_TRIES)
    def describe_alarms_for_metric(self, *args, **kwargs):
        return self.client.describe_alarms_for_metric(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=MAX_TRIES)
    def put_metric_alarm(self, *args, **kwargs):
        return self.client.put_metric_alarm(*args, **kwargs)


@click.command()
@click.option('--host', '-h', default='localhost',
              help='Hostname of redis server')
@click.option('--port', '-p', default=6379, help='Port of redis server')
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
@click.option('--max-metrics', default=20,
              help='Maximum number of CloudWatch metrics to publish')
@click.option('--threshold', default=50,
              help='Default maximum queue length before alarm notification is'
              + ' sent')
@click.option('--queue-threshold', type=(str, int), multiple=True,
              help='Threshold per queue in format --queue-threshold'
              + ' {queue_name} {threshold}. May be used multiple times')
@click.option('--sns-arn', '-s', help='ARN for SNS alert topic', required=True)
def check_queues(host, port, environment, deploy, max_metrics, threshold,
                 queue_threshold, sns_arn):

    thresholds = dict(queue_threshold)

    timeout = 1
    namespace = "celery/{}-{}".format(environment, deploy)
    redis_client = RedisWrapper(host=host, port=port, socket_timeout=timeout,
                                socket_connect_timeout=timeout)
    cloudwatch = CwBotoWrapper()
    metric_name = 'queue_length'
    dimension = 'queue'
    response = cloudwatch.list_metrics(Namespace=namespace,
                                       MetricName=metric_name,
                                       Dimensions=[{'Name': dimension}])
    existing_queues = []
    for m in response["Metrics"]:
        existing_queues.extend(
            [d['Value'] for d in m["Dimensions"] if (
                d['Name'] == dimension and
                not d['Value'].endswith(".pidbox") and
                not d['Value'].startswith("_kombu"))])

    redis_queues = set([k.decode() for k in redis_client.keys()
                        if (redis_client.type(k) == b'list' and
                            not k.decode().endswith(".pidbox") and
                            not k.decode().startswith("_kombu"))])

    all_queues = existing_queues + list(
        set(redis_queues).difference(existing_queues)
    )

    metric_data = []

    for queue_name in all_queues:
        metric_data.append({
            'MetricName': metric_name,
            'Dimensions': [{
                "Name": dimension,
                "Value": queue_name
            }],
            'Value': redis_client.llen(queue_name)
        })

    if len(metric_data) > 0:
        for metric_data_grouped in grouper(metric_data, max_metrics):
            print("metric_data {}".format(metric_data))
            cloudwatch.put_metric_data(Namespace=namespace, MetricData=metric_data)

    for queue in all_queues:
        dimensions = [{'Name': dimension, 'Value': queue}]
        queue_threshold = threshold
        if queue in thresholds:
            queue_threshold = thresholds[queue]
        # Period is in seconds
        period = 60
        evaluation_periods = 15
        comparison_operator = "GreaterThanThreshold"
        treat_missing_data = "notBreaching"
        statistic = "Maximum"
        actions = [sns_arn]
        alarm_name = "{}-{} {} queue length over threshold".format(environment,
                                                                   deploy,
                                                                   queue)

        print('Creating or updating alarm "{}"'.format(alarm_name))
        cloudwatch.put_metric_alarm(AlarmName=alarm_name,
                                    AlarmDescription=alarm_name,
                                    Namespace=namespace,
                                    MetricName=metric_name,
                                    Dimensions=dimensions,
                                    Period=period,
                                    EvaluationPeriods=evaluation_periods,
                                    TreatMissingData=treat_missing_data,
                                    Threshold=queue_threshold,
                                    ComparisonOperator=comparison_operator,
                                    Statistic=statistic,
                                    InsufficientDataActions=actions,
                                    OKActions=actions,
                                    AlarmActions=actions)

# Stolen right from the itertools recipes
# https://docs.python.org/3/library/itertools.html#itertools-recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    chunks = zip_longest(*args, fillvalue=fillvalue)
    # Remove Nones in function
    for chunk in chunks:
        yield [v for v in chunk if v is not None]

if __name__ == '__main__':
    check_queues()
