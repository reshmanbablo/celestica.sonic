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
The module file for sag
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
module: sag
version_added: 1.0.0
short_description: Resource module to configure SAG(Static Anycast Gateway).
description:
  - This module configures and manages SAG(Static Anycast Gateway) on devices running Celestica SONiC NOS.
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
notes:
  - Tested against Advanced Celestica SONiC, release 2.0.
  - This module works with connection C(network_cli).
options:
  config:
    description:
      - A dictionary of SAG(Static Anycast Gateway) configurations.
    type: dict
    suboptions:
      # SAG(Static Anycast Gateway) config
      mac:
        description:
          - SAG(Static Anycast Gateway) MAC address configuration
          - Allowed to configure ONE MAC address entry only in the device.
        type: list
        elements: dict
        suboptions:
          address:
            description:
              - MAC address.
            type: str
            required: true

      # SAG(Static Anycast Gateway) config in VLAN interface
      vlan:
        description:
          - SAG(Static Anycast Gateway) configuration in VLAN interface
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - Full name of the interface, i.e. Vlan10. Vlan ID Range is 1-4092.
            type: str
            required: true
          sag-ip:
            description:
              - SAG(Static Anycast Gateway) IPv4 & IPv6 configuration in VLAN interface
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
# Celestica-DS1000# show sag mac
# ---------------------
# SAG MAC
# ---------------------
# ---------------------
# Celestica-DS1000#
#
# Play:
# ----
#

    - name: Merge SAG Mac Address Configuration
      celestica.sonic.sag:
        config:
          mac:
            - address: 10:20:30:40:50:60
        state: merged

# After state:
# ------------
#
# Celestica-DS1000# show sag mac
# ---------------------
# SAG MAC
# ---------------------
# 10:20:30:40:50:60
# ---------------------
# Celestica-DS1000#


# Using state : merged
#
# Before state:
# -------------
#
# Celestica-DS1000# show sag interface
# ------------------------------------------------------------------------------
# Vlan                IP address
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Number of SAG Interfaces:0
# ------------------------------------------------------------------------------
# Celestica-DS1000#
#
# Play:
# ----
#

    - name: Merge SAG IP Configuration
      celestica.sonic.sag:
        config:
          vlan:
            - name: Vlan102
              sag-ip: 1.1.1.1
            - name: Vlan101
              sag-ip: 2.2.2.2
        state: merged


# After state:
# ------------
#
# Celestica-DS1000# show sag interface
# ------------------------------------------------------------------------------
# Vlan                IP address
# ------------------------------------------------------------------------------
# Vlan101             2.2.2.2
# Vlan102             1.1.1.1
# ------------------------------------------------------------------------------
# Number of SAG Interfaces:2
# ------------------------------------------------------------------------------
# Celestica-DS1000#


# Using state : deleted
#
# Before state:
# -------------
#
# Celestica-DS1000# show sag mac
# ---------------------
# SAG MAC
# ---------------------
# 10:20:30:40:50:60
# ---------------------
# Celestica-DS1000#
# Celestica-DS1000# show sag interface
# ------------------------------------------------------------------------------
# Vlan                IP address
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Number of SAG Interfaces:0
# ------------------------------------------------------------------------------
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Delete SAG Mac Address Configuration
      celestica.sonic.sag:
        config:
          mac:
            - address: 10:20:30:40:50:60
        state: deleted

# After state:
# ------------
# Celestica-DS1000# show sag mac
# ---------------------
# SAG MAC
# ---------------------
# ---------------------
# Celestica-DS1000# show sag interface
# ------------------------------------------------------------------------------
# Vlan                IP address
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# Number of SAG Interfaces:0
# ------------------------------------------------------------------------------
# Celestica-DS1000#


# Using state : deleted
#
# Before state:
# -------------
# Celestica-DS1000# show sag interface
# ------------------------------------------------------------------------------
# Vlan                IP address
# ------------------------------------------------------------------------------
# Vlan101             2.2.2.2
# Vlan102             1.1.1.1
# ------------------------------------------------------------------------------
# Number of SAG Interfaces:2
# ------------------------------------------------------------------------------
# Celestica-DS1000#
#
# Play:
# ----
#

    - name: Delete SAG IP Configuration
      celestica.sonic.sag:
        config:
          vlan:
            - name: Vlan102
              sag-ip: 1.1.1.1
        state: deleted

# After state:
# ------------
#
# Celestica-DS1000# show sag interface
# ------------------------------------------------------------------------------
# Vlan                IP address
# ------------------------------------------------------------------------------
# Vlan101             2.2.2.2
# ------------------------------------------------------------------------------
# Number of SAG Interfaces:1
# ------------------------------------------------------------------------------
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
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.sag.sag import SagArgs
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.config.sag.sag import Sag


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=SagArgs.argument_spec,
                           supports_check_mode=True)

    result = Sag(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
