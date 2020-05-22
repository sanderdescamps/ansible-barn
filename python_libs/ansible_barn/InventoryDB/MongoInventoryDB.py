from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_barn.InventoryDB import InventoryDB
from ansible_barn.InventoryDB import MemberNotFoundError
import pymongo 
import urllib.parse
import uuid
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars
import json



class MongoInventoryDB(object):
  def __init__(self, hostname, port=27017, username=None, password=None):
    self.hostname = hostname
    self.port = port
    self.username = username
    self.password = password
    if username is not None and password is not None:
      self.mdb = pymongo.MongoClient("mongodb://%s:%s@%s:%s/" % (urllib.parse.quote_plus(self.username), urllib.parse.quote_plus(self.password), self.hostname, str(self.port)))
    else:
      self.mdb = pymongo.MongoClient("mongodb://%s:%s/" % (self.hostname, str(self.port)))
    self.mdb["inventory"]["host_inventory"]
    self.mdb["inventory"]["group_inventory"]

  def host_exist(self,name):
    if self.mdb["inventory"]["host_inventory"].count_documents({ "name": name }) > 0:
      return True
    return False

  def group_exist(self, name):
    if self.mdb["inventory"]["group_inventory"].count_documents({ "name": name }) > 0:
      return True
    return False

  def add_host(self, host):
    if type(host) is str: 
      h = Host(host)
      self.mdb["inventory"]["host_inventory"].insert_one(h.serialize())

  def add_group(self, group):
    if type(group) is str: 
      g = Group(group)
      self.mdb["inventory"]["group_inventory"].insert_one(g.serialize())

  def add_child_group_to_group(self, child_group, parent_group):
    self.mdb["inventory"]["group_inventory"].update_one({ "name": child_group },{ "$addToSet": { "parent_groups": parent_group } })
    self.mdb["inventory"]["group_inventory"].update_one({ "name": parent_group },{ "$addToSet": { "child_groups": child_group } })

  def add_host_to_group(self, host_name, group_name):
    if self.host_exist(host_name): 
      self.mdb["inventory"]["group_inventory"].update_one({ "name": group_name },{ "$addToSet": { "hosts": host_name } })
      self.mdb["inventory"]["host_inventory"].update_one({ "name": host_name },{ "$addToSet": { "groups": group_name } })
    else: 
      raise MemberNotFoundError



  # def update_host(self,host):
  #   if self.host_exist(host.get_name()):
  #     myquery = { "name": host.get_name() }
  #     s_host = host.serialize()
  #     newvalues = { "$set": { "vars": s_host["vars"], "address": s_host["address"], "uuid": s_host["uuid"], "groups": list(map(lambda y: y.get_name(), host.get_groups())), "implicit": s_host["implicit"]  } }
  #     self.mdb["inventory"]["host_inventory"].update_one(myquery, newvalues)

  # def update_group(self, group):
  #   if self.group_exist(group.get_name()):
  #     myquery = { "name": group.get_name() }
  #     s_group = group.serialize()
  #     newvalues = { "$set": { "vars": s_group["vars"], "parent_groups": s_group["parent_groups"], "depth": s_group["depth"], "hosts": s_group["hosts"]  } }
  #     self.mdb["inventory"]["group_inventory"].update_one(myquery, newvalues) 

  # def get_group(self, name):
  #   query = { "name": name }
  #   data = self.mdb["inventory"]["group_inventory"].find_one(query)
  #   data["hosts"] = list(map(lambda x: self.get_host(x), data["hosts"]))
  #   data["parent_groups"] = list(map(lambda x: self.get_group(x).serialize(), data["parent_groups"]))
  #   #data["parent_groups"] = list(map(self.get_group, data["hosts"]))
  #   g = Group()
  #   g.deserialize(data)
  #   return g

  # def get_host(self, name):
  #   query = { "name": name }
  #   data = self.mdb["inventory"]["host_inventory"].find_one(query)
  #   h = Host()
  #   h.deserialize(data)
  #   return h

  def set_variable(self, name, key, value):
    if self.host_exist(name):
      self.mdb["inventory"]["host_inventory"].update_one({"name": name}, {"$set": {"vars": {key: value}}})
    elif self.group_exist(name):
      self.mdb["inventory"]["group_inventory"].update_one({"name": name}, {"$set": {"vars": {key: value}}})

  def get_vars(self,name):
    if self.host_exist(name):
      res={}
      host = self.mdb["inventory"]["host_inventory"].find_one({ "name": name })
      if "vars" in host and host["vars"] is not None and len(host["vars"]) > 0:
          res = combine_vars(res,host["vars"])
      
      to_process_groups = host["groups"]
      while len(to_process_groups)>0:
        g_name = to_process_groups.pop()
        g = self.mdb["inventory"]["group_inventory"].find_one({ "name": g_name })
        if "vars" in g and g["vars"] is not None and len(g["vars"]) > 0:
          res = combine_vars(res,g["vars"])
        if "parent_groups" in g and g["parent_groups"] is not None and len(g["parent_groups"]) > 0:
          to_process_groups.extend(g["parent_groups"])
    
    elif self.group_exist(name):
      res={}
      to_process_groups = [name]
      while len(to_process_groups)>0:
        g_name = to_process_groups.pop()
        g = self.mdb["inventory"]["group_inventory"].find_one({ "name": g_name })
        if "vars" in g and g["vars"] is not None and len(g["vars"]) > 0:
          res = combine_vars(res,g["vars"])
        if "parent_groups" in g and g["parent_groups"] is not None and len(g["parent_groups"]) > 0:
          to_process_groups.extend(g["parent_groups"])
    return res

  def _flush(self):
    self.mdb["inventory"]["host_inventory"].delete_many({})
    self.mdb["inventory"]["group_inventory"].delete_many({})

  def _print_all(self):
    print("##### HOSTS ######")
    cursor = self.mdb["inventory"]["host_inventory"].find({})
    for document in cursor:
      del document["_id"]
      print(json.dumps(document, sort_keys=True, indent=2))
    print("##### GROUPS ######")
    cursor = self.mdb["inventory"]["group_inventory"].find({})
    for document in cursor:
      del document["_id"]
      print(json.dumps(document, sort_keys=True, indent=2))
   