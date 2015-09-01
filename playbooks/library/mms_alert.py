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

    def post():
        pass
        
    def delete():
        pass


class ArgumentError(Exception):
    pass

def main():

    arg_spec = dict(
        base_url=dict(required=True, type='str'),
        group_id=dict(required=True, type='str'),
        api_user=dict(required=True, type='str'),
        api_key=dict(required=True, type='str'),
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=False)

    base_url = module.params.get('base_url')
    group_id = module.params.get('group_id')
    api_user = module.params.get('api_user')
    api_key = module.params.get('api_key')

    c = CloudManagerClient(base_url, group_id, api_user, api_key)
    module.exit_json(api_output = c.get('/groups/{group_id}/alertConfigs'.format(group_id=group_id)))

main()
