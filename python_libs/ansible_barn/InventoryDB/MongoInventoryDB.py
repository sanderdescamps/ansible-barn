from ansible_barn.InventoryDB import InventoryDB
from ansible_barn.InventoryDB import MemberNotFoundError
import pymongo 
import urllib.parse
import uuid
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars
import json

def clean_dir(d):
  res = {}
  if type(d)== dict:
    for k,v in d.items():
      if k.startswith('_'):
        pass
      elif type(v) == dict or type(v) == list:
        res[k] = clean_dir(v)
      else:
        res[k]=v
  elif type(d)== list:
    res = list(map(lambda x: clean_dir(x) if type(x)==dict else x, d))    
  return res

class MongoInventoryDB(InventoryDB):
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

  def __export_host(self, name=None):
    if name is None or name.lower() == "all":
      return { "hosts": list(self.mdb["inventory"]["host_inventory"].find({})), "groups": list(self.mdb["inventory"]["group_inventory"].find({}))}
    elif self.host_exist(name):
      return { "hosts": list(self.mdb["inventory"]["host_inventory"].find({ "name": name }))}

  def export(self, name=None):
    if name is None or name.lower() == "all":
      hosts = list(self.mdb["inventory"]["host_inventory"].find())
      hosts = clean_dir(hosts)
      groups = list(self.mdb["inventory"]["group_inventory"].find())
      groups = clean_dir(groups)
      return { "hosts": hosts, "groups": groups}
    elif self.host_exist(name):
      hosts = list(self.mdb["inventory"]["host_inventory"].find({ "name": name }))
      hosts = clean_dir(hosts)
      return { "hosts": hosts}
    elif self.group_exist(name):
      groups = list(self.mdb["inventory"]["group_inventory"].find({ "name": name }))
      groups = clean_dir(groups)
      return { "groups": groups}
