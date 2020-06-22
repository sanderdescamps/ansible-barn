from ansiblebarn.BarnBuilder import barnBuilder

if __name__ == '__main__':
    # barnBuilder.load_extra_vars(
    #   { "barn_user": "admin-user",
    #     "barn_password": "jfldmdpdeiehjkHGSthjjhDdfghhFdf",
    #     "barn_hostname": "192.168.56.3",
    #     "barn_port": 27017,
    #     "barn_inventory_type": "mongodb",})
    barn = barnBuilder.get_instance()
    barn._flush()
    barn.add_host("srvplex01.myhomecloud.be")
    barn.add_host("srvdns01.myhomecloud.be")
    barn.add_host("srvdns02.myhomecloud.be")

    barn.set_variable("srvdns01.myhomecloud.be","env_environment", "development")
    barn.set_variable("srvdns01.myhomecloud.be","env_environment", "test")
    barn.add_group("dns_servers")
    barn.set_variable("dns_servers","description", "Dit zijn de DNS servers")
    barn.add_host_to_group("srvdns01.myhomecloud.be","dns_servers")
    barn.add_host_to_group("srvdns02.myhomecloud.be","dns_servers")
    barn.add_group("all_servers")
    barn.add_child_group_to_group("dns_servers","all_servers")
    
    barn._print_all()
    print("vars of srvdns01: ", barn.get_vars("srvdns01.myhomecloud.be"))
    print("vars of dns_servers group: ", barn.get_vars("dns_servers"))