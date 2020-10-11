# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
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
    # ansible -i 'barn://127.0.0.1:5000' -m ping
    
    # Barn connection string with username and password
    # ansible -i 'barn://user:password@127.0.0.1:5000' -m ping

    # Barn connection string with token
    # ansible -i 'barn://qsjdfmlkqjsdmflkqjsdmlfkhqsomigamdfjqsdkfjqsdmjf@127.0.0.1:5000' -m ping

    # still supports w/o ranges also
    # ansible-playbook -i 'localhost,' play.yml
'''

import os
import re
import json
from ansible.module_utils.urls import Request
from ansible.module_utils.urls import urllib_error
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):

    NAME = 'barn'
    
    def _load_connection_string(self, connection_string):
        m_pw = re.search(r'^barn://([^:]+):([^@]+)@([^:]+):(\d+)$', connection_string)
        if m_pw:
            self.barn_vars = dict(
                barn_user=m_pw.group(1),
                barn_password=m_pw.group(2),
                barn_host=m_pw.group(3),
                barn_port=m_pw.group(4))
        m_simple = re.search(r'^barn://([^:]+):(\d+)$', connection_string)
        if m_simple:
            self.barn_vars = dict(
                barn_host=m_simple.group(1),
                barn_port=m_simple.group(2))
        m_token = re.search(r'^barn://([^@]+)@([^:]+):(\d+)$', connection_string)
        if m_token:
            self.barn_vars = dict(
                barn_token=m_token.group(1),
                barn_host=m_token.group(2),
                barn_port=m_token.group(3))

    def _load_connection_file(self, path):
        data = None
        try:
            self.barn_vars = self.loader.load_from_file(path, cache=False)
        except Exception as e:
            raise AnsibleParserError(e)
        return data

    def _load_barn_vars(self, path):
        con_string = self._extract_connection_string_from_path(path)
        if con_string:
            self._load_connection_string(con_string)
        elif super(InventoryModule, self).verify_file(path) and path.endswith(('barn.yaml','barn.yml')):
            self._load_connection_file(path)

    def _extract_connection_string_from_path(self, path):
        m_cs = re.search(r'.+barn://?(.+)$', path)
        if m_cs:
            return "barn://" + m_cs.group(1)
        return None

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.barn_vars = None
        self.loader = None

    def verify_file(self, path):
        '''Return true/false if this is a 
        valid file for this plugin to consume
        '''
        valid = False
        if super(InventoryModule, self).verify_file(path) and path.endswith(('barn.yaml','barn.yml')):
            self.display.vv("add Barn inventory")
            valid = True
        elif self._extract_connection_string_from_path(path):
            self.display.vv("add Barn inventory")
            valid = True
        else:
            print("barn inventory not supported")
        return valid

    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory file '''
        self.loader = loader
        if self.barn_vars is None:
            self._load_barn_vars(path)

        

        query_args = dict()
        query_args["headers"] = {'Content-type': 'application/json'}

        if self.barn_vars.get("barn_user", False) and self.barn_vars.get("barn_password", False):
            query_args["url_username"] = self.barn_vars.get("barn_user")
            query_args["url_password"] = self.barn_vars.get("barn_password")
            query_args["force_basic_auth"] = True
        elif self.barn_vars.get("token", False):
            query_args["headers"]["x-access-tokens"] = self.barn_vars.get("token")

        try:
            r = Request().open("GET", "http://%s:%s/inventory" %(
                        self.barn_vars.get("barn_host", "127.0.0.1"),
                        self.barn_vars.get("barn_port", "5000")), **query_args)

        except urllib_error.HTTPError as e:
            try:
                body = json.loads(e.read())
            except AttributeError:
                body = {}
            raise AnsibleParserError(message=body.get("error", ""))

        
        return json.loads(r.read()).get("results", {})

