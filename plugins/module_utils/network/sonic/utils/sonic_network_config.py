#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# sonic_network_config
from copy import deepcopy

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import (
    NetworkConfig,
    dumps,
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
import ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils as cmn

from ansible.utils.display import Display
display = Display()

class SonicNetworkConfig(NetworkConfig):

    # Constructor
    def __init__(
        self, indent=1, contents=None, comment_tokens=None, ignore_lines=None
    ):
        super().__init__(indent=indent, contents=contents,
                         comment_tokens=comment_tokens,
                         ignore_lines=ignore_lines)

    # Get partial or full matched path
    def get_object_partial(self, path, is_full_match):
        #display.vvv("get_object_partial(), path: %s, path[-1]: %s, path[:-1]: %s" % (path, path[-1], path[:-1]))
        result = list()
        # Full match case
        if is_full_match:
            result = self.get_object(path)
            return result

        # Partial match case
        for item in self.items:
            #display.vvv("get_object_partial(), item.text: %s" % (item.text))
            # Append SPACE with key pattern for exact match
            if item.text.startswith(path[-1] + ' ') or item.text == path[-1]:
                #display.vvv("get_object_partial(), item.parents: %s" % (item.parents))
                if item.parents == path[:-1]:
                    result.append(item)

        return result

    # Get partial or full matched block
    def get_block_partial(self, path, is_full_match):
        matches = list()
        result = list()
        #cmn.log_vars(path=path)

        if not isinstance(path, list):
            raise AssertionError("path argument must be a list object")

        # Full match case
        if is_full_match:
            result = self.get_block(path)
            return result

        # Partial match case
        for item in self.items:
            # Append SPACE with key pattern for exact match
            cmd = path[-1]
            if item.text.startswith(cmd + ' '):
                parent_cmds = path[:-1]
                if item.parents and parent_cmds:
                    if check_parents_partial_match(item.parents, parent_cmds):
                        matches.append(item)
                        #cmn.log("Adding %s with parent partial matched to matches" % (item.text))
                else:
                    matches.append(item)
                    #cmn.log("Adding %s without parent partial matched to matches" % (item.text))

        # Expand all blocks
        for match in matches:
            self._expand_block(match)
            #cmn.log("match-text=%s, match-line=%s, match-children=%s" % (match.text, match.line, match.children))
            result.append(match)

        return result

    # Check whether all parent nodes matches with parent_cmds
    def check_parents_partial_match(parent_nodes, parent_cmds):
        result = True

        #cmn.log_vars(parent_nodes=parent_nodes, parent_cmds=parent_cmds)
        if not parent_nodes or not parent_cmds:
            result = False
            return result

        for index, node in enumerate(parent_nodes):
            cmd = None
            if node.text:
                cmd = parent_cmds.pop()
            if cmd and not node.text.startswith(cmd + ' '):
                result = False
                break

        return result

    # Remove empty block
    def remove_empty_block(self, cmd, parent_cmds):
        result = False
        cmds = list()

        # Form cmds to search
        if parent_cmds:
            cmds.extend(parent_cmds)
        cmds.append(cmd)

        # Find the block
        obj = self.get_object(cmds)

        # Check whether the block is empty
        if obj and not obj.has_children:
            result = True

        # Remove the block, if empty
        if result:
            self.items.remove(obj)
        # TODO : Remove the cmd from children list of parent_cmds
        # otherwise, empty parent mode cannot be removed.

        return result

