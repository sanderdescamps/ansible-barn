# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from ansible.utils.vars import merge_hash
from ansible.config.manager import ensure_type
from ansible.errors import AnsibleParserError
from ansible.module_utils.urls import Request
from ansible.module_utils.urls import urllib_error
from ansible.plugins.inventory import BaseInventoryPlugin
import os
import re
import json
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

BARN_CONFIG_PATHS = [
    [
        os.path.join(os.getcwd(), "barn.yml"),
        os.path.join(os.getcwd(), "barn.yaml"),
        os.path.join(os.getcwd(), "barn.json")
    ], [
        os.path.join(os.path.expanduser("~"), ".barn.yml"),
        os.path.join(os.path.expanduser("~"), ".barn.yaml"),
        os.path.join(os.path.expanduser("~"), ".barn.json")
    ], [
        os.path.join("/etc/barn/", "barn.yml"),
        os.path.join("/etc/barn/", "barn.yaml"),
        os.path.join("/etc/barn/", "barn.json")
    ]
]

DEFAULT_BARN_VARS = dict(
    barn_user="admin",
    barn_password="admin",
    barn_hostname="127.0.0.1",
    barn_port="5000",
    fetch_variables=False
)


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
        barn_vars = {}
        if path.endswith("@barn"):
            for path_set in BARN_CONFIG_PATHS:
                for path in path_set:
                    if os.path.exists(path):
                        try:
                            barn_vars = merge_hash(loader.load_from_file(
                                path, cache=False), barn_vars)
                        except Exception as e:
                            raise AnsibleParserError(e)
                        break
        else:
            barn_vars = loader.load_from_file(path, cache=False)

        barn_url = barn_vars.get("barn_url")
        barn_host = barn_vars.get(
            "barn_host", barn_vars.get("barn_hostname", None))
        barn_port = barn_vars.get("barn_port", 443)
        barn_https = ensure_type(barn_vars.get("barn_https", True), 'bool')
        validate_certs = barn_vars.get("validate_certs", True)
        barn_user = barn_vars.get("barn_user", None)
        barn_password = barn_vars.get("barn_password", None)
        token = barn_vars.get("barn_token", None)

        if not barn_url and barn_host and barn_port:
            protocol = "https" if barn_https else "http"
            barn_url = "{}://{}:{}".format(protocol, barn_host, barn_port)
            self.display.warning(
                "The options barn_host and barn_port are deprecated. Please use barn_url instead.")
        elif barn_url and not barn_url.startswith("https://") and not barn_url.startswith("http://"):
            protocol = "http" if "barn_https" in barn_vars and not barn_https else "https"
            barn_url = "{}://{}".format(protocol, barn_url)
        barn_url = barn_url.rstrip("/")

        if not barn_url:
            return

        query_args = dict(
            follow_redirects=True,
            validate_certs=validate_certs
        )
        query_args["headers"] = {'Content-type': 'application/json'}
        if token:
            query_args["headers"]["x-access-tokens"] = token
        if barn_user:
            query_args["url_username"] = barn_user
            query_args["force_basic_auth"] = True
        if barn_password:
            query_args["url_password"] = barn_password
            query_args["force_basic_auth"] = True

        # query_args = dict(
        #     follow_redirects=True,
        #     validate_certs=validate_certs
        # )
        # query_args["headers"] = {'Content-type': 'application/json'}

        # if barn_vars.get("barn_user", False) and barn_vars.get("barn_password", False):
        #     query_args["url_username"] = barn_vars.get("barn_user")
        #     query_args["url_password"] = barn_vars.get("barn_password")
        #     query_args["force_basic_auth"] = True
        # elif barn_vars.get("token", False):
        #     query_args["headers"]["x-access-tokens"] = barn_vars.get(
        #         "token")

        hosts = []
        groups = []
        try:
            self.display.vvv(
                "Connect to {}/api/v1/inventory/hosts".format(barn_url))
            r = Request().open("GET", "{}/api/v1/inventory/hosts".format(barn_url), **query_args)
            hosts = json.loads(r.read()).get("result")
            self.display.vvv(json.dumps(dict(hosts=hosts)))

            self.display.vvv(
                "Connect to {}/api/v1/inventory/groups".format(barn_url))
            r = Request().open("GET", "{}/api/v1/inventory/groups".format(barn_url), **query_args)
            groups = json.loads(r.read()).get("result")
            self.display.vvv(json.dumps(dict(groups=groups)))
        except urllib_error.HTTPError as e:
            try:
                body = json.loads(e.read())
            except AttributeError:
                body = {}

            raise AnsibleParserError(message="{}: {}".format(
                body.get("status", "Unknown Error"), body.get("msg", "")))
        except urllib_error.URLError as e:  # SSL_cert_verificate_error
            msg = "{}: {}".format(e.code if hasattr(e, 'code') else "Unknown Error", str(
                e.reason) if hasattr(e, 'reason') else "Can't connect to barn")
            raise AnsibleParserError(message=msg)

        for h in hosts:
            inventory.add_host(h.get("name"))
            if barn_vars.get("fetch_variables", False):
                for k, v in h.get("vars", {}).items():
                    inventory.set_variable(h.get("name"), k, v)
        for g in groups:
            inventory.add_group(g.get("name"))
            if barn_vars.get("fetch_variables", False):
                for k, v in g.get("vars", {}).items():
                    inventory.set_variable(g.get("name"), k, v)
            for h in g.get("hosts", []):
                inventory.add_child(g.get("name"), h)
        # Add child groups
        for g in groups:
            for cg in g.get("child_groups", []):
                if cg in inventory.groups:
                    inventory.add_child(g.get("name"), cg)
