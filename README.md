Ansible modules to interact with Cloudera Manager
===

[Cloudera Manager](https://www.cloudera.com/content/www/en-us/products/cloudera-manager.html) is an administration GUI for CDH. It also provides an python API to interact with its core. These ansible modules are not intended to replace it, just to ease bootstrap.

Python API may not be always up-to-date so some features may be missing. Futhermore, these modules have been tested only with Cloudera Manager Express.

## Howto
### Installation
Install cm_apy python package on the system running ansible.
```shell
pip install cm_api
```
After cloning this repository, copy library/* to your library directoty. If you don't have one, a `library/` directory in your ansible workspace is sufficient.
### Using modules
Kudos to ansible team, you just need to add  -M <path to library> to enable modules. you can also add a `library` entry to your ansible.cfg. Please refer to [ansible documentation](http://docs.ansible.com/ansible/intro_configuration.html#library).

## Modules
You can find examples in playbooks/tests
### cloudera_manager_config
Configure Cloudera Manager.

### cloudera_manager_user
Add, update or remove Cloudera Manager users.

### clouder_manager_install_host [WIP]
Deploy Cloudera Agent to host
