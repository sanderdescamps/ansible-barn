# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils.urls import urllib_error
from ansible.module_utils.urls import Request
from ansible.errors import AnsibleParserError
import json
import re
import os
__metaclass__ = type

DOCUMENTATION = '''
    inventory: barn
    version_added: "2.9"
    short_description: Get hostlist from barn
    description:
        - Connects to Barn server and fetches all hosts.
        - This plugin only applies barn connection strings or to playbooks with a barn.cfg in the root directory.
'''

EXAMPLES = '''
    # Barn connection string (Guest user)
    # ansible all -i barn.yml -m ping
    
    # barn.yml
        ---
        plugin: barn
        barn_user: sdescamps
        barn_password: superstrongpassword
        barn_hostname: 127.0.0.1
        barn_port: 5000
        fetch_variables: false
'''

class InventoryModule(BaseInventoryPlugin):

    NAME = 'barn'

    def _load_connection_file(self, path, loader):
        try:
            self.barn_vars.update(loader.load_from_file(path, cache=False))
        except Exception as e:
            raise AnsibleParserError(e)

    def _validate_connection_file(self, path):
        '''Verifies if "plugin: barn" is in the file.
        '''
        conn_file = open(path, 'r')
        conn_text = conn_file.read()
        conn_file.close()
        matches = re.findall("plugin: +barn", conn_text)
        return len(matches) > 0

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.barn_vars = dict(
            barn_user="admin",
            barn_password="admin",
            barn_hostname="127.0.0.1",
            barn_port="5000",
            fetch_variables=False
        )


    def verify_file(self, path):
        '''Checks if the barn config file is a valid config file.
        '''
        valid = False
        if path.lower().endswith("@barn"):
            self.display.vv("Using Barn as inventory source")
            valid = True
        elif super(InventoryModule, self).verify_file(path) and self._validate_connection_file(path):
            self.display.vv("Using Barn as inventory source")
            valid = True
        else: 
            self.display.vv("Unable to parse Barn Inventory")
        return valid


    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory file '''

        
        if os.path.exists(os.path.join(os.environ['HOME'],".barn.yml")): 
            self._load_connection_file(os.path.join(os.environ['HOME'],".barn.yml"), loader)
        elif os.path.exists(os.path.join(os.environ['HOME'],".barn.yaml")): 
            self._load_connection_file(os.path.join(os.environ['HOME'],".barn.yaml"), loader)
        if os.path.exists("/etc/barn/barn.yml"):
            self._load_connection_file("/etc/barn/barn.yml", loader)
        elif os.path.exists("/etc/barn/barn.yaml"):
            self._load_connection_file("/etc/barn/barn.yaml", loader)
        
        if not path.endswith("@barn"):
            self._load_connection_file(path, loader)

        query_args = dict()
        query_args["headers"] = {'Content-type': 'application/json'}

        if self.barn_vars.get("barn_user", False) and self.barn_vars.get("barn_password", False):
            query_args["url_username"] = self.barn_vars.get("barn_user")
            query_args["url_password"] = self.barn_vars.get("barn_password")
            query_args["force_basic_auth"] = True
        elif self.barn_vars.get("token", False):
            query_args["headers"]["x-access-tokens"] = self.barn_vars.get(
                "token")

        hosts = []
        groups = []
        try:
            self.display.vvv("Connect to http://%s:%s/hosts" % (self.barn_vars.get("barn_hostname"),self.barn_vars.get("barn_port")))
            r = Request().open("GET", "http://%s:%s/hosts" % (
                self.barn_vars.get("barn_hostname"),
                self.barn_vars.get("barn_port")), **query_args)
            hosts = json.loads(r.read()).get("result")
            self.display.vvv(json.dumps(hosts))
            self.display.vvv("Connect to http://%s:%s/groups" % (self.barn_vars.get("barn_hostname"),self.barn_vars.get("barn_port")))
            r = Request().open("GET", "http://%s:%s/groups" % (
                self.barn_vars.get("barn_hostname"),
                self.barn_vars.get("barn_port")), **query_args)
            groups = json.loads(r.read()).get("result")
            self.display.vvv(json.dumps(groups))
        except urllib_error.HTTPError as e:
            try:
                body = json.loads(e.read())
            except AttributeError:
                body = {}
            raise AnsibleParserError(message=body.get("error", ""))

        for h in hosts:
            inventory.add_host(h.get("name"))
            if self.barn_vars.get("fetch_variables", False):
                for k, v in h.get("vars", {}).items():
                    inventory.set_variable(h.get("name"), k, v)
        for g in groups:
            inventory.add_group(g.get("name"))
            if self.barn_vars.get("fetch_variables", False):
                for k, v in g.get("vars", {}).items():
                    inventory.set_variable(g.get("name"), k, v)
            for h in g.get("hosts", []):
                inventory.add_child(g.get("name"), h)
        # Add child groups
        for g in groups:
            for cg in g.get("child_groups", []):
                if cg in inventory.groups:
                    inventory.add_child(g.get("name"), cg)
