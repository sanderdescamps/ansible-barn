#!/usr/bin/env python3

class InventoryObject:
  def __init__(self, name):
    self.name = name
    self.vars = {}

  def get_object(self):
    return self.vars
  
class InventoryGroup(InventoryObject):
  def __init__(self, name):
      self.groups = {}

class InventoryHost(InventoryObject):
  def addVar(self, name, value):
    self.vars[name] = value
  
  def get_object(self):
    return { self.name : self.vars }










def main():
  print("is this really a joke or what?")



 
if __name__== "__main__":
  main()
