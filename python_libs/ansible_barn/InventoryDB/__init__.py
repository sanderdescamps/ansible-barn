import pymongo 
import urllib.parse
import uuid
from ansible.inventory.host import Host

class InventoryDB(object):
  def get_id_host(self, hostname):
    return None

