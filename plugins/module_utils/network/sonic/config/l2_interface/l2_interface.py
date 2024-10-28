#
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The l2_interface class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.cfg.base import (
    ConfigBase,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.config_utils import (
    execute_module_internal,
    build_config,
)

RESOURCE_NAME = 'l2_interface'

class L2_interface(ConfigBase):
    """
    The l2_interface class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l2_interface',
    ]

    def __init__(self, module):
        super(L2_interface, self).__init__(module)

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        return execute_module_internal(self, RESOURCE_NAME)
