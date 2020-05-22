import os
import sys
import argparse
from elasticsearch import Elasticsearch
from datetime import datetime
from ansible_barn.InventoryDB import InventoryDB


try:
    import json
except ImportError:
    import simplejson as json


class ElasticInventoryDB(InventoryDB):
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

    def get_all_hosts(self):
        return self.es.search(index='inventory',body={
            "query": {
                "match_all": {}
            }
        })
    def get_host_by_id(self, id):
        return self.es.get(index='inventory',doc_type='host',id=id)

if __name__ == '__main__':
    barn=ElasticInventoryDB('192.168.1.39', 9200)
    # barn.flush()
    # barn.sample_init()
    # print(json.dumps(barn.get_id_host('srvdns02.myhomecloud.be'), indent=2))
    # print(json.dumps(barn.get_all_hosts(), indent=2))
    # print(json.dumps(barn.get_host_by_id(2), indent=2))

