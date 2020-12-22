#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a virtual module that is entirely implemented as an action plugin and runs on the controller

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: barn_read
version_added: 2.9.9
short_description: Read variables from Barn
description:
  - The M(barn_read) module reads variables from the barn server
  - This task only has an action plugin. You can run the task even when no connection to the host is possible. 
options:
  barn_host:
    description:
      - hostname or IP address of Barn server
      - This option has been deprecated in favor of C(barn_url).
    type: str
    version_added: '2.9.9'
  barn_port:
    description:
      - Specific port for Barn server
      - This option has been deprecated in favor of C(barn_url).
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
  load_to_facts:
    description:
      - If true the variables will be added in the hostvars of the host.
    type: bool
    default: False
    version_added: '2.9.9'
  include:
    description:
      - Include only certain variables. Especially helpful when load_to_facts==True
    type: list
    default: []
    version_added: '2.9.9'
  exclude:
    description:
      - Exclude certain variables. Especially helpful when load_to_facts==True
    type: list
    default: []
    version_added: '2.9.9'
notes:
- barn_read is an action plugin, without a module. 
author:
- Sander Descamps <sander_descamps@hotmail.com>
'''

EXAMPLES = r'''
  - name: Read info from Barn
    barn_read:
      barn_host: "127.0.0.1"
      barn_user: "admin"
      barn_password: "admin"
      barn_port: 5000
      load_to_facts: False
    register: output_barn_read

  - name: Load specific variable from barn and add them to hostvars
    barn_read:
      barn_host: "127.0.0.1"
      barn_user: "admin"
      barn_password: "admin"
      barn_port: 5000
      load_to_facts: True
      include:
        - environment
        - application_id

  - name: Load all variable except some and add them to hostvars
    barn_read:
      barn_host: "127.0.0.1"
      barn_user: "admin"
      barn_password: "admin"
      barn_port: 5000
      load_to_facts: True
      exclude:
        - pointlessvariable  
'''
