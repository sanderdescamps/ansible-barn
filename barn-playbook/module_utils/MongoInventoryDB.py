from InventoryDB import InventoryDB
import pymongo 
import urllib.parse
import uuid
from ansible.inventory.host import Host

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

  def sample_init(self):
    self.mdb["inventory"]["host_inventory"].delete_many({})
    self.add_host("srvplex01.myhomecloud.be")
    self.add_host("srvdns01.myhomecloud.be")
    self.add_host("srvdns02.myhomecloud.be")

  def host_exist(self,name):
    if self.mdb["inventory"]["host_inventory"].find({ "name": name }).count() > 0:
      return True
    return False

  def add_host(self, host):
    if type(host) is str: 
      h = Host(host)
      self.mdb["inventory"]["host_inventory"].insert_one(h.serialize())
    elif type(host) is Host:
      self.mdb["inventory"]["host_inventory"].insert_one(host.serialize())

  def update_host(self,host):
    if self.host_exist(host.get_name()):
      myquery = { "name": host.get_name() }
      s_host = host.serialize()
      newvalues = { "$set": { "vars": s_host["vars"], "address": s_host["address"], "uuid": s_host["uuid"], "groups": s_host["groups"], "implicit": s_host["implicit"]  } }
      self.mdb["inventory"]["host_inventory"].update_one(myquery, newvalues)

  def get_host(self, name):
    query = { "name": name }
    data = self.mdb["inventory"]["host_inventory"].find_one(query)
    h = Host()
    h.deserialize(data)
    return h

  def set_variable(self, name, key, value):
    h = self.get_host(name)
    h.set_variable(key,value)
    self.update_host(h)

  def main(self):
    self.sample_init()
    print(self.get_host("srvdns02.myhomecloud.be").serialize())
    self.set_variable("srvdns02.myhomecloud.be","newvar","newvalue")
    cursor = self.mdb["inventory"]["host_inventory"].find({})
    for document in cursor:
      print(document)
     

if __name__ == '__main__':
    inventory_database=MongoInventoryDB('192.168.1.39', 27017, "admin-user", "jfldmdpdeiehjkHGSthjjhDdfghhFdf")
    #inventory_database=MongoInventoryDB('192.168.1.39', 27017, "mongo-user", "mDFKMDFJAMZLFNQMDSLFIHADFANMDFJAlEFjkdfjoqjdf")
    inventory_database.main()

    