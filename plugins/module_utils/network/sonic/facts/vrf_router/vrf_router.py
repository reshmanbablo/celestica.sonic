#
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vrf_router fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.facts_utils import (
    init_facts_internal,
    populate_facts,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.vrf_router.vrf_router import Vrf_routerArgs

RESOURCE_NAME = 'vrf_router'

class Vrf_routerFacts(object):
    """ The vrf_router fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        return init_facts_internal(self, RESOURCE_NAME, module, subspec, options,
                                   Vrf_routerArgs.argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for vrf_router
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        return populate_facts(self, connection, ansible_facts, data)
