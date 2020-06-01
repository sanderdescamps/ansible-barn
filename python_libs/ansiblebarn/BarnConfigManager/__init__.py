import configparser
import os
from ansible.utils.path import unfrackpath
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.errors import AnsibleError

def find_barn_config_file():
  potential_paths = []

  cwd = os.getcwd()
  print(cwd)
  cwd_cfg = os.path.join(cwd, "barn.cfg")
  potential_paths.append(cwd_cfg)

  potential_paths.append(unfrackpath("~/.barn.cfg", follow=False))

  potential_paths.append("/etc/ansible/barn.cfg")

  for path in potential_paths:
      b_path = to_bytes(path)
      if os.path.exists(b_path) and os.access(b_path, os.R_OK):
          return path
  else:
      return None

class UndefinedBarnSettingError(AnsibleError):
  def __init__(self,message):
    super(UndefinedBarnSettingError, self).__init__(message)

class BarnConfigManager(object):

  def __init__(self):
    self.settings = {}

  def _read_config_yaml_file(self,path):
    raise NotImplementedError

  def _read_config_ini_file(self,path):
    """
      Load ini config file
    """
    if os.path.isfile(path):
      config = configparser.ConfigParser()
      config.read(path)
      for k,v in config.items('defaults'):
          self.settings[k] = v
      self._parse_config()

  def _parse_config(self):
    """
      Iterate over all settings and correct potential mistakes
    """
    for k,v in self.settings.items():
      if k == "barn_inventory_type":
        self.settings[k] = v.lower()
      

  def load_config_file(self, path):
    if path.endswith('.yml') or path.endswith('.yaml'):
      self._read_config_yaml_file(path)
    elif path.endswith('.ini') or path.endswith('.cfg'):
      self._read_config_ini_file(path)
  
  def load_config_files(self,paths):
    """
      Load multiple config files, input path-list from low to high priority
    """
    for p in paths:
      self.load_config_file(p)

  def load_env_vars(self):
    """
      Load properties stored in the environment variables
    """
    for k,v in os.environ.items():
      if k.lower().startswith('barn'):
        self.settings[k.lower()] = v

  def load_extra_vars(self,vars):
    for k,v in vars.items():
      if v is not None:
        self.settings[k]=v

  def get_config_value(self,name):
    if name in self.settings:
      return self.settings[name]
    elif name == "barn_inventory_type":
      return "mongodb"
    elif name == "barn_port" and self.get_config_value("barn_inventory_type") == "mongodb":
      return "27017"
    elif name == "barn_port" and self.get_config_value("barn_inventory_type") == "elastic":
      return "9200"
    else:
      return None

