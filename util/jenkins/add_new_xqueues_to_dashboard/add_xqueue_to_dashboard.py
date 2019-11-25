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


def generate_dashboard_widget_metrics(
    cloudwatch,
    namespace,
    metric_name,
    dimension_name,
    properties={},
    right_axis_items=[]
):
    pp = pprint.PrettyPrinter(indent=4)

    metrics = cloudwatch.list_metrics(
        Namespace=namespace, MetricName=metric_name, Dimensions=[{"Name": dimension_name}]
    )

    values = []

    for metric in metrics['Metrics']:
        for dimension in metric['Dimensions']:
            if dimension['Name'] == dimension_name:
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
    height,
    width=24,
    stacked=False,
    region='us-east-1',
    period=60,
    right_axis_items=[]
):
    return {'type': 'metric', 'height': height, 'width': width, 'x': x, 'y': y,
            'properties': {
                 'period': period, 'view': 'timeSeries', 'stacked': stacked, 'region': region,
                 'title': "{} (auto-generated)".format(title),
                 'metrics': generate_dashboard_widget_metrics(cloudwatch, namespace, metric_name, dimension_name,
                                                              metrics_properties, right_axis_items=right_axis_items)
                 }
            }


@click.command()
@click.option('--environment', '-e', required=True)
@click.option('--deploy', '-d', required=True,
              help="Deployment (i.e. edx or stage)")
def generate_dashboard(environment, deploy):
    pp = pprint.PrettyPrinter(indent=4)
    cloudwatch = CwBotoWrapper()

    dashboard_name = "{}-{}-xqueues".format(environment, deploy)
    xqueue_namespace = "xqueue/{}-{}".format(environment, deploy)

    widgets = []
    y_cord = 0
    height = 9

    if deploy == 'edx' and environment == 'prod':
        y_cord += height
        height = 9

        widgets.append(generate_dashboard_widget(cloudwatch, y=y_cord, height=height,
                                                 title="{}-{} Xqueue Queues".format(environment, deploy),
                                                 namespace=xqueue_namespace, metric_name="queue_length",
                                                 dimension_name="queue",
                                                 )
                       )

    dashboard_body = {'widgets': widgets}

    print("Dashboard Body")
    pp.pprint(dashboard_body)

    cloudwatch.put_dashboard(DashboardName=dashboard_name,
                             DashboardBody=json.dumps(dashboard_body))


if __name__ == '__main__':
    generate_dashboard()
