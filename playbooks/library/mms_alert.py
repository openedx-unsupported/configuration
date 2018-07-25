#!/usr/bin/env python

DOCUMENTATION = """
---
module: mms_alert
short_description: 
description:
version_added: "1.9.3"
author: Edward Zarecor
options:
"""

EXAMPLES = '''
'''

from ansible.module_utils.basic import *
import json
from json import JSONEncoder
import requests

class CloudManagerClient(object):
    def __init__(self, base_url, group_id, api_user, api_key):
        self.base_url = base_url + "/api/public/v1.0"
        self.group_id = group_id
        self.http_digest_auth = requests.auth.HTTPDigestAuth(api_user, api_key)

    def get(self, path):
        api_target = self.base_url + path
        r = requests.get(api_target, auth=self.http_digest_auth)
        return r.json()

    def put():
        pass

    def post(self, path, data):
        api_target = self.base_url + path
        return json.dumps(data, cls=MyEncoder)
        #r = requests.post(api_target, auth=self.http_digest_auth, data=data)
        
    def delete():
        pass


class ArgumentError(Exception):
    pass


#
# TODO: make work recursively
# TODO: make export the models
#
class CommonEqualityMixin(object):

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

class Alert(CommonEqualityMixin):
    def __init__(self, id, group_id, alert_config_id, type_name, event_type_name, status):
        self.id = id
        self.group_id = group_id
        self.alert_config_id = alert_config_id
        self.type_name = type_name
        self.event_type_name = event_type_name
        self.status = status


class AlertConfiguration(CommonEqualityMixin):
    def __init__(self, group_id, type_name, event_type_name, enabled, matchers, notifications):
        self.group_id = group_id
        self.type_name = type_name
        self.event_type_name = event_type_name
        self.enabled = enabled
        self.matchers = matchers
        self.notifications = notifications

class AlertMatcher(CommonEqualityMixin):
    def __init__(self, field_name, operator, value):
        self.field_name = field_name
        self.operator = operator
        self.value = value

class AlertNotification(object):
    def __init__(self, type_name, email_address, interval_min, delay_min):
        self.type_name = type_name;
        self.email_address = email_address
        self.interval_min = interval_min
        self.delay_min = delay_min

class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__ 

def create_or_update_alert_config(client):
    
    matcher0 = AlertMatcher("foo","bar","baz")
    notification0 = AlertNotification("EMAIL", "ed@example.com", 60, 5)
    alert0 = AlertConfiguration("foo", "REPLICA_SET", "RESYNC_REQUIRED", True, [], [])


    matcher1 = AlertMatcher("foo","bar","baz")
    notification1 = AlertNotification("EMAIL", "ed@example.com", 60, 5)
    alert1 = AlertConfiguration("foo", "REPLICA_SET", "RESYNC_REQUIRED", True, [], [])

    raise Exception(alert0 == alert1)

    return client.post('/groups/1111/alertConfigs', alert0)
    

def main():

    arg_spec = dict(
        state=dict(required=True, type='str'),
        base_url=dict(required=True, type='str'),
        group_id=dict(required=True, type='str'),
        api_user=dict(required=True, type='str'),
        api_key=dict(required=True, type='str'),
        matchers=dict(type='list'),
        notifications=dict(type='list'),
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=False)

    state = module.params.get('state')
    base_url = module.params.get('base_url')
    group_id = module.params.get('group_id')
    api_user = module.params.get('api_user')
    api_key = module.params.get('api_key')
    matchers = module.params.get('matchers')
    notifications = module.params.get('notifications')

    c = CloudManagerClient(base_url, group_id, api_user, api_key)

    create_or_update_alert_config(c)

    #module.exit_json(api_output = c.get('/groups/{group_id}/alertConfigs'.format(group_id=group_id)))
    module.exit_json(api_output = create_or_update_alert_config(c))

main()
