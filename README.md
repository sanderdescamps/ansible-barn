# ansible-barn
A storage place for information used by Ansible playbooks


# API

## GET /nodes/
**description:** Get all host or group 

**properties:**
- *type*: type of the node {host, group}
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
    
## POST /nodes/
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


