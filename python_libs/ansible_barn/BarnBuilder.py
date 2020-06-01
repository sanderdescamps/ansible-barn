from ansible_barn.InventoryDB.MongoInventoryDB import MongoInventoryDB
from ansible_barn.InventoryDB.ElasticInventoryDB import ElasticInventoryDB
from ansible_barn.InventoryDB import BarnTypeNotSupported
from ansible_barn.BarnConfigManager import BarnConfigManager, find_barn_config_file
import configparser
import os

class BarnBuilder(object):
  def __init__(self):
    self.barn = None
    self.config_manager = BarnConfigManager()

    #Find and read the barn config file
    cfg_path = find_barn_config_file()
    if cfg_path:
      self.config_manager.load_config_file(cfg_path)
    
    #Read enviroment variables
    self.config_manager.load_env_vars()
  
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
    