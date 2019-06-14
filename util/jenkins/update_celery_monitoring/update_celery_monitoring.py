import re
import redis
import click
import boto3
import botocore
import backoff
from pprint import pprint
from itertools import zip_longest
from collections import defaultdict

MAX_TRIES = 5


# Queues that should be gone. Inclusion in this list will stop this script from
# zero filling them, but if they are >0 they will still get tracked
queue_blacklist = ['celery', 'ecommerce']

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


class Ec2BotoWrapper(object):
    def __init__(self):
        self.client = boto3.client('ec2')

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=MAX_TRIES)
    def describe_instances(self, *args, **kwargs):
        return self.client.describe_instances(*args, **kwargs)


def count_workers(environment, deploy, cluster):
    ec2 = Ec2BotoWrapper()

    counts_by_play = defaultdict(int)

    reservations = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:environment', 'Values': [environment]},
            {'Name': 'tag:deployment', 'Values': [deploy]},
            {'Name': 'tag:cluster', 'Values': [cluster]},
            {'Name': 'instance-state-name', 'Values': ['running']},
        ]
    )['Reservations']

    for reservation in reservations:
        for instance in reservation["Instances"]:
            tag_asg = None
            for tag in instance['Tags']:
                if tag.get('Key') == 'aws:autoscaling:groupName':
                    # Reduce number of metrics from 1000 to 10 by changing first 2 numbers of ASG version to stars
                    # This reduces the cloudwatch cost
                    tag_asg = re.sub('-v[0-9]{2}', '-v**', tag.get('Value'))
                    counts_by_play[tag_asg] += 1

    metric_data = []

    for play, num_workers in counts_by_play.items():
        metric_data.append({
            'MetricName': 'count',
            'Dimensions': [{
                "Name": "workers",
                "Value": play
            }],
            'Value': num_workers
            }
        )

    return metric_data

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
    redis_client = RedisWrapper(host=host, port=port, socket_timeout=timeout,
                                socket_connect_timeout=timeout)
    cloudwatch = CwBotoWrapper()
    namespace = "celery/{}-{}".format(environment, deploy)
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
                not d['Value'] in queue_blacklist and
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
            'Value': redis_client.llen(queue_name),
            'Unit': 'Count',
        })

    if len(metric_data) > 0:
        for metric_data_grouped in grouper(metric_data, max_metrics):
            print("metric_data:")
            pprint(metric_data, width=120)
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

    # Track number of worker instances so it can be graphed in CloudWatch
    workers_metric_data = count_workers(environment, deploy, 'worker')
    print("workers_metric_data:")
    pprint(workers_metric_data, width=120)
    cloudwatch.put_metric_data(Namespace=namespace, MetricData=workers_metric_data)


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
