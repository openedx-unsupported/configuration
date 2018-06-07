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
        self.client = boto3.client('cloudwatch')

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=max_tries)
    def list_metrics(self, *args, **kwargs):
        return self.client.list_metrics(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=max_tries)
    def put_metric_data(self, *args, **kwargs):
        return self.client.put_metric_data(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=max_tries)
    def describe_alarms_for_metric(self, *args, **kwargs):
        return self.client.describe_alarms_for_metric(*args, **kwargs)

    @backoff.on_exception(backoff.expo,
                          (botocore.exceptions.ClientError),
                          max_tries=max_tries)
    def put_metric_alarm(self, *args, **kwargs):
        return self.client.put_metric_alarm(*args, **kwargs)


@click.command()
@click.option('--host', '-h', default='localhost',
              help='Hostname of redis server')
@click.option('--port', '-p', default=6379, help='Port of redis server')
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
@click.option('--max-metrics', default=30,
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
            [d['Value'] for d in m["Dimensions"] if d['Name'] == dimension])

    redis_queues = set([k.decode() for k in redis_client.keys()
                        if redis_client.type(k) == b'list'])

    all_queues = existing_queues + list(
        set(redis_queues).difference(existing_queues)
    )

    if len(all_queues) > max_metrics:
        # TODO: Use proper logging framework
        print("Warning! Too many metrics, refusing to publish more than {}"
              .format(max_metrics))

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
            'Value': redis_client.llen(queue)
        })

    if len(metric_data) > 0:
        cloudwatch.put_metric_data(Namespace=namespace, MetricData=metric_data)

    for queue in queues:
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


if __name__ == '__main__':
    check_queues()
