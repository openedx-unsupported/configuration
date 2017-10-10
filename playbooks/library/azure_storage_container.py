#!/usr/bin/env python

DOCUMENTATION = '''
---
module: azure_storage_container
short_description: create or delete a storage container in azure
description:
     - Creates or deletes storage containers. This module has a dependency on python-azure >= 0.7.1
version_added: "1.9"
options:
  name:
    description:
      - name of the container
    required: true
    default: null
  public_access:
    description:
      - the type of access allowed
    required: false
    default: null
  account_name:
    description:
      - name of the storage account
    required: true
    default: null
  account_key:
    description:
      - key used to access the storage account (either primary or secondary)
    required: true
    default: null
  state:
    description:
      - creates or destroys storage containers
    required: true
    default: 'present'
    aliases: []
requirements: [ "azure" ]
author: Darren Warner
'''

EXAMPLES = '''
# Note: None of these examples set account name or account key
# Create a storage account
- local_action:
    module: azure_storage_container
    name: my-container
    account_name: my-storage-account
    account_key: my-storage-account-key
# Delete a storage account
- local_action:
    module: azure_storage_container
    name: my-container
    account_name: my-storage-account
    account_key: my-storage-account-key
    state: absent
'''

import sys
import json

try:
    import azure as windows_azure

    from azure.common import AzureException
    from azure.common import AzureMissingResourceHttpError
    from azure.storage import (CloudStorageAccount)
except ImportError as a:
    print "failed=True msg='azure required for this module': %s" % (a)
    sys.exit(1)

def create_storage_container(module, azure):
    """
    Create a storage container
    module : AnsibleModule object
    azure: authenticated azure BlobService object
    Returns:
        True if a new container was created, false otherwise
    """
    name = module.params.get('name')
    public_access = module.params.get('public_access')

    storage_container = None
    try:
        storage_container = azure.get_container_properties(container_name=name)
    except AzureMissingResourceHttpError as e:
        pass  # no such container
    except AzureException as e:
        module.fail_json(msg="failed to find the storage container: %s" % str(e))

    if not storage_container:
        changed = True
        azure.create_container(container_name=name, x_ms_blob_public_access=public_access)
        storage_container = azure.get_container_properties(container_name=name)
    else:        
        changed = False

    return (changed, storage_container)

def delete_storage_container(module, azure):
    """
    Deletes a storage container
    module : AnsibleModule object
    azure: authenticated azure BlobService object
    Returns:
        True if a container was deleted
    """

    name = module.params.get('name')

    changed = False

    storage_container = None
    try:
        storage_container = azure.get_container_properties(container_name=name)
    except AzureMissingResourceHttpError as e:
        pass  # no such service
    except AzureException as e:
        module.fail_json(msg="failed to find the storage container: %s" % str(e))

    if storage_container:
        changed = True
        result = azure.delete_container(container_name=name, fail_not_exist=True)

    return changed, storage_container

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            public_access=dict(choices=['container', 'blob']),
            account_name=dict(required=True),
            account_key=dict(required=True),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )
    
    account_name = module.params.get('account_name')
    account_key = module.params.get('account_key')

    azure = CloudStorageAccount(account_name, account_key).create_blob_service()

    if module.params.get('state') == 'absent':
        (changed, storage_container) = delete_storage_container(module, azure)

    elif module.params.get('state') == 'present':
        (changed, storage_container) = create_storage_container(module, azure)

    module.exit_json(changed=changed, storage_container=json.loads(json.dumps(storage_container, default=lambda o: o.__dict__)))


# import module snippets
from ansible.module_utils.basic import *

main()

