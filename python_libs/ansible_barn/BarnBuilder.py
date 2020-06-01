from ansible_barn.InventoryDB.MongoInventoryDB import MongoInventoryDB
from ansible_barn.InventoryDB.ElasticInventoryDB import ElasticInventoryDB
from ansible_barn.InventoryDB import BarnTypeNotSupported
from ansible_barn.BarnConfigManager import BarnConfigManager, find_barn_config_file
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
    self.barn = None
    self.config_manager = BarnConfigManager()
    cfg_path=find_barn_config_file()
    self.config_manager.load_config_file(cfg_path)
  
  def reconnect(self):
    raise NotImplementedError

  def get_instance(self):
    if self.config_manager.get_config_value("barn_inventory_type") == "mongodb":
      return MongoInventoryDB(self.config_manager.get_config_value("barn_hostname"),
          port=self.config_manager.get_config_value("barn_port"),
          username=self.config_manager.get_config_value("barn_user"),
          password=self.config_manager.get_config_value("barn_password"))
    elif self.config_manager.get_config_value("barn_inventory_type") == "elastic":
      return MongoInventoryDB(self.config_manager.get_config_value("barn_hostname"),
          port=self.config_manager.get_config_value("barn_port"),
          username=self.config_manager.get_config_value("barn_user"),
          password=self.config_manager.get_config_value("barn_password"))
    else:
      raise BarnTypeNotSupported


barnBuilder = BarnBuilder()
    