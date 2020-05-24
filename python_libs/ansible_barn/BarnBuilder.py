from ansible_barn.InventoryDB.MongoInventoryDB import MongoInventoryDB
from ansible_barn.InventoryDB.ElasticInventoryDB import ElasticInventoryDB
from ansible_barn.InventoryDB import BarnTypeNotSupported
import configparser
import os

# def __read_cfg_files():
#     res = {}
#     for p in BARN_CONFIG_PATH:
#         if os.path.isfile(p):
#             config = configparser.ConfigParser()
#             config.read(p)
#             for k,v in config.items('defaults'):
#                 res[k] = v
#     return res

# def __read_env_vars():
#     res = {}
#     if "BARN_USER" in os.environ:
#         res["barn_user"] = os.environ["BARN_USER"]
#     if "BARN_PASSWORD" in os.environ:
#         res["barn_password"] = os.environ["BARN_PASSWORD"]
#     if "BARN_HOSTNAME" in os.environ:
#         res["barn_hostname"] = os.environ["BARN_HOSTNAME"]
#     return res

# def __load_properties(additional_properties=None):
#     prop_files=__read_cfg_files()
#     prop_env=__read_env_vars()
#     prop_custom=additional_properties
#     res = prop_files
#     res.update(prop_env)
#     res.update(prop_custom)
#     return res

# def connect(prop):
#     global __barn
#     if "barn_inventory_type" not in prop or prop["barn_inventory_type"].lower() == "mongodb": 
#       __barn=MongoInventoryDB(prop["barn_hostname"],port=prop["barn_port"],username=prop["barn_user"],password=prop["barn_password"])
#     elif prop["barn_inventory_type"].lower() == "elastic":
#       __barn=ElasticInventoryDB(prop["barn_hostname"],port=prop["barn_port"],username=prop["barn_user"],password=prop["barn_password"])
#     else:
#       raise BarnTypeNotSupported

# def get_barn():
#   global __barn
#   if __barn is None:
#     prop = __load_properties()
#     connect(prop)
#   return __barn

class BarnBuilder(object):
  def __init__(self):
    self.properties = {}
    self.barn = None
  
  def load_config_file(self, path):
    """
      Load ini config file
    """
    if os.path.isfile(path):
      config = configparser.ConfigParser()
      config.read(path)
      for k,v in config.items('defaults'):
          self.properties[k] = v
  
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
    if "BARN_USER" in os.environ:
      self.properties["barn_user"] = os.environ["BARN_USER"]
    if "BARN_PASSWORD" in os.environ:
      self.properties["barn_password"] = os.environ["BARN_PASSWORD"]
    if "BARN_HOSTNAME" in os.environ:
      self.properties["barn_hostname"] = os.environ["BARN_HOSTNAME"]
    if "BARN_PORT" in os.environ:
      self.properties["barn_port"] = os.environ["BARN_PORT"]
    if "BARN_INVENTORY_TYPE" in os.environ:
      self.properties["barn_inventory_type"] = os.environ["BARN_INVENTORY_TYPE"]

  def connect(self):
    if "barn_inventory_type" not in self.properties or self.properties["barn_inventory_type"].lower() == "mongodb": 
      self.barn=MongoInventoryDB(self.properties["barn_hostname"],port=self.properties["barn_port"],username=self.properties["barn_user"],password=self.properties["barn_password"])
    elif self.properties["barn_inventory_type"].lower() == "elastic":
      self.barn=ElasticInventoryDB(self.properties["barn_hostname"],port=self.properties["barn_port"],username=self.properties["barn_user"],password=self.properties["barn_password"])
    else:
      raise BarnTypeNotSupported

  def get_instance(self):
    if self.barn is None:
      self.connect()
    return self.barn

barnBuilder = BarnBuilder()
    