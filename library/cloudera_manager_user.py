#!/usr/bin/python
# cloudera_manager_users: manage cloudera manager users

DOCUMENTATION = '''
---
module: cloudera_manager_users
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
    state:
      description:
        - whether to ensure the user is present or absent, or list all users.
      required: false
      default: present
      choices: ['present', 'absent', 'list']
    name:
      description:
        - Name of the user to create, remove or modify.
      required: false
      default: null
      aliases: [ user ]
    password:
      description:
        - passord for user. By without `force_password_update`, password is set only when user is created.
      required: false
      defaut: null
    roles:
      description:
        - List of role(s) attached to user.
      required: false
      defaut: null
    force_password_update:
      description:
        - Force password update everytime.
      required: false
      defaut: False
'''
EXAMPLES = '''
# list Clouder manager users
- cloudera_manager_users:
    cm_host: cm.example.com
    cm_username: admin
    cm_password: "my-password"
    state: list
  register: cm_users

# create user or update it when roles change
- cloudera_manager_users:
    cm_host: cm.example.com
    cm_username: admin
    cm_password: my-password
    name: my_second_admin
    password: insecure
    state: present
    roles: ROLE_ADMIN

# create user or update it
- cloudera_manager_users:
    cm_host: cm.example.com
    cm_username: admin
    cm_password: my-password
    name: my_second_admin
    password: insecure
    force_password_update: true
    state: present
    roles: ROLE_ADMIN
'''


import os
import time
import syslog
import sys

try:
    from cm_api.api_client import *
    from cm_api.endpoints import users
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
            force_password_update=dict(required=False, type='bool', default=False),
            cm_version=dict(required=False, type='int', default=10),
            name=dict(required=False, type='str', aliases=[ 'user' ]),
            password=dict(required=False, type='str'),
            roles=dict(required=False, type='list', default=None),
            state=dict(default='present', choices=['present', 'absent', 'list'])
        )
    )

    cm_host = module.params.get('cm_host')
    cm_port = module.params.get('cm_port')
    cm_username = module.params.get('cm_username')
    cm_password = module.params.get('cm_password')
    cm_tls = module.params.get('cm_tls')
    force_password_update = module.params.get('force_password_update')
    cm_version = module.params.get('cm_version')
    username = module.params.get('name')
    password = module.params.get('password')
    roles = module.params.get('roles')
    state = module.params.get('state')

    changed = False

    if not HAS_CM_API:
        module.fail_json(changed=changed, msg='cm_api required for this module')

    try:
        cm_conn = ApiResource(cm_host, server_port=cm_port,
                              username=cm_username, password=cm_password,
                              use_tls=cm_tls, version=cm_version)
    except ApiException as e:
        module.fail_json(changed=changed,
                         msg="Can't connect to API: {}".format(e))

    if state == 'list':
        users_list = []
        ulist = cm_conn.get_all_users(view='export')
        for i in range(len(ulist)):
            u = dict()
            u['username'] = ulist[i].name
            u['roles'] = ulist[i].roles
            users_list.append(u)
        module.exit_json(changed=changed, users=users_list)
    user_exists = False
    cur_user = None

    try:
        cur_user = cm_conn.get_user(username)
        user_exists = True
    except ApiException as e:
        if str(e) != "User '" + username + "' does not exist. (error 404)":
            module.fail_json(changed=changed, msg='{}'.format(e))

    if state == "absent":
        if user_exists:
            try:
                cm_conn.delete_user(username)
                module.exit_json(changed=True, msg="user is deleted")
            except:
                module.fail_json(changed=changed, msg='{}'.format(e))
    else:
        if user_exists:
            if roles != cur_user.roles:
                try:
                    if not force_password_update:
                        password = None
                    updated_user = users.ApiUser(cm_conn, username, password, roles)
                    users.update_user(cm_conn, updated_user)
                    module.exit_json(changed=True, msg="role updated")
                except ApiException as e:
                    module.fail_json(changed=changed, msg="{}".format(e))
            else:
                module.exit_json(changed=False)
        else:
            try:
                cm_conn.create_user(username, password, roles)
            except ApiException as e:
                module.fail_json(changed=True, msg="{}".format(e))
    module.exit_json(changed=True, msg="user is created")

# import module snippets
from ansible.module_utils.basic import *
main()
