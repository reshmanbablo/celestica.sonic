#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The module file for facts
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: facts
author:  Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
short_description: Get facts about Celestica SONiC devices.
description:
  - Collects facts from network devices running the Celestica SONiC network operating
    system. This module places the facts collected in the fact tree indexed by the
    respective resource name.  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
version_added: 1.0.0
notes:
- Tested against Advanced Celestica SONiC 2.0
- Legacy fact gathering C(gather_subset) is not supported in current release
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all, min, hardware, config, legacy, and interfaces. Can specify a
        list of values to include a larger subset. Values can also be used
        with an initial C(!) to specify that a specific subset should
        not be collected.
    required: false
    type: list
    elements: str
    default: '!config'
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all and the resources like interface, vlan, bgp, etc.
        Can specify a list of values to include a larger subset. Values
        can also be used with an initial C(!) to specify that a
        specific subset should not be collected.
        List of all available network resources supported by the device
        can be gatherd using C(available_network_resources)
        See EXAMPLES.
    required: false
    type: list
    elements: str
  available_network_resources:
    description:
      - Provides the list of network resources for which resource modules are available when set as V(true).
        See EXAMPLES.
    type: bool
    default: false
"""

EXAMPLES = """
- name: Get all network resources
  celestica.sonic.facts:
    available_network_resources: true

- name: Gather all facts
  celestica.sonic.facts:
    gather_subset: all
    gather_network_resources: all

- name: Gather only the NTP facts
  celestica.sonic.facts:
    gather_network_resources:
      - ntp

- name: Gather VLAN and interface facts.
  celestica.sonic.facts:
    gather_network_resources:
      - vlan
      - interface

- name: Gather facts except SNMP and VxLAN
  celestica.sonic.facts:
    gather_network_resources:
      - "!snmp"
      - "!vxlan"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list
ansible_net_gather_network_resources:
  description: The list of network resource subset names collected from the device
  returned: when gather_network_resources is configured
  type: list
ansible_network_resources:
  description: The list of fact for network resource subsets collected from the device
  returned: when gather_network_resource is configured
  type: list
available_network_resources:
  description: The list of network resources for which resource modules are available.
  returned: when available_network_resources is configured as true
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.facts.facts import FactsArgs
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.facts import (
    RESOURCE_SUBSETS,
    Facts,
)

def main():
    """
    Main entry point for module execution

    :returns: ansible_facts
    """
    module = AnsibleModule(argument_spec=FactsArgs.argument_spec,
                           supports_check_mode=True)

    warnings = []
    ansible_facts = {}

    if module.params.get("available_network_resources"):
        ansible_facts["available_network_resources"] = sorted(
            RESOURCE_SUBSETS.keys(),
        )

    result = Facts(module).get_facts()

    additional_facts, additional_warnings = result
    ansible_facts.update(additional_facts)
    warnings.extend(additional_warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
