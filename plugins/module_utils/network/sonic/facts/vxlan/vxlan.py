#
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vxlan fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.facts_utils import (
    init_facts_internal,
    populate_facts,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.vxlan.vxlan import VxlanArgs

RESOURCE_NAME = 'vxlan'

class VxlanFacts(object):
    """ The vxlan fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        return init_facts_internal(self, RESOURCE_NAME, module, subspec, options,
                                   VxlanArgs.argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for vxlan
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        return populate_facts(self, connection, ansible_facts, data)
