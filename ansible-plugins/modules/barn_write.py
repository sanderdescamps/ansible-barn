#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a virtual module that is entirely implemented as an action plugin and runs on the controller

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: barn_write
version_added: 2.9.9
short_description: Make changes in Barn
description:
  - The M(barn_write) module manages the variables of a host inside Barn
  - This task only has an action plugin. You can run the task even when no connection to the host is possible. 
options:
  barn_host:
    description:
      - hostname or IP address of Barn server
    type: str
    version_added: '2.9.9'
  barn_port:
    description:
      - Specific port for Barn server
    type: str
    default: 443
    version_added: '2.9.9'
  barn_https:
    description:
      - Use B(https) if true
      - This option has been deprecated in favor of C(barn_url).
    type: bool
    default: true
    version_added: '2.9.9'
  barn_url:
    description:
      - Url of the barn host
      - Module will default to B(https) when no protocol is defined
      - "Examples: U(http://127.0.0.1:5000/), U(https://barn.myhomecloud.be), U(barn.myhomecloud.be)"
    type: str
    required: true
    version_added: '2.9.9'
  validate_certs:
    description:
      - Validate the ssl certificate 
    type: bool
    default: true
    version_added: '2.9.9'
  barn_user:
    description:
      - Username to authenticate against Barn
    type: str
    version_added: '2.9.9'
  barn_password:
    description:
      - Password to authenticate against Barn
    type: str
    version_added: '2.9.9'
  barn_token:
    description:
      - Authentication token instead of username and password
    type: str
    version_added: '2.9.9'
  state:
    description:
      - Whether the host is added/updated in the Barn server or removed from the Barn server. 
    type: str
    choices: [ absent, present ]
    default: present
    version_added: '2.9.9'
notes:
- barn_write is an action plugin, without a module. 
author:
- Sander Descamps <sander_descamps@hotmail.com>
'''

EXAMPLES = r'''
- name: Add host to Barn
  barn_write:
    barn_host: "127.0.0.1"
    barn_user: "admin"
    barn_password: "admin"
    barn_port: 5000
    state: present
    vars: 
      hostdef_ip: 10.6.51.32
      env_environment: development
      installed_packages:
        - "nano"
        - "vim"
        - "tcpdump"

- name: Remove old_variable from host variables inside Barn
  barn_write:
    barn_host: "127.0.0.1"
    barn_user: "admin"
    barn_password: "admin"
    barn_port: 5000
    remove_vars: 
      - old_variable

- name: Remove host from Barn
  barn_write:
    barn_host: "127.0.0.1"
    barn_user: "admin"
    barn_password: "admin"
    barn_port: 5000
    state: absent
'''
