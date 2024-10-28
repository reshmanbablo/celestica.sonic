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
The module file for vrf_router
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
module: vrf_router
version_added: 1.0.0
short_description: Resource module to configure static routes, router-id in non-default VRF.
description:
  - This module configures and manages static routes, router-id in non-default VRF on devices running Celestica SONiC NOS.
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
notes:
  - Tested against Advanced Celestica SONiC, release 2.0.
  - This module works with connection C(network_cli).
options:
  config:
    description:
      - A dictionary of static route configurations in non-default VRF.
    type: dict
    suboptions:
      # VRF config
      vrf:
        description:
          - VRF static route configuration.
        type: list
        elements: dict
        suboptions:
          name:
            description:
              - VRF name, shall be prefixed with 'Vrf' pattern. Maximum of 15 characters.
            type: str
            required: true

          # IPv4 router config in non-default VRF.
          ipv4:
            description:
              - IPv4 router configuration in default VRF.
            type: dict
            suboptions:
              # IPv4 router-id config in non-default VRF.
              router-id:
                description:
                  - IPv4 address to use as router identifier.
                type: str

              # IPv4 static route config in non-default VRF.
              route:
                description:
                  - IPv4 static route configuration in non-default VRF.
                type: list
                elements: dict
                suboptions:
                  destination:
                    description:
                      - Destination prefix address with mask
                    type: str
                    required: true
                  next-hops:
                    description:
                      - Next hop configuration
                    type: list
                    elements: dict
                    suboptions:
                      next-hop:
                        description:
                          - Next-hop router configuration
                          - IP address, interface name, blackhole, Null0 are allowed
                        type: str
                        required: true
                      next-hop-vrf:
                        description:
                          - Next hope VRF name, shall be prefixed with 'Vrf' pattern. Maximum of 15 characters.
                        type: str
                      interface:
                        description:
                          - IP gateway interface name
                        type: str
                      onlink:
                        description:
                          - Option to specify the nexthop as directly attached to the interface
                          - Valid only when interface is passed
                        type: bool
                      distance:
                        description:
                          - Distance value. Range is 1-255.
                        type: int
                      tag:
                        description:
                          - Tag value. Range is 1-4294967295.
                          - Valid only when distance is passed
                        type: int

          # IPv6 router config in default VRF.
          ipv6:
            description:
              - IPv6 router configuration in default VRF.
            type: dict
            suboptions:
              # IPv6 router-id config in default VRF.
              router-id:
                description:
                  - IPv6 address to use as router identifier.
                type: str

              # IPv6 static route config in non-default VRF.
              route:
                description:
                  - IPv6 static route configuration in non-default VRF.
                type: list
                elements: dict
                suboptions:
                  destination:
                    description:
                      - Destination prefix address with mask
                    type: str
                    required: true
                  next-hops:
                    description:
                      - Next hop configuration
                    type: list
                    elements: dict
                    suboptions:
                      next-hop:
                        description:
                          - Next-hop router configuration
                          - IP address, interface name, blackhole, Null0 are allowed
                        type: str
                        required: true
                      next-hop-vrf:
                        description:
                          - Next hope VRF name, shall be prefixed with 'Vrf' pattern. Maximum of 15 characters.
                        type: str
                      interface:
                        description:
                          - IP gateway interface name
                        type: str
                      onlink:
                        description:
                          - Option to specify the nexthop as directly attached to the interface
                          - Valid only when interface is passed
                        type: bool
                      distance:
                        description:
                          - Distance value. Range is 1-255.
                        type: int
                      tag:
                        description:
                          - Tag value. Range is 1-4294967295.
                          - Valid only when distance is passed
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
# Celestica-DS1000# show running-config
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Merge VRF Static Route Configuration
      celestica.sonic.vrf_router:
        config:
          vrf:
            - name: Vrf1
              ipv4:
                router-id: 10.1.1.1
                route:
                  - destination: 20.1.1.0/24
                    next-hops:
                      - next-hop: 1.1.1.1
                        next-hop-vrf: Vrf2
                        interface: Ethernet1
                        onlink: true
                        distance: 2
                        tag: 23
                      - next-hop: 2.2.2.2
                        distance: 3
                        tag: 33
                  - destination: 30.1.1.0/24
                    next-hops:
                      - next-hop: Null0
                        distance: 4
                        tag: 44
            - name: Vrf2
              ipv6:
                route:
                  - destination: 1002:64:cf7::/64
                    next-hops:
                      - next-hop: 2002:53:be2:30::64
                        next-hop-vrf: Vrf1
                        interface: Ethernet1
                        onlink: true
                      - next-hop: blackhole
                        distance: 2
                        tag: 2
        state: merged

# After state:
# ------------
#
# Celestica-DS1000# show running-config
# !
# vrf Vrf1
#  ip router-id 10.1.1.1
#  ip route 20.1.1.0/24 1.1.1.1 Ethernet1 tag 23 2 nexthop-vrf Vrf2 onlink
#  ip route 20.1.1.0/24 2.2.2.2 tag 33 3
#  ip route 30.1.1.0/24 Null0 tag 44 4
# exit-vrf
# !
# vrf Vrf2
#  ipv6 route 1002:64:cf7::/64 2002:53:be2:30::64 Ethernet1 nexthop-vrf Vrf1 onlink
#  ipv6 route 1002:64:cf7::/64 blackhole tag 2 2
# exit-vrf
# Celestica-DS1000#


# Using state : deleted
#
# Before state:
# -------------
#
# Celestica-DS1000# show running-config
# !
# vrf Vrf1
#  ip router-id 10.1.1.1
#  ip route 20.1.1.0/24 1.1.1.1 Ethernet1 tag 23 2 nexthop-vrf Vrf2 onlink
#  ip route 20.1.1.0/24 2.2.2.2 tag 33 3
#  ip route 30.1.1.0/24 Null0 tag 44 4
# exit-vrf
# !
# vrf Vrf2
#  ipv6 route 1002:64:cf7::/64 2002:53:be2:30::64 Ethernet1 nexthop-vrf Vrf1 onlink
#  ipv6 route 1002:64:cf7::/64 blackhole tag 2 2
# exit-vrf
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Delete VRF Static Route Configuration
      celestica.sonic.vrf_router:
        config:
          vrf:
            - name: Vrf1
              ipv4:
                router-id: 10.1.1.1
                route:
                  - destination: 20.1.1.0/24
                    next-hops:
                      - next-hop: 1.1.1.1
                        next-hop-vrf: Vrf2
                        interface: Ethernet1
                        onlink: true
                        distance: 2
                        tag: 23
                  - destination: 30.1.1.0/24
                    next-hops:
                      - next-hop: Null0
                        distance: 4
                        tag: 44
            - name: Vrf2
              ipv6:
                route:
                  - destination: 1002:64:cf7::/64
                    next-hops:
                      - next-hop: blackhole
                        distance: 2
                        tag: 2
        state: deleted

# After state:
# ------------
#
# Celestica-DS1000# show running-config
# !
# vrf Vrf1
#  ip route 20.1.1.0/24 2.2.2.2 tag 33 3
# exit-vrf
# !
# vrf Vrf2
#  ipv6 route 1002:64:cf7::/64 2002:53:be2:30::64 Ethernet1 nexthop-vrf Vrf1 onlink
# exit-vrf
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
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.vrf_router.vrf_router import Vrf_routerArgs
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.config.vrf_router.vrf_router import Vrf_router


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Vrf_routerArgs.argument_spec,
                           supports_check_mode=True)

    result = Vrf_router(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
