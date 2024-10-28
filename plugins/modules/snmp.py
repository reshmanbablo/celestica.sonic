#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The module file for snmp
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
    'license': 'Apache 2.0'
}

DOCUMENTATION = """
---
module: snmp
version_added: 1.0.0
short_description: Resource module to configure SNMP.
description:
  - This module configures and manages SNMP on devices running Celestica SONiC NOS.
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
notes:
  - Tested against Advanced Celestica SONiC, release 2.0.
  - This module works with connection C(network_cli).
options:
  config:
    description:
      - A dictionary of SNMP configurations
    type: dict
    suboptions:
      # SNMP server config
      snmp-server:
        description:
          - SNMP server global configurations
        type: dict
        suboptions:
          contact:
            description:
              - Contact information. Maximum of 255 characters.
            type: str
          location:
            description:
              - Location information. Maximum of 255 characters.
            type: str

      # SNMP agent config
      agent-address:
        description:
          - SNMP Agent address configuration
        type: list
        elements: dict
        suboptions:
          ip-addr:
            description:
              - IP address
            type: str
            required: true
          port:
            description:
              - Port number
              - Range is 1024-65535
              - Default 161
            type: int
          vrf:
            description:
              - VRF name
              - Maximum of 15 characters
              - Shall be prefixed with 'Vrf' keyword
            type: str

      # SNMP community config
      community:
        description:
          - SNMP community configuration
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - Community string. (4-32 characters ; no space, comma, @ allowed)
            type: str
            required: true
          access:
            description:
              - Community access type
            type: str
            choices: [read-only, read-write]

      # Trap receiver config
      trap-host:
        description:
          - Trap host configurations
        type: list
        elements: dict
        suboptions:
          ip-addr:
            description:
              - IP address
            type: str
            required: true
          version:
            description:
              - SNMP version number
              - Range is 1-3
            type: int
            required: true
          port:
            description:
              - Port number
              - Range is 1024-65535
              - Default 161
            type: int
          vrf:
            description:
              - VRF name
              - Maximum of 15 characters
              - Shall be prefixed with 'Vrf' keyword
            type: str
          community:
            description:
              - Community string. (4-32 characters ; no space, comma, @ allowed)
            type: str

      # SNMPv3 user config
      user:
        description:
          - SNMPv3 user configurations
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - User name. Maximum of 32 characters.
            type: str
            required: true
          user-type:
            description:
              - User type
            type: str
            choices: [noAuthNoPriv, AuthNoPriv, Priv]
          auth-algorithm:
            description:
              - Authentication algorithm
              - Valid only when user-type has AuthNoPriv or Priv
            type: str
            choices: [sha, md5]
          encrypted-auth-password:
            description:
              - Authentication password as encrypted
              - Valid only when user-type has AuthNoPriv or Priv
            type: str
          encrypt-algorithm:
            description:
              - Encryption algorithm
              - Valid only when user-type has Priv
            type: str
            choices: [aes, des]
          encrypted-encrypt-password:
            description:
              - Encryption password as encrypted
              - Valid only when user-type has Priv
            type: str
          access:
            description:
              - User access type
            type: str
            choices: [read-only, read-write]

  state:
    description:
      - The state of the configuration after module completion.
      - C(merged) - Merge specified configuration with on-device running configuration.
      - C(deleted) - Delete the specified on-device running configuration or applies the default value.
    type: str
    choices:
      - merged
      - deleted
    default: merged
"""
EXAMPLES = """
# Using state : merged
#
# Before state:
# -------------
#
# Celestica-DS1000# show running-config snmp
# !
# snmp-server location public
# snmp-server user user1 noAuthNoPriv RO
# snmp-server host 10.2.1.1 version 3 port 1025 vrf Vrf1
# snmp-server agent-address 10.1.1.1
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Merge SNMP Configuration
      celestica.sonic.snmp:
        config:
          snmp-server:
            contact: Celestica
            location: India
          community:
            - name: community_ro
              access: read-only
            - name: community_rw
              access: read-write
          agent-address:
            - ip-addr: 10.1.1.1
              vrf: mgmt
            - ip-addr: 10.1.1.1
              port: 1024
              vrf: mgmt
            - ip-addr: 20.1.1.1
          trap-host:
            - ip-addr: 10.2.2.1
              version: 1
              port: 1024
              vrf: mgmt
              community: community_rw
            - ip-addr: 10.2.3.1
              version: 2
          user:
            - name: user2
              user-type: Priv
              auth-algorithm: md5
              encrypted-auth-password: md5encrypt
              encrypt-algorithm: aes
              encrypted-encrypt-password: aesenencrypt
              access: read-only
            - name: user3
              user-type: AuthNoPriv
              auth-algorithm: md5
              encrypted-auth-password: md5encrypt
              access: read-only
            - name: user4
              user-type: noAuthNoPriv
              access: read-write
        state: merged

# After state:
# ------------
#
# Celestica-DS1000# show running-config snmp
# !
# snmp-server contact Celestica
# snmp-server location India
# snmp-server community community_ro RO
# snmp-server community community_rw RW
# snmp-server user user1 noAuthNoPriv RO
# snmp-server user user2 Priv MD5 encrypted-auth-password md5encrypt AES encrypted-encrypt-password aesenencrypt RO
# snmp-server user user3 AuthNoPriv MD5 encrypted-auth-password md5encrypt RO
# snmp-server user user4 noAuthNoPriv RW
# snmp-server host 10.2.2.1 version 1 community community_rw port 1024 vrf mgmt
# snmp-server host 10.2.3.1 version 2
# snmp-server host 10.2.1.1 version 3 port 1025 vrf Vrf1
# snmp-server agent-address 10.1.1.1 port 1024 vrf mgmt
# snmp-server agent-address 10.1.1.1
# snmp-server agent-address 10.1.1.1 vrf mgmt
# snmp-server agent-address 20.1.1.1
# Celestica-DS1000#


# Using state : deleted
#
# Before state:
# -------------
#
# Celestica-DS1000# show running-config snmp
# !
# snmp-server contact Celestica
# snmp-server location India
# snmp-server community community_ro RO
# snmp-server community community_rw RW
# snmp-server user user1 noAuthNoPriv RO
# snmp-server user user2 Priv MD5 encrypted-auth-password md5encrypt AES encrypted-encrypt-password aesenencrypt RO
# snmp-server user user3 AuthNoPriv MD5 encrypted-auth-password md5encrypt RO
# snmp-server user user4 noAuthNoPriv RW
# snmp-server host 10.2.2.1 version 1 community community_rw port 1024 vrf mgmt
# snmp-server host 10.2.3.1 version 2
# snmp-server host 10.2.1.1 version 3 port 1025 vrf Vrf1
# snmp-server agent-address 10.1.1.1 port 1024 vrf mgmt
# snmp-server agent-address 10.1.1.1
# snmp-server agent-address 10.1.1.1 vrf mgmt
# snmp-server agent-address 20.1.1.1
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Delete SNMP Configuration
      celestica.sonic.snmp:
        config:
          snmp-server:
            contact: Celestica
            location: India
          community:
            - name: community_ro
          agent-address:
            - ip-addr: 10.1.1.1
              vrf: mgmt
            - ip-addr: 20.1.1.1
          trap-host:
            - ip-addr: 10.2.2.1
              version: 1
            - ip-addr: 10.2.1.1
              version: 3
          user:
            - name: user2
            - name: user3
        state: deleted

# After state:
# ------------
#
# Celestica-DS1000# show running-config snmp
# !
# snmp-server location public
# snmp-server community community_rw RW
# snmp-server user user1 noAuthNoPriv RO
# snmp-server user user4 noAuthNoPriv RW
# snmp-server host 10.2.3.1 version 2
# snmp-server agent-address 10.1.1.1 port 1024 vrf mgmt
# snmp-server agent-address 10.1.1.1
# Celestica-DS1000#


"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['command 1', 'command 2', 'command 3']
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.snmp.snmp import SnmpArgs
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.config.snmp.snmp import Snmp


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=SnmpArgs.argument_spec,
                           supports_check_mode=True)

    result = Snmp(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
