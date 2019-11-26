from __future__ import absolute_import
from __future__ import print_function
import click
import yaml
import json
from collections import defaultdict
import six

@click.command()
@click.option('--files', '-m', multiple=True)
def check_for_yaml_key_collisions(files):
    values_for_keys = defaultdict(lambda: [])
    for file_path in files:
        content = None
        if file_path.endswith(".yml") or file_path.endswith(".yaml"):
            stream = open(file_path, 'r')
            content = yaml.safe_load(stream)
        elif file_path.endswith(".json"):
            with open(file_path, "r") as read_file:
                content = json.load(read_file)
        for key, value in six.iteritems(content):
            values_for_keys[key].append(value)

    collisions = {}

    for key,value in six.iteritems(values_for_keys):
        if len(value) > 1:
            collisions[key] = value


    if len(list(collisions.keys())) > 0:
        print((str.format("Found key collisions: {}", len(collisions))))
        for key,value in six.iteritems(collisions):
            print((str.format("{} {}", key, value)))
        exit(1)
    else:
        print("No collisions found")
        exit(0)

if __name__ == '__main__':
    check_for_yaml_key_collisions()
