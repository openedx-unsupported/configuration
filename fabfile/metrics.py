import boto
from .ec2 import instance_id


def instance_tags_for_current_host():
    """
    Returns the datadog style tags for the active host
    """
    return instance_tags([instance_id()])


def instance_tags(instance_ids):
    """
    Returns datadog style tags for the specified instances
    """
    ec2 = boto.connect_ec2()

    tags = set()
    for res in ec2.get_all_instances(instance_ids):
        for instance in res.instances:
            ec2_tags = instance.tags

            tags.add('instance_id:' + instance.id)
            if 'group' in ec2_tags:
                tags.add('fab-group:' + ec2_tags['group'])
            if 'environment' in ec2_tags:
                tags.add('fab-environment:' + ec2_tags['environment'])
            if 'variant' in ec2_tags:
                tags.add('fab-variant:' + ec2_tags['variant'])

    return list(tags)
