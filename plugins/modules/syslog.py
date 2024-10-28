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
The module file for syslog
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
module: syslog
version_added: 1.0.0
short_description: Resource module to configure syslog.
description:
  - This module configures and manages syslog on devices running Celestica SONiC NOS.
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
notes:
  - Tested against Advanced Celestica SONiC, release 2.0.
  - This module works with connection C(network_cli).
options:
  config:
    description:
      - Specifies configurations.
    type: dict
    suboptions:
      # Syslog server config
      server:
        description:
          - Server configuration.
        type: list
        elements: dict
        suboptions:
          ip-addr:
            description:
              - IPv4 or IPv6 address of server
            type: str
            required: true

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
# Celestica-DS1000# show running-config syslog
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Merge Syslog server Configuration
      celestica.sonic.syslog:
        config:
          server:
            - ip-addr: 1.1.1.1
            - ip-addr: 2.2.2.2
        state: merged

# After state:
# ------------
#
# Celestica-DS1000# show running-config syslog
# !
# syslog server 1.1.1.1
# syslog server 2.2.2.2
# Celestica-DS1000#


# Using state : deleted
#
# Before state:
# -------------
#
# Celestica-DS1000# show running-config syslog
# !
# syslog server 1.1.1.1
# syslog server 2.2.2.2
# Celestica-DS1000#
#
# Play:
# ----
#
    - name: Delete Syslog server Configuration
      celestica.sonic.syslog:
        config:
          server:
            - ip-addr: 1.1.1.1
        state: deleted

# After state:
# ------------
#
# Celestica-DS1000# show running-config syslog
# !
# syslog server 2.2.2.2
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
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.syslog.syslog import SyslogArgs
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.config.syslog.syslog import Syslog


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=SyslogArgs.argument_spec,
                           supports_check_mode=True)

    result = Syslog(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
