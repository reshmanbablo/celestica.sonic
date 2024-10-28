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
The module file for vlan
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
module: vlan
version_added: 1.0.0
short_description: Resource module to configure VLAN interface.
description:
  - This module configures and manages VLAN interface on devices running Celestica SONiC NOS.
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
notes:
  - Tested against Advanced Celestica SONiC, release 2.0.
  - This module works with connection C(network_cli).
options:
  config:
    description:
      - A dictionary of VLAN interface configurations.
    type: dict
    suboptions:
      # VLAN Interface config
      interface:
        description:
          - Interface configuration
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - Full name of the interface, i.e. Vlan10. Vlan ID Range is 1-4092.
            type: str
            required: true
          enabled:
            description:
              - Admin state of the interface
            type: bool
          description:
            description:
              - Description of the interface
            type: str
          mtu:
            description:
              - MTU configuration
              - Range is 1312-9216
            type: int

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
# Celestica-DS1000# show running-config interface Vlan
# !
# interface Vlan 101
# Celestica-DS1000#
# Play:
# ----
#

    - name: Merge Vlan Configuration
      celestica.sonic.vlan:
        config:
          interface:
            - name: Vlan102
              enabled: true
              description: "Internal Vlan"
              mtu: 1313
            - name: Vlan103
              enabled: false
        state: merged

# After state:
# ------------
#
# Celestica-DS1000# show running-config interface Vlan
# !
# interface Vlan 101
# !
# interface Vlan 102
#  description "Internal Vlan"
#  mtu 1313
#  no shutdown
# !
# interface Vlan 103
#  shutdown
# Celestica-DS1000#


# Using state : deleted
#
# Before state:
# -------------
#
# Celestica-DS1000# show running-config interface Vlan
# !
# interface Vlan 101
# !
# interface Vlan 102
#  description "Internal Vlan"
#  mtu 1313
#  no shutdown
# !
# interface Vlan 103
#  shutdown
# Celestica-DS1000#
#
# Play:
# ----
#

    - name: Delete Vlan Configuration
      celestica.sonic.vlan:
        config:
          interface:
            - name: Vlan102
              enabled: true
              description: "Internal Vlan"
              mtu: 1313
            - name: Vlan101
        state: deleted

# After state:
# ------------
#
# Celestica-DS1000# show running-config interface Vlan
# !
# interface Vlan 102
#  mtu 9100
#  shutdown
# !
# interface Vlan 103
#  shutdown
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
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.vlan.vlan import VlanArgs
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.config.vlan.vlan import Vlan


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=VlanArgs.argument_spec,
                           supports_check_mode=True)

    result = Vlan(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
