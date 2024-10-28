#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# config_sonic_cli
import os
import json
from copy import deepcopy

from ansible.module_utils._text import to_text
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.sonic_network_config import (
    SonicNetworkConfig,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    remove_empties,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.sonic import (
    run_commands,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.conv_utils import (
    translate,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.sonic_cli import (
    RootNode,
)
import ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils as cmn

class SonicConfigSonicCli(object):

    # Constructor
    def __init__(self, config_obj):
        self.config_obj = config_obj
        self.resource_tree = cmn.get_resource_tree(config_obj._module)

    def build_config(self, want, have, state):
        """
        Build configurations from facts

        :param want: The configuration from play
        :param have: The configuration in managed node
        :param state: The state from playbook

        :returns config (list): List of generated config commands
        """
        config = None
        haveLocal = None
        # self.resource_tree.dump()

        # 1. Get RootNode instance
        root = self.resource_tree
        if not root:
            cmn.log(f"Internal error: resource tree is empty")
            return

        # 2. Extract have & want nodes without config
        haveLocal = have.get('config', None)
        wantLocal = want

        # 3. Call buildConfig of root object
        config = root.buildConfig(wantLocal, haveLocal, state)

        return config

