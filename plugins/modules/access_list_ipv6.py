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
The module file for access_list_ipv6
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
module: access_list_ipv6
version_added: 1.0.0
short_description: Resource module to configure IPv6 access list.
description:
  - This module configures and manages IPv6 access list on devices running Celestica SONiC NOS.
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
notes:
  - Tested against Advanced Celestica SONiC, release 2.0.
  - This module works with connection C(network_cli).
options:
  config:
    description:
      - A dictionary of IPv6 access list configurations.
    type: dict
    suboptions:
      # IPv6 access-list config
      access-list:
        description:
          - IPv6 access list configuration
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - Access list name
            type: str
            required: true
          # Sequence numbers under IPv6 access-list config
          sequence-numbers:
            description:
              - Seqeuce number under access list configuration
            type: list
            # TODO: Add required_if for tcp & udp protocol related settings
            elements: dict
            suboptions:
              seq:
                description:
                  - Sequence number. Range is 1-65535.
                type: int
                required: true
              action:
                description:
                  - Packet action.
                type: str
                choices: [deny, permit]
              protocol:
                description:
                  - Protocol name or number.
                type: str
                choices: ['1', '2', '6', '17', '46', '47', '51', '103', '115', icmpv6, ipv6, tcp, udp]
              src:
                description:
                  - Source IPv6 prefix with mask, 'any' keyword is allowed too.
                type: str
              src-port-eq:
                description:
                  - Match only packets on a given port number. Range is 0-65535.
                  - Valid only when protocol is either tcp or udp.
                type: int
              src-port-range-start:
                description:
                  - Match only packets greater than the given port number. Range is 0-65534.
                  - Valid only when protocol is either tcp or udp.
                type: int
              src-port-range-end:
                description:
                  - Match only packets lesser than the given port number. Range is 1-65535.
                  - Valid only when protocol is either tcp or udp.
                type: int
              dst:
                description:
                  - Destination IPv6 prefix with mask, 'any' keyword is allowed too.
                type: str
              dst-port-eq:
                description:
                  - Match only packets on a given port number. Range is 0-65535.
                  - Valid only when protocol is either tcp or udp.
                type: int
              dst-port-range-start:
                description:
                  - Match only packets greater than the given port number. Range is 0-65534.
                  - Valid only when protocol is either tcp or udp.
                type: int
              dst-port-range-end:
                description:
                  - Match only packets lesser than the given port number. Range is 1-65535
                  - Valid only when protocol is either tcp or udp.
                type: int
              tcp-flag-ack:
                description:
                  - Match on the ACK  bit.
                  - Valid only when protocol is tcp.
                type: bool
              tcp-flag-fin:
                description:
                  - Match on the FIN  bit.
                  - Valid only when protocol is tcp.
                type: bool
              tcp-flag-psh:
                description:
                  - Match on the PSH  bit.
                  - Valid only when protocol is tcp.
                type: bool
              tcp-flag-rst:
                description:
                  - Match on the RST  bit.
                  - Valid only when protocol is tcp.
                type: bool
              tcp-flag-syn:
                description:
                  - Match on the SYN  bit.
                  - Valid only when protocol is tcp.
                type: bool
              tcp-flag-urg:
                description:
                  - Match on the URG  bit.
                  - Valid only when protocol is tcp.
                type: bool
              dscp:
                description:
                  - Consider only packets matching DSCP value. Range is 0-63.
                type: int

      # IPv6 access-list binding to interfaces
      interface:
        description:
          - IPv6 access list binding to interfaces.
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - Full name of the interface, i.e. Ethernet0, PortChannel10, Vlan10.
              - Ethernet, PortChannel and Vlan interfaces are allowed.
            type: str
            required: true
          access-group:
            description:
              - IPV6 access list binding to interfaces.
            type: list
            elements: dict
            suboptions:
              access-list:
                description:
                  - Access list name.
                type: str
              direction:
                description:
                  - Direction in which access-list to be applied.
                type: str
                choices: [in, out]

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
# Celestica-DS1000# show running-config ipv6 access-list
# !
# ipv6 access-list aclv6_test1
#  sequence 1 permit 2 21::22/128 any dscp 2
# !
# interface Ethernet 0
#  ipv6 access-group aclv6_test1 in
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Merge Access List IPv6 Configuration
      celestica.sonic.access_list_ipv6:
        config:
          access-list:
            - name: aclv6_test1
              sequence-numbers:
                - seq: 2
                  action: permit
                  protocol: icmpv6
                  src: 1::2/128
                  dst: 3::4/128
                  dscp: 2
                - seq: 3
                  action: permit
                  protocol: ipv6
                  src: any
                  dst: 5::6/128
                - seq: 4
                  action: permit
                  protocol: 2
                  src: 7::8/128
                  dst: any
                  dscp: 5
                - seq: 5
                  action: permit
                  protocol: tcp
                  src: 9::10/128
                  src-port-eq: 2
                  dst: 11::12/128
                  dst-port-range-start: 4
                  dst-port-range-end: 65535
                  tcp-flag-ack: true
                  tcp-flag-fin: true
                  tcp-flag-psh: true
                  tcp-flag-rst: true
                  tcp-flag-syn: true
                  tcp-flag-urg: true
            - name: aclv6_test2
              sequence-numbers:
                - seq: 1
                  action: permit
                  protocol: icmpv6
                  src: any
                  dst: any
                  dscp: 10
                - seq: 2
                  action: permit
                  protocol: udp
                  src: 13::14/128
                  src-port-range-start: 2
                  src-port-range-end: 65535
                  dst: 15::16/128
                  dst-port-range-start: 0
                  dst-port-range-end: 8
        state: merged

    - name: Merge IPv6 Access List and Interface Binding Configuration
      celestica.sonic.access_list_ipv6:
        config:
          interface:
            - name: Ethernet0
              access-group:
                - access-list: aclv6_test2
                  direction: out
            - name: Ethernet1
              access-group:
                - access-list: aclv6_test1
                  direction: in
        state: merged


# After state:
# ------------
#
# Celestica-DS1000# show running-config ipv6 access-list
# !
# ipv6 access-list aclv6_test1
#  sequence 1 permit 2 21::22/128 any dscp 2
#  sequence 2 permit icmpv6 1::2/128 3::4/128 dscp 2
#  sequence 3 permit ipv6 any 5::6/128
#  sequence 4 permit 2 7::8/128 any dscp 5
#  sequence 5 permit tcp 9::10/128 src-eq 2 11::12/128 dst-range 4 65535 fin syn rst psh ack urg
# !
# ipv6 access-list aclv6_test2
#  sequence 1 permit icmpv6 any any dscp 10
#  sequence 2 permit udp 13::14/128 src-range 2 65535 15::16/128 dst-range 0 8
# !
# interface Ethernet 0
#  ipv6 access-group aclv6_test1 in
#  ipv6 access-group aclv6_test2 out
# !
# interface Ethernet 1
#  ipv6 access-group aclv6_test1 in
# Celestica-DS1000#


# Using state : deleted
#
# Before state:
# -------------
# Celestica-DS1000# show running-config ipv6 access-list
# !
# ipv6 access-list aclv6_test1
#  sequence 1 permit 2 21::22/128 any dscp 2
#  sequence 2 permit icmpv6 1::2/128 3::4/128 dscp 2
#  sequence 3 permit ipv6 any 5::6/128
#  sequence 4 permit 2 7::8/128 any dscp 5
#  sequence 5 permit tcp 9::10/128 src-eq 2 11::12/128 dst-range 4 65535 fin syn rst psh ack urg
# !
# ipv6 access-list aclv6_test2
#  sequence 1 permit icmpv6 any any dscp 10
#  sequence 2 permit udp 13::14/128 src-range 2 65535 15::16/128 dst-range 0 8
# !
# interface Ethernet 0
#  ipv6 access-group aclv6_test1 in
#  ipv6 access-group aclv6_test2 out
# !
# interface Ethernet 1
#  ipv6 access-group aclv6_test1 in
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Delete Access List IPv6 Configuration
      celestica.sonic.access_list_ipv6:
        config:
          access-list:
            - name: aclv6_test1
              sequence-numbers:
                - seq: 4
                - seq: 5
            - name: aclv6_test2
        state: deleted

    - name: Delete IPv6 Access List and Interface Binding Configuration
      celestica.sonic.access_list_ipv6:
        config:
          interface:
            - name: Ethernet0
              access-group:
                - access-list: aclv6_test2
                  direction: out
            - name: Ethernet1
              access-group:
                - access-list: aclv6_test1
                  direction: in
        state: deleted


# After state:
# ------------
#
# Celestica-DS1000# show running-config ipv6 access-list
# !
# ipv6 access-list aclv6_test1
#  sequence 1 permit 2 21::22/128 any dscp 2
#  sequence 2 permit icmpv6 1::2/128 3::4/128 dscp 2
#  sequence 3 permit ipv6 any 5::6/128
# !
# interface Ethernet 0
#  ipv6 access-group aclv6_test1 in
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
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.access_list_ipv6.access_list_ipv6 import Access_list_ipv6Args
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.config.access_list_ipv6.access_list_ipv6 import Access_list_ipv6


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Access_list_ipv6Args.argument_spec,
                           supports_check_mode=True)

    result = Access_list_ipv6(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
