#!/usr/bin/env python

'''
Example custom dynamic inventory script for Ansible, in Python.
'''

import os
import sys
import argparse
from elasticsearch import Elasticsearch
from datetime import datetime

try:
    import json
except ImportError:
    import simplejson as json

es = Elasticsearch(hosts=[{'host': '192.168.1.39', 'port': 9200}])

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
        res=es.index(index='inventory',doc_type='host',body=e1)
        print(res)
        res=es.index(index='inventory',doc_type='host',id=2,body=e2)
        print(res)
        res=es.index(index='inventory',doc_type='host',id=3,body=e3)
        print(res)

    def flush(self):
        self.es.indices.delete(index='inventory')

    def add_host(self):
        return None

    def get_id_host(self, hostname):
        res = es.search(index='inventory',body={
            'query':{
                'match_phrase':{
                    'hostname': hostname
                }
            }
        })
        return res['hits']['hits'][0]['_id']

    def get_all_hosts(self):
        return es.search(index='inventory',body={
            "query": {
                "match_all": {}
            }
        })
    def get_host_by_id(self, id):
        return es.get(index='inventory',doc_type='host',id=id)



class ExampleInventory(object):

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()

        # Called with `--list`.
        if self.args.list:
            self.inventory = self.example_inventory()
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.empty_inventory()
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.empty_inventory()
        print(json.dumps(self.inventory))

    # Example inventory for testing.
    def example_inventory(self):
        return {
            'group': {
                'hosts': ['192.168.28.71', '192.168.28.72'],
                'vars': {
                    'ansible_ssh_user': 'vagrant',
                    'ansible_ssh_private_key_file':
                        '~/.vagrant.d/insecure_private_key',
                    'example_variable': 'value'
                }
            },
            '_meta': {
                'hostvars': {
                    '192.168.28.71': {
                        'host_specific_var': 'foo'
                    },
                    '192.168.28.72': {
                        'host_specific_var': 'bar'
                    }
                }
            }
        }

    def get_all_hosts(self):
        res = es.search(index="hosts", body={"query": {"match_all": {}}})
        


    def get_host(self, host): 
        return {'_meta': {'hostvars': {}}}

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()

# Get the inventory.
#ExampleInventory()
barn=BarnInventory('192.168.1.39', 9200)
# barn.flush()
# barn.sample_init()
print(json.dumps(barn.get_id_host('srvdns02.myhomecloud.be'), indent=2))
# print(json.dumps(barn.get_all_hosts(), indent=2))
# print(json.dumps(barn.get_host_by_id(2), indent=2))