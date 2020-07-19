#/usr/bin/python3
import re

connection_string = "barn://user:password@127.0.0.1:5000"
m = re.search(r'barn://([^:]+):([^@]+)@([^:]+):(\d+)', connection_string)
print(m)
output = dict(
                user=m.group(1),
                password=m.group(2),
                host=m.group(3),
                port=m.group(4))
print(output)