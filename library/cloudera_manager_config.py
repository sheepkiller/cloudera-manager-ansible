#!/usr/bin/python
# cloudera_manager_users: manage cloudera manager config

DOCUMENTATION = '''
---
module: cloudera_manager_config
short_description: Configure Cloudera Manager
description:
    - Configure Cloudera Manager
options:
    cm_host:
      description:
        - Cloudera Manager hostname.
      required: true
      default: null
    cm_port:
      description:
        - Cloudera Manager port.
      required: false
      default: 7180
    cm_username:
      description:
        - Cloudera Manager user.
      required: true
      default: null
    cm_password:
      description:
        - Cloudera Manager password.
      required: true
      default: null
    cm_tls:
      description:
        - Use TLS to connect to Cloudera Manager. You may need to set cm_port.
      required: false
      default: false
    cm_version:
      description:
        - Version of API to use. Currently, cm_api (python) is 10.
      required: false
      default: 10
    name:
      description:
        - Name of configuration setting you want to modify.
      required: false
      default: null
    value:
      description:
        - Value of configuration setting (required if `name` is set).
      required: false
      default: null
    state:
      description:
        - whether to ensure the configurations setting is present or absent (factory default), or list all settings.
      required: false
      default: present
      choices: ['present', 'absent', 'list']
'''

EXAMPLES = '''
# Retrieve the Cloudera Manager settings
- cloudera_manager_config:
    cm_host: cm.example.com
    cm_username: admin
    cm_password: my-password
    state: list
  register: cm

# set CUSTOM_HEADER_COLOR to RED
 - cloudera_manager_config:
    cm_host: cm.example.com
    cm_username: admin
    cm_password: my-password
    name: CUSTOM_HEADER_COLOR
    state: present
    value: RED

# set CUSTOM_HEADER_COLOR to defaut
- cloudera_manager_config:
    cm_host: cm.example.com
    cm_username: admin
    cm_password: my-password
    name: CUSTOM_HEADER_COLOR
    state: absent
'''

import os
import time
import syslog
import sys

try:
    from cm_api.api_client import *
    from cm_api.endpoints.cms import ClouderaManager
    from cm_api.endpoints.types import config_to_json, ApiConfig
    HAS_CM_API = True
except ImportError:
    HAS_CM_API = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cm_host=dict(required=True, type='str'),
            cm_port=dict(required=False, type='int', default=7180),
            cm_username=dict(required=True, type='str'),
            cm_password=dict(required=True, type='str'),
            cm_tls=dict(required=False, type='bool', default=False),
            cm_version=dict(required=False, type='int', default=10),
            name=dict(required=False, type='str'),
            value=dict(required=False, type='str'),
            state=dict(default='present',
                       choices=['present', 'absent', 'list'])
        )
    )

    cm_host = module.params.get('cm_host')
    cm_port = module.params.get('cm_port')
    cm_username = module.params.get('cm_username')
    cm_password = module.params.get('cm_password')
    cm_tls = module.params.get('cm_tls')
    cm_version = module.params.get('cm_version')
    cm_config_key = module.params.get('name')
    cm_config_value = module.params.get('value')
    state = module.params.get('state')

    changed = False

    if not HAS_CM_API:
        module.fail_json(changed=changed, msg='cm_api required for this module')

    try:
        cm_conn = ApiResource(cm_host, server_port=cm_port,
                              username=cm_username, password=cm_password,
                              use_tls=cm_tls, version=cm_version)
        cms = ClouderaManager(cm_conn)
    except ApiException as e:
        module.fail_json(changed=changed,
                         msg="Can't connect to API: {}".format(e))

    try:
        _settings = cms.get_config('full')
    except ApiException as e:
        module.fail_json(changed=changed, msg="{}".format(e))

    _settings = cms.get_config('full')
    settings = dict()
    for key in _settings:
        settings[key] = dict()
        settings[key]['name'] = _settings[key].name
        settings[key]['default'] = _settings[key].default
        settings[key]['value'] = None
        if _settings[key].value is not None:
            settings[key]['value'] = _settings[key].value

    if state == 'list':
        module.exit_json(changed=changed, settings=settings)

    if cm_config_key is None:
        module.fail_json(changed=changed, msg='Missing `name` option.')

    if cm_config_key not in settings:
        module.fail_json(changed=changed,
                         msg='{} is not a valid configuration entry'.format(cm_config_key))

    if state == "absent":
        cm_config_value = None
    elif cm_config_value is None:
        module.fail_json(changed=changed, msg='Missing `value` option.')

    if cm_config_value != settings[cm_config_key]['value']:
        try:
            update = dict()
            update[cm_config_key] = cm_config_value
            rc = cms.update_config(update)
            module.exit_json(changed=True, settings=rc)
        except Exception as e:
            module.fail_json(changed=False, msg="{}".format(e))
    module.exit_json(changed=False, settings=cms.get_config('summary'))

# import module snippets
from ansible.module_utils.basic import *
main()
