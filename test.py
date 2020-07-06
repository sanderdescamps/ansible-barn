from ansible.inventory.group import Group
from ansible.inventory.host import Host

h1 = Host("srvdns01.myhomecloud.be")
h2 = Host("srvdns02.myhomecloud.be")

g1 = Group(name="testgroup")
g1.add_host(h1)
g1.add_host(h2)

print(g1.serialize())
