from __future__ import absolute_import
from __future__ import print_function
import pprint
import re

import boto3
import botocore
import backoff
import click
import json

MAX_TRIES = 1

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
    def put_dashboard(self, *args, **kwargs):
        return self.client.put_dashboard(*args, **kwargs)

def generate_dashboard_widget_metrics(cloudwatch, namespace, metric_name, dimension_name, properties={}, include_filter=None, exclude_filter=None, right_axis_items=[]):
    # https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/CloudWatch-Dashboard-Body-Structure.html#CloudWatch-Dashboard-Properties-Metrics-Array-Format
    # [Namespace, MetricName, [{DimensionName,DimensionValue}...] [Rendering Properties Object] ]
    # ['AWS/EC2', 'CPUUtilization', 'AutoScalingGroupName', 'asg-name', {'period': 60}]
    pp = pprint.PrettyPrinter(indent=4)

    metrics = cloudwatch.list_metrics(
        Namespace=namespace, MetricName=metric_name, Dimensions=[{"Name": dimension_name}]
    )

    values = []

    for metric in metrics['Metrics']:
        for dimension in metric['Dimensions']:
            if dimension['Name'] == dimension_name:
                if include_filter is None or re.search(include_filter, dimension['Value'], re.IGNORECASE):
                    if exclude_filter is None or not re.search(exclude_filter, dimension['Value'], re.IGNROECASE):
                        values.append(dimension['Value'])

    values.sort()

    new_widget_metrics = []
    for value in values:
        value_properties = properties.copy()
        value_properties['label'] = value
        if value in right_axis_items:
            value_properties["yAxis"] = "right"
        new_widget_metrics.append([namespace, metric_name, dimension_name, value, value_properties])

    return new_widget_metrics

# * means that all arguments after cloudwatch are keyword arguments only and are not positional
def generate_dashboard_widget(
    cloudwatch,
    *,
    x=0,
    y,
    title,
    namespace,
    metric_name,
    dimension_name,
    metrics_properties={},
    include_filter=None,
    exclude_filter=None,
    height,
    width=24,
    stacked=False,
    region='us-east-1',
    period=60,
    right_axis_items=[]
):
    return { 'type': 'metric', 'height': height, 'width': width, 'x': x, 'y': y,
    'properties': {
        'period': period, 'view': 'timeSeries', 'stacked': stacked, 'region': region,
        'title': "{} (auto-generated)".format(title),
        'metrics': generate_dashboard_widget_metrics(cloudwatch, namespace, metric_name, dimension_name, metrics_properties,
            include_filter=include_filter, exclude_filter=exclude_filter, right_axis_items=right_axis_items)
    }
}

@click.command()
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or edge)")
def generate_dashboard(environment, deploy):
    pp = pprint.PrettyPrinter(indent=4)
    cloudwatch = CwBotoWrapper()

    dashboard_name = "{}-{}-queues".format(environment, deploy)
    celery_namespace = "celery/{}-{}".format(environment, deploy)
    xqueue_namespace = "xqueue/{}-{}".format(environment, deploy)

    widgets = []
    width = 24
    y_cord = 0
    region = "us-east-1"
    right_axis_items=["edx.lms.core.ace", "edx.lms.core.background_process"]
    right_axis_items_age=[]

    height = 9

    cpu_widget = generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
        title="{}-{}-Worker ASG Average CPU".format(environment, deploy),
        namespace="AWS/EC2", metric_name="CPUUtilization", dimension_name="AutoScalingGroupName",
        include_filter="{}-{}-Worker".format(environment, deploy)
    )

    cpu_widget['properties']['annotations'] = {
        'horizontal': [
            {'label': 'Scale Up', 'value': 90, 'color': '#d62728'},
            {'label': 'Scale Down', 'value': 45, 'color': '#2ca02c'}
        ]
    }

    cpu_widget['properties']['yAxis'] = {'left': {'min': 0, 'max': 100}}

    widgets.append(cpu_widget)

    y_cord += height
    height = 6

    worker_count_widget = generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
        title="{}-{}-Worker Count".format(environment, deploy),
        namespace=celery_namespace, metric_name="count", dimension_name="workers"
    )

    worker_count_widget['properties']['stacked'] = True

    widgets.append(worker_count_widget)

    y_cord += height
    height = 9

    widgets.append(generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
        title="{}-{} All Celery Queues".format(environment, deploy),
        namespace=celery_namespace, metric_name="queue_length", dimension_name="queue",
        right_axis_items=right_axis_items
    ))

    y_cord += height
    height = 9

    widgets.append(generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
        title="{}-{} All Queues Next Task Age".format(environment, deploy),
        namespace=celery_namespace, metric_name="next_task_age", dimension_name="queue",
        right_axis_items=right_axis_items_age
    ))

    y_cord += height
    height = 9

    widgets.append(generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
        title="{}-{} LMS Queues".format(environment, deploy),
        namespace=celery_namespace, metric_name="queue_length", dimension_name="queue",
        include_filter="^edx.lms",
        right_axis_items=right_axis_items
    ))

    y_cord += height
    height = 9

    widgets.append(generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
        title="{}-{} CMS Queues".format(environment, deploy),
        namespace=celery_namespace, metric_name="queue_length", dimension_name="queue",
        include_filter="^edx.cms",
        right_axis_items=right_axis_items
    ))

    if deploy == 'edx' and environment == 'prod':
        y_cord += height
        height = 9

        widgets.append(generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
            title="{}-{} Xqueue Queues".format(environment, deploy),
            namespace=xqueue_namespace, metric_name="queue_length", dimension_name="queue",
        ))


    if deploy in ["edx", "edge"]:
        y_cord += height
        height = 9

        widgets.append(generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
            title="{}-{} Ecommerce".format(environment, deploy),
            namespace=celery_namespace, metric_name="queue_length", dimension_name="queue",
            include_filter="^ecommerce\.",
        ))

        y_cord += height
        height = 9

        widgets.append(generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
            title="{}-{} Legacy Celery (Ecommerce) should be 0".format(environment, deploy),
            namespace=celery_namespace, metric_name="queue_length", dimension_name="queue",
            include_filter="celery",
        ))

    dashboard_body = { 'widgets': widgets }

    print("Dasboard Body")
    pp.pprint(dashboard_body)

    cloudwatch.put_dashboard(DashboardName=dashboard_name, DashboardBody=json.dumps(dashboard_body))

if __name__ == '__main__':
    generate_dashboard()
