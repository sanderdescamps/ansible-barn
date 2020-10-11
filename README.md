# ansible-barn
Ansible-barn or barn in short is a central variable server for Ansible. It provides a central location to store variables. Via Ansible modules you can easily get and set variables. Via an API ansible will store the variables in a MongoDB database. At the moment Ansible-barn is still under construction. 

# API

## Methodes

### GET hosts/groups/nodes
**description:** Get one or all hosts or groups

**properties:**
- *type*: type of the node {host, group}. Only usefull when querying nodes. 
- *name*: Name of the host of Group

**return:**

    {
      "results": [
        {
          "_cls": "Node.Host",
          "_id": {
            "$oid": "5eff0236c8eeb1ae91a5cbc8"
          },
          "groups": [],
          "name": "srvdns01.myhomecloud.be",
          "vars": {}
        }
      ]
    }
    
### POST /nodes/
**description:** Add new host or group

**properties:**
- **name**: name of the host/group
- **type**: type of the node {host, group}
- **groups**: groups a host belongs to (when type==host)
- **child_groups**: child groups of a group (comma seperated list)
- **parent_groups**: parent groups a group belongs to (comma seperated list)



##Result

    {
        "error": "this is the error message"
        "warning": "this is the warning message. With a warning there is still a result"
        "info": "This is the info message"
        "status"; "Status code of the http request"
    }


# Inventory
## Generate Ansible inventory file

Write the full inventory to a json-file. The json-file can directly be read by Ansible. No authentication required. 

    curl -s http://127.0.0.1:5000/inventory_file > test_inventory.json


## Install barn inventory 

    mkdir -p ~/.ansible/plugins/inventory/
    ln -s ~/git/ansible-barn/barn-playbook/inventory_plugins/barn.py ~/.ansible/plugins/inventory/barn.py