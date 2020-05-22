import pymongo 
import urllib.parse
import uuid
from ansible.inventory.host import Host

class MemberNotFoundError(Exception):
    """Member not found in InventoryDB"""

class InventoryDB(object):
  from __future__ import (absolute_import, division, print_function)
  __metaclass__ = type

  def host_exist(self,name):
    pass

  def group_exist(self, name):
    pass

  def add_host(self, host):
    pass

  def add_group(self, group):
    pass

  def add_child_group_to_group(self, child_group, parent_group):
    pass

  def add_host_to_group(self, host_name, group_name):
    pass

  def set_variable(self, name, key, value):
    pass

  def get_vars(self,name):
    pass
  

