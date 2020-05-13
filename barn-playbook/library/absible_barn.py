#!/usr/bin/python

# Copyright: (c) 2020, Sander Descamps <sander_descamps@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ansible_barn

short_description: Module to add the Ansible facts into the Ansible-barn

version_added: "2.9"

description:
    - "Module to add the Ansible facts into the Ansible-barn"

options:
    name:
        description:
            - This is the message to send to the test module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_test:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the test module generates
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
try:
    import json
except ImportError:
    import simplejson as json



import os
import sys
import argparse
from elasticsearch import Elasticsearch
from datetime import datetime

try:
    import json
except ImportError:
    import simplejson as json
class BarnInventory(object):
    def __init__(self, host, host_port):
        self.es_host = host
        self.es_host_port = host_port
        self.es = Elasticsearch(hosts=[{'host': self.es_host, 'port': self.es_host_port}])

    def sample_init(self):
        self.es.indices.create(index='inventory')
        e1={
            "hostname" :  "srvplex01.myhomecloud.be",
            "hostname_short" :   "srvplex01",
            "ip_address" :         "10.10.6.29",
            "facts" :       {}
        }
        e2={
            "hostname" :  "srvdns01.myhomecloud.be",
            "hostname_short" :   "srvdns01",
            "ip_address" :         "10.10.6.4",
            "facts" :       {}
        }
        e3={
            "hostname" :  "srvdns02.myhomecloud.be",
            "hostname_short" :   "srvdns02",
            "ip_address" :         "10.10.6.5",
            "facts" :       {},
            "creation_date" : datetime.now()
        }
        res=self.es.index(index='inventory',doc_type='host',body=e1)
        print(res)
        res=self.es.index(index='inventory',doc_type='host',id=2,body=e2)
        print(res)
        res=self.es.index(index='inventory',doc_type='host',id=3,body=e3)
        print(res)

    def flush(self):
        self.es.indices.delete(index='inventory')

    def add_host(self):
        return None

    def get_id_host(self, hostname):
        res = self.es.search(index='inventory',body={
            'query':{
                'match_phrase':{
                    'hostname': hostname
                }
            }
        })
        return res['hits']['hits'][0]['_id']

    def get_all_hosts(self):
        return self.es.search(index='inventory',body={
            "query": {
                "match_all": {}
            }
        })
    def get_host_by_id(self, id):
        return self.es.get(index='inventory',doc_type='host',id=id)





def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', require=True),
        data=dict(type='dict', required=True),
        host=dict(type='str', require=True),
        port=dict(type='int', require=False, default=9200),
        state=dict(type='str', required=False, default='present')
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    barn=BarnInventory(module.params['host'], module.params['port'])
    id=barn.get_id_host(module.params['name'])

    if( id is None ):
        barn.
    else:
        res=barn.get_host_by_id(id)
    
    
    
    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = res
    result['message'] = 'goodbye'

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if True:
        result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['host'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

