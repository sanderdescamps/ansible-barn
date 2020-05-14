from ansible_barn.InventoryDB.MongoInventoryDB import MongoInventoryDB

class BarnInventory(object):
  def __init__(self,  inventory_db :MongoInventoryDB ):
    self.inv_db =  inventory_db

  def lookup_hosts(self,name): 
    if self.inv_db.host_exist("name"):
      return [self.inv_db.get_host(name)]
    else
      self.inv_db.
    
    return None

