def remove_underscore_keys(d):
  """
    Recursivly remove underscore keys from directory or list of directories
  """
  res = {}
  if type(d)== dict:
    for k,v in d.items():
      if k.startswith('_'):
        pass
      elif type(v) == dict or type(v) == list:
        res[k] = remove_underscore_keys(v)
      else:
        res[k]=v
  elif type(d)== list:
    res = list(map(lambda x: remove_underscore_keys(x) if type(x)==dict else x, d))    
  return res