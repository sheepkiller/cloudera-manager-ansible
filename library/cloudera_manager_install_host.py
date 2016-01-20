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
    host:
      description:
        - Host to deploy Cloudera Manager Agent
      required: true
    username:
      description:
        - user name to connect with via ssh
      required: true
    sshport:
      description:
        - ssh port to connect to
      required: false
      default: 22
    password:
      description:
        - password
      required: false
      default: null
    private_key:
      description:
        - private key to auth
      required: False
      default: null
    passphrase:
      description:
        - passphrase for the private key (if any)
      require: False
      default: null
    cm_repo_url:
      description
        - url of Cloudera Manager repo
      require: False
      default: null
    gpg_key_custom_url:
      description
        -  GPG key of Cloudera Manager repo
      require: False
      default: null
    java_strategy:
      description
        - NOT TESTED
      require: False
      default: null
    unlimited_jce:
      description
        - NOT TESTED
      require: False
      default: null
'''

EXAMPLES = '''
# Install Cloudera manager Agent
- name: add hosts to clusters
  cloudera_manager_install_host:
    cm_host: cm.example.com
    cm_username: admin
    cm_password: my-password"
    username: root
    password: root_password
    host: my-node
    cm_repo_url: https://archive.cloudera.com/cm5/redhat/7/x86_64/cm/5
'''

import os
import time
import syslog
import sys

try:
    from cm_api.api_client import *
    from cm_api.endpoints.cms import ClouderaManager
    from cm_api.endpoints.hosts import *
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
            host=dict(required=True, type='list'),
            username=dict(required=True, type='str'),
            sshport=dict(required=False, type='str', default='22'),
            password=dict(required=False, type='str'),
            private_key=dict(required=False, type='str'),
            passphrase=dict(required=False, type='str'),
            cm_repo_url=dict(required=False, type='str'),
            gpg_key_custom_url=dict(required=False, type='str'),
            java_strategy=dict(required=False, type='str'),
            unlimited_jce=dict(required=False, type='str')
        )
        ,
        mutually_exclusive = [
                              ['password','private_key'],
                              ['password','passphrase'],
                             ]
    )

    cm_host = module.params.get('cm_host')
    cm_port = module.params.get('cm_port')
    cm_username = module.params.get('cm_username')
    cm_password = module.params.get('cm_password')
    cm_tls = module.params.get('cm_tls')
    cm_version = module.params.get('cm_version')
    host = module.params.get('host')
    username = module.params.get('username')
    sshport = module.params.get('sshport')
    password = module.params.get('password')
    private_key = module.params.get('private_key')
    passphrase = module.params.get('passphrase')
    cm_repo_url = module.params.get('cm_repo_url')
    gpg_key_custom_url = module.params.get('gpg_key_custom_url')
    java_strategy = module.params.get('java_strategy')
    unlimited_jce = module.params.get('unlimited_jce')



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

    _hosts = hosts.get_all_hosts(cm_conn)
    cm_hosts = dict()
    for k in range (len(_hosts)):
        h = dict()
        for (key, value) in _hosts[k].__dict__.items():
            if isinstance(value, basestring):
                h[key] = value
        cm_hosts[_hosts[k].hostname] = h

    rc_hosts = dict()
    for k in range (len(host)):
        if host[k] in cm_hosts:
            rc_hosts[host[k]] = cm_hosts[host[k]]
            host.pop(k)

    if len(host) == 0:
        module.exit_json(changed=False, msg="host already exist", host=rc_hosts)

    try:
        cmd = cms.host_install(user_name=username, host_names=host,
            ssh_port=sshport, password=password,
            private_key=private_key, passphrase=passphrase,
            parallel_install_count=1, cm_repo_url=cm_repo_url,
            gpg_key_custom_url=gpg_key_custom_url,
            java_install_strategy=java_strategy,
            unlimited_jce=unlimited_jce)
        cmd = cmd.wait()
        cmd = cmd.fetch()
        if cmd.success != True:
            module.fail_json(changed=False, msg=cmd.resultMessage)
        module.exit_json(changed=True, msg=cmd.resultMessage)
    except ApiException as e:
        module.fail_json(changed=changed, msg="{}".format(e))

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
main()
