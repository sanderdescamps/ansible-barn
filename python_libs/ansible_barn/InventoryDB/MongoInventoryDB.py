from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_barn.InventoryDB import InventoryDB
import pymongo 
import urllib.parse
import uuid
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars



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
    if self.mdb["inventory"]["host_inventory"].find({ "name": name }).count() > 0:
      return True
    return False

  def group_exist(self, name):
    if self.mdb["inventory"]["group_inventory"].find({ "name": name }).count() > 0:
      return True
    return False

  def add_host(self, host):
    if type(host) is str: 
      h = Host(host)
      self.mdb["inventory"]["host_inventory"].insert_one(h.serialize())
    elif type(host) is Host:
      self.mdb["inventory"]["host_inventory"].insert_one(host.serialize())

  def add_group(self, group):
    if type(group) is str: 
      g = Group(group)
      self.mdb["inventory"]["group_inventory"].insert_one(g.serialize())
    elif isinstance (group, Group):
      s_group = group.serialize()
      # s_group["hosts"] = list(map(str, s_group["hosts"]))
      s_group["hosts"] = list(map(lambda x: x.get_name(), s_group["hosts"]))
      s_group["parent_groups"] = list(map(lambda y: y["name"], s_group["parent_groups"]))
      self.mdb["inventory"]["group_inventory"].insert_one(s_group)

  def update_host(self,host):
    if self.host_exist(host.get_name()):
      myquery = { "name": host.get_name() }
      s_host = host.serialize()
      newvalues = { "$set": { "vars": s_host["vars"], "address": s_host["address"], "uuid": s_host["uuid"], "groups": s_host["groups"], "implicit": s_host["implicit"]  } }
      self.mdb["inventory"]["host_inventory"].update_one(myquery, newvalues)

  def update_group(self, group):
    if self.group_exist(group.get_name()):
      myquery = { "name": group.get_name() }
      s_group = group.serialize()
      newvalues = { "$set": { "vars": s_group["vars"], "parent_groups": s_group["parent_groups"], "depth": s_group["depth"], "hosts": s_group["hosts"]  } }
      self.mdb["inventory"]["group_inventory"].update_one(myquery, newvalues) 

  def get_group(self, name):
    query = { "name": name }
    data = self.mdb["inventory"]["group_inventory"].find_one(query)
    data["hosts"] = list(map(lambda x: self.get_host(x), data["hosts"]))
    data["parent_groups"] = list(map(lambda x: self.get_group(x).serialize(), data["parent_groups"]))
    #data["parent_groups"] = list(map(self.get_group, data["hosts"]))
    g = Group()
    g.deserialize(data)
    return g

  def get_host(self, name):
    query = { "name": name }
    data = self.mdb["inventory"]["host_inventory"].find_one(query)
    h = Host()
    h.deserialize(data)
    return h

  def set_variable(self, name, key, value):
    if self.host_exist(name):
      h = self.get_host(name)
      h.set_variable(key,value)
      self.update_host(h)
    elif self.group_exist(name):
      g = self.get_group(name)
      g.set_variable(key,value)
      self.update_group(g)
  


  def _flush(self):
    self.mdb["inventory"]["host_inventory"].delete_many({})
    self.mdb["inventory"]["group_inventory"].delete_many({})

  def _print_all(self):
    cursor = self.mdb["inventory"]["host_inventory"].find({})
    for document in cursor:
      print(document)
    cursor = self.mdb["inventory"]["group_inventory"].find({})
    for document in cursor:
      print(document)


if __name__ == '__main__':
    inventory_database=MongoInventoryDB('192.168.1.39', 27017, "admin-user", "jfldmdpdeiehjkHGSthjjhDdfghhFdf")
    #inventory_database=MongoInventoryDB('192.168.1.39', 27017, "mongo-user", "mDFKMDFJAMZLFNQMDSLFIHADFANMDFJAlEFjkdfjoqjdf")

    inventory_database._flush()
    inventory_database.add_host("srvplex01.myhomecloud.be")
    inventory_database.add_host("srvdns01.myhomecloud.be")
    inventory_database.add_host("srvdns02.myhomecloud.be")
    


    h1 = inventory_database.get_host("srvdns01.myhomecloud.be")
    h2 = Host("srvdns02.myhomecloud.be")

    h1.set_variable("env_environment", "development")
    inventory_database.update_host(h1)
    g1 = Group(name="dns_servers")
    g2 = Group(name="all_servers")
    g1.add_host(h1)
    g1.add_host(h2)
    g2.add_child_group(g1)
    inventory_database.add_group(g1)
    inventory_database.add_group(g2)
    print(inventory_database.get_host("srvdns01.myhomecloud.be").get_vars())



    