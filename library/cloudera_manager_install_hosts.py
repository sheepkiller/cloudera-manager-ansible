#!/usr/bin/python
# cloudera_manager_hosts: Install agents and add hosts to Cloudera Manager

DOCUMENTATION = '''
---
module: cloudera_manager_hosts
short_description: Install agents and add hosts to Cloudera Manager
description:
    - Install agents and add hosts to Cloudera Manager
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
    hosts:
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
        - The Cloudera Manager repository URL to use
      require: False
      default: null
    gpg_key_custom_url:
      description
        -  GPG key of Cloudera Manager repositor
      require: False
      default: null
    java_strategy:
      description
        - Strategy to use for JDK installation.
      require: False
      default: null
    unlimited_jce: Flag for unlimited strength JCE policy files installation
      description
        - NOT TESTED. Flag for unlimited strength JCE policy files installation
      require: False
      default: null
    parallel_install_count:
      description:
        - Number of simultaneous installations.
      required: False
      default: 1
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
    hosts: my-node
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

class cmInstall(object):

    def __init__(self, module):
        self.changed = False
        self.module = module
        self.cm_host = module.params.get('cm_host')
        self.cm_port = module.params.get('cm_port')
        self.cm_username = module.params.get('cm_username')
        self.cm_password = module.params.get('cm_password')
        self.cm_tls = module.params.get('cm_tls')
        self.cm_version = module.params.get('cm_version')
        self.hosts = module.params.get('hosts')
        self.username = module.params.get('username')
        self.sshport = module.params.get('sshport')
        self.password = module.params.get('password')
        self.private_key = module.params.get('private_key')
        self.passphrase = module.params.get('passphrase')
        self.cm_repo_url = module.params.get('cm_repo_url')
        self.gpg_key_custom_url = module.params.get('gpg_key_custom_url')
        self.java_strategy = module.params.get('java_strategy')
        self.unlimited_jce = module.params.get('unlimited_jce')
        self.parallel_install_count = module.params.get('parallel_install_count')
        self.hosts_to_install = self.hosts
        self.hosts_reply = dict()
        try:
            self.cm_conn = ApiResource(self.cm_host, server_port=self.cm_port,
                                  username=self.cm_username, password=self.cm_password,
                                  use_tls=self.cm_tls, version=self.cm_version)
            self.cms = ClouderaManager(self.cm_conn)
        except ApiException as e:
            self.module.fail_json(changed=self.changed,
                             msg="Can't connect to API: {}".format(e))

    def clean_hosts(self, postinstall=False):
        _hosts = hosts.get_all_hosts(self.cm_conn)
        cm_hosts = dict()
        for k in range (len(_hosts)):
            h = dict()
            for (key, value) in _hosts[k].__dict__.items():
                if isinstance(value, basestring):
                    h[key] = value
            cm_hosts[_hosts[k].hostname] = h

        for k in range (len(self.hosts_to_install)):
            if self.hosts_to_install[k] in cm_hosts:
                self.hosts_reply[self.hosts_to_install[k]] = cm_hosts[self.hosts_to_install[k]]
                self.hosts_to_install.pop(k)
        if postinstall == False:
            if len(self.hosts_to_install) == 0:
                self.module.exit_json(changed=False, msg="hosts already exist", hosts=self.hosts_reply)



    def do_install(self):
        try:
            cmd = self.cms.host_install(user_name=self.username, host_names=self.hosts_to_install,
                ssh_port=self.sshport, password=self.password,
                private_key=self.private_key, passphrase=self.passphrase,
                parallel_install_count=self.parallel_install_count, cm_repo_url=self.cm_repo_url,
                gpg_key_custom_url=self.gpg_key_custom_url,
                java_install_strategy=self.java_strategy,
                unlimited_jce=self.unlimited_jce)
            cmd = cmd.wait()
            cmd = cmd.fetch()
            if cmd.success != True:
                self.module.fail_json(changed=False, msg=cmd.resultMessage)
            self.clean_hosts(postinstall=True)
            self.module.exit_json(changed=True, msg=cmd.resultMessage, hosts=self.hosts_reply)
        except ApiException as e:
            self.module.fail_json(changed=changed, msg="{}".format(e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cm_host=dict(required=True, type='str'),
            cm_port=dict(required=False, type='int', default=7180),
            cm_username=dict(required=True, type='str'),
            cm_password=dict(required=True, type='str', no_log=True),
            cm_tls=dict(required=False, type='bool', default=False),
            cm_version=dict(required=False, type='int', default=10),
            hosts=dict(required=True, type='list'),
            username=dict(required=True, type='str'),
            sshport=dict(required=False, type='int', default=22),
            password=dict(required=False, type='str', no_log=True),
            private_key=dict(required=False, type='str', no_log=True),
            passphrase=dict(required=False, type='str', no_log=True),
            cm_repo_url=dict(required=False, type='str'),
            gpg_key_custom_url=dict(required=False, type='str'),
            java_strategy=dict(required=False, type='str'),
            unlimited_jce=dict(required=False, type='str'),
            parallel_install_count=dict(required=False, type='int', default=1)
        )
        ,
        mutually_exclusive = [
                              ['password','private_key'],
                              ['password','passphrase'],
                             ]
    )

    changed = False

    cm_conn = cmInstall(module)
    cm_conn.clean_hosts()
    cm_conn.do_install()

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
main()
