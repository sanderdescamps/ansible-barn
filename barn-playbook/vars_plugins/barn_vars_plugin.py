from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
  vars: barn_vars
  version_added: "2.9"
  short_description: Load variables from central barn server
  requirements:
    - authentication file for barn (barn.cfg)
  description:
    - Loads YAML vars into corresponding groups/hosts in group_vars/ and host_vars/ directories.
    - Files are restricted by extension to one of .yaml, .json, .yml or no extension.
    - Hidden (starting with '.') and backup (ending with '~') files and directories are ignored.
    - Only applies to inventory sources that are existing paths.
    - Starting in 2.10, this plugin requires whitelisting and is whitelisted by default.
  options:
    stage:
    ini:
      - key: stage
      section: vars_host_group_vars
    env:
      - name: ANSIBLE_VARS_PLUGIN_STAGE
    _valid_extensions:
    default: [".yml", ".yaml", ".json"]
    description:
      - "Check all of these extensions when looking for 'variable' files which should be YAML or JSON or vaulted versions of these."
      - 'This affects vars_files, include_vars, inventory and vars plugins among others.'
    env:
      - name: ANSIBLE_YAML_FILENAME_EXT
    ini:
      - section: yaml_valid_extensions
      key: defaults
    type: list
  extends_documentation_fragment:
    - vars_plugin_staging
'''

import os
from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.vars import BaseVarsPlugin
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars
from ansiblebarn.BarnBuilder import barnBuilder
from ansible.utils.display import Display

FOUND = {}
display=Display()

# def load_barn_properties():
#   b_path=os.path.dirname(os.path.abspath(__file__))
#   if b_path.endswith("vars_plugins"):
#     b_path = b_path[:-13]
#   display.v("Using %s as config file for ansible-barn"%("~/.barn.cfg"))
#   barnBuilder.load_config_file("~/.barn.cfg")
#   display.v("Using %s as config file for ansible-barn"%(b_path +"/barn.cfg"))
#   barnBuilder.load_config_file(b_path +"/barn.cfg")
#   display.v("Using %s as config file for ansible-barn"%("/etc/ansible/barn.cfg"))
#   barnBuilder.load_config_file("/etc/ansible/barn.cfg")
#   display.v("Using %s environment variables for ansible-barn")
#   barnBuilder.load_env_vars()

# load_barn_properties()

class VarsModule(BaseVarsPlugin):

  def __init__(self):
    super(VarsModule, self).__init__()
    self.barn = barnBuilder.get_instance()

  def get_vars(self, loader, path, entities, cache=True):
    if not isinstance(entities, list):
      entities = [entities]

    super(VarsModule, self).get_vars(loader, path, entities)

    data = {}
    for entity in entities:
      try:
        v = self.barn.get_vars(entity.name)
        if v is not None: 
          data = combine_vars(data, v)
      except Exception as e:
        raise AnsibleParserError(to_native(e))
    return data



