from ansible_barn.InventoryDB.MongoInventoryDB import MongoInventoryDB

if __name__ == '__main__':
    inventory_database=MongoInventoryDB('192.168.1.39', 27017, "admin-user", "jfldmdpdeiehjkHGSthjjhDdfghhFdf")
    #inventory_database=MongoInventoryDB('192.168.1.39', 27017, "mongo-user", "mDFKMDFJAMZLFNQMDSLFIHADFANMDFJAlEFjkdfjoqjdf")

    inventory_database._flush()
    inventory_database.add_host("srvplex01.myhomecloud.be")
    inventory_database.add_host("srvdns01.myhomecloud.be")
    inventory_database.add_host("srvdns02.myhomecloud.be")

    inventory_database.set_variable("srvdns01.myhomecloud.be","env_environment", "development")
    inventory_database.set_variable("srvdns01.myhomecloud.be","env_environment", "test")
    inventory_database.add_group("dns_servers")
    inventory_database.set_variable("dns_servers","description", "Dit zijn de DNS servers")
    inventory_database.add_host_to_group("srvdns01.myhomecloud.be","dns_servers")
    inventory_database.add_host_to_group("srvdns02.myhomecloud.be","dns_servers")
    inventory_database.add_group("all_servers")
    inventory_database.add_child_group_to_group("dns_servers","all_servers")
    
    inventory_database._print_all()
    print("vars of srvdns01: ", inventory_database.get_vars("srvdns01.myhomecloud.be"))
    print("vars of dns_servers group: ", inventory_database.get_vars("dns_servers"))