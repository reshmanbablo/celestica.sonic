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
The module file for l3_access_list
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
module: l3_access_list
version_added: 1.0.0
short_description: Resource module to configure L3 access list.
description:
  - This module configures and manages L3 access list on devices running Celestica SONiC NOS.
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
notes:
  - Tested against Advanced Celestica SONiC, release 2.0.
  - This module works with connection C(network_cli).
options:
  config:
    description:
      - A dictionary of access list configurations.
    type: dict
    suboptions:
      # IPv4 access-list config
      access-list-ipv4:
        description:
          - IPv4 access list configuration
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - Access list name
            type: str
            required: true
          # Sequence numbers under IPv4 access-list config
          sequence-numbers:
            description:
              - Seqeuce number under access list configuration
            type: list
            elements: dict
            suboptions:
              seq:
                description:
                  - Sequence number. Range is 1-4294967295.
                type: int
                required: true
              action:
                description:
                  - Packet action.
                type: str
                choices: [deny, permit]
              prefix:
                description:
                  - IPv4 prefix with mask, 'any' keyword is allowed too.
                type: str
              remark:
                description:
                  - Remark configuration. Comment up to 100 characters.
                type: str

      # IPv6 access-list config
      access-list-ipv6:
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
            elements: dict
            suboptions:
              seq:
                description:
                  - Sequence number. Range is 1-4294967295.
                type: int
                required: true
              action:
                description:
                  - Packet action.
                type: str
                choices: [deny, permit]
              prefix:
                description:
                  - IPv6 prefix with mask, 'any' keyword is allowed too.
                type: str
              remark:
                description:
                  - Remark configuration. Comment up to 100 characters.
                type: str

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
# Celestica-DS1000# show running-config
# !
# ip-accesslist aclv4_test2 seq 5 permit 1.1.1.0/24
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Merge L3 Access List Configuration
      celestica.sonic.l3_access_list:
        config:
          access-list-ipv4:
            - name: aclv4_test1
              sequence-numbers:
                - seq: 2
                  action: permit
                  prefix: any
                - seq: 7
                  action: deny
                  prefix: 10.1.1.0/24
            - name: aclv4_test2
              sequence-numbers:
                - seq: 3
                  action: deny
                  prefix: any
          access-list-ipv6:
            - name: aclv6_test1
              sequence-numbers:
                - seq: 4
                  action: permit
                  prefix: 10::/64
        state: merged


# After state:
# ------------
#
# Celestica-DS1000# show running-config
# !
# ip-accesslist aclv4_test2 seq 5 permit 1.1.1.0/24
# ip-accesslist aclv4_test1 seq 2 permit any
# ip-accesslist aclv4_test1 seq 7 deny 10.1.1.0/24
# ip-accesslist aclv4_test2 seq 3 deny any
# !
# ipv6-accesslist aclv6_test1 seq 4 permit 10::/64
# Celestica-DS1000#


# Using state : deleted
#
# Before state:
# -------------
# Celestica-DS1000# show running-config
# !
# ip-accesslist aclv4_test2 seq 5 permit 1.1.1.0/24
# ip-accesslist aclv4_test1 seq 2 permit any
# ip-accesslist aclv4_test1 seq 7 deny 10.1.1.0/24
# ip-accesslist aclv4_test2 seq 3 deny any
# !
# ipv6-accesslist aclv6_test1 seq 4 permit 10::/64
# Celestica-DS1000#
#
# Play:
# ----
#

    - name: Delete L3 Access List Configuration
      celestica.sonic.l3_access_list:
        config:
          access-list-ipv4:
            - name: aclv4_test1
              sequence-numbers:
                - seq: 2
                  action: permit
                  prefix: any
            - name: aclv4_test2
              sequence-numbers:
                - seq: 3
                  action: deny
                  prefix: any
          access-list-ipv6:
            - name: aclv6_test1
              sequence-numbers:
                - seq: 4
                  action: permit
                  prefix: 10::/64
        state: deleted

# After state:
# ------------
#
# Celestica-DS1000# show running-config
# !
# ip-accesslist aclv4_test2 seq 5 permit 1.1.1.0/24
# ip-accesslist aclv4_test1 seq 7 deny 10.1.1.0/24
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
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.l3_access_list.l3_access_list import L3_access_listArgs
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.config.l3_access_list.l3_access_list import L3_access_list


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=L3_access_listArgs.argument_spec,
                           supports_check_mode=True)

    result = L3_access_list(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
