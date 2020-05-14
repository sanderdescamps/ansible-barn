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
    e1={
        "hostname" :  "srvplex01.myhomecloud.be",
        "hostname_short" :   "srvplex01",
        "ip_address" :         "10.10.6.29",
        "facts" :       {}
    }
    e2={
        "hostname" :  "srvdns01.myhomecloud.be",
        "hostname_short" :   "srvdns01",
        "ip_address" :         "10.10.6.4",
        "facts" :       {}
    }
    e3={
        "hostname" :  "srvdns02.myhomecloud.be",
        "hostname_short" :   "srvdns02",
        "ip_address" :         "10.10.6.5",
        "facts" :       {},
        "creation_date" : "kdfpd"
    }
    self.addhost(e1)
    self.addhost(e2)
    self.addhost(e3)


  def host_exist(self,hostname):
    if self.mdb["inventory"]["host_inventory"].find({ "hostname": hostname }).count() > 0:
      return True
    return False

  def addhost(self, host):
    if not self.host_exist(host["hostname"]):
      self.mdb["inventory"]["host_inventory"].insert_one(host)

  def get_host(self, hostname):
    query = { "hostname": hostname }
    mydoc = self.mdb["inventory"]["host_inventory"].find_one(query)
    return mydoc
  
  def set_variable(self, hostname, key, value):
    query = { "hostname": hostname }
    newvalue = { "$set": { key: value } }
    self.mdb["inventory"]["host_inventory"].update_one(query, newvalue)

  def main(self):
    self.sample_init()
    self.get_host("srvdns02.myhomecloud.be")
    self.set_variable("srvdns02.myhomecloud.be","newvar","newvalue")
    cursor = self.mdb["inventory"]["host_inventory"].find({})
    for document in cursor:
          print(document)
     

if __name__ == '__main__':
    #inventory_database=MongoInventoryDB('192.168.1.39', 27017, "admin-user", "jfldmdpdeiehjkHGSthjjhDdfghhFdf")
    #inventory_database=MongoInventoryDB('192.168.1.39', 27017, "mongo-user", "mDFKMDFJAMZLFNQMDSLFIHADFANMDFJAlEFjkdfjoqjdf")
    #inventory_database.main()

    h = Host("srvdns02.myhomecloud.be",port=22)
    print(h.serialize())

    