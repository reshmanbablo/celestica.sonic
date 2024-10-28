#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# config_utils
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.utils import (
    dict_diff,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.sonic import (
    run_commands,
)
import ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils as cmn
from ansible.utils.display import Display

display = Display()

# Constants
COMMON_NAME = 'common'
CREATE_NAME = 'create'
DELETE_NAME = 'delete'
CMD_NAME = 'cmd'
VAL_NAME = 'val'
CONFIG_NAME = 'config'
STATE_NAME = 'state'
STATE_MERGED = 'merged'
STATE_DELETED = 'deleted'

class SonicConfigClickCli(object):
    def __init__(self, config_inst):
        self.config_inst = config_inst
        self.state = config_inst._module.params.get(STATE_NAME)

    # Parse click_cli_token dict & derive the command based on requested state
    def derive_command(self, node):
        #display.vvv("derive_command(), node: %s, state: %s" % (node, self.state))
        result = ''
        if isinstance(node, dict):
            if COMMON_NAME in node:
                result = result + node[COMMON_NAME]
            if self.state in [STATE_MERGED]:
                result = result + ' ' + node[CREATE_NAME]
            elif self.state in [STATE_DELETED]:
                result = result + ' ' + node[DELETE_NAME]
            else: pass
        else:
            result = node

        return result

    def generate_commands_for_list(self, path, nodes, result):
        #display.vvv("generate_commands_for_list(): %s, path: %s, nodes: %s, state: %s, result: %s" % (path, nodes, state, result))
        path_parts = path.split('.')
        # Locate the list node from module_ref
        tmp_node = cmn.get_module_ref(self.config_inst._module)
        for path_part in path_parts:
            if not path_part in tmp_node:
                tmp_node = None
                break
            else:
                tmp_node = tmp_node[path_part]

        if not tmp_node:
            return

        #display.vvv("generate_commands_for_list(), tmp_node: %s" % (tmp_node))
        command_str_common = None
        if cmn.CLICK_CLI_TOKEN_NAME in tmp_node:
            command_str_common = self.derive_command(tmp_node[cmn.CLICK_CLI_TOKEN_NAME])

        # Process the list
        for node in nodes:
            command = ''
            if command_str_common:
                command = command + command_str_common
            for k, v in node.items():
                #display.vvv("generate_commands_for_list(), k: %s, v: %s" % (k, v))
                if k in tmp_node:
                    if isinstance(tmp_node[k], dict):
                        if cmn.CLICK_CLI_TOKEN_NAME in tmp_node[k]:
                            command = command + ' ' + self.derive_command(tmp_node[k][cmn.CLICK_CLI_TOKEN_NAME])
                if v:
                    command = command + ' ' + str(v)
            #display.vvv("generate_commands_for_list(), command: %s" % (command))
            result.append(command)

        #display.vvv("generate_commands_for_list(), result: %s" % (result))
        return

    def generate_command(self, node, path, command):
        #display.vvv("generate_command(), node: %s, path: %s, command: %s" % (node, path, command))
        if cmn.CLICK_CLI_TOKEN_NAME in node:
            if command[CMD_NAME]:
                command[CMD_NAME] = command[CMD_NAME] + ' '
            command[CMD_NAME] = command[CMD_NAME] + self.derive_command(node[cmn.CLICK_CLI_TOKEN_NAME])

        if not path:
            #display.vvv("generate_command(), command: %s" % (command))
            return command

        path_parts = path.split('.', 1)
        #display.vvv("generate_command(), path_parts: %s" % (path_parts))
        path_first_part = path_parts[0]
        path_left = None
        if len(path_parts) > 1:
            path_left = path_parts[1]
        if path_first_part in node:
            next_node = node[path_first_part]
            #display.vvv("generate_command(), next_node: %s" % (next_node))
            if isinstance(next_node, dict):
                self.generate_command(next_node, path_left, command)
        return command

    def generate_commands(self, paths, result):
        module_ref = cmn.get_module_ref(self.config_inst._module)
        for k, v in paths.items():
            #display.vvv("generate_commands(), k: %s, v: %s" % (k, v))
            if cmn.TYPE_NAME in v and v[cmn.TYPE_NAME] == cmn.LIST_NAME:
                self.generate_commands_for_list(k, v[VAL_NAME], result)
            else:
                command = {CMD_NAME: ''}
                self.generate_command(module_ref, k, command)
                if VAL_NAME in v:
                    val_str = str(v[VAL_NAME])
                    command[CMD_NAME] = command[CMD_NAME] + ' ' + val_str
                #display.vvv("generate_commands(), full command: %s" % (command))
                result.append(command[CMD_NAME])

    def generate_paths(self, node, parent_path, result):
        #display.vvv("generate_paths(), node: %s, parent_path: %s, result: %s" % (node, parent_path, result))
        path = ''
        for k, v in node.items():
            #display.vvv("generate_paths(), k: %s, v: %s" % (k, v))
            if not parent_path:
                path = k
            else:
                path = parent_path + '.' + k

            if isinstance(v, dict):
                self.generate_paths(v, path, result)
            elif isinstance(v, list):
                path_val = dict()
                path_val.update({cmn.TYPE_NAME: cmn.LIST_NAME})
                path_val.update({VAL_NAME: v})
                result.update({path: path_val})
            else:
                path_val = dict()
                path_val.update({VAL_NAME: v})
                #display.vvv("generate_paths(), path_val: %s" % (path_val))
                result.update({path: path_val})

    def build_config(self, want, have, state):
        result = list()
        paths = dict()
        want_tmp = {CONFIG_NAME: want}
        have_tmp = {CONFIG_NAME: have}
        diff = dict_diff(have_tmp, want_tmp)

        display.vvv("build_config(), want: %s, have: %s, diff: %s" % (want_tmp, have_tmp, diff))
        # Return when diff is empty
        if not diff:
            return result

        self.generate_paths(diff, None, paths)
        display.vvv("build_config(), paths: %s" % (paths))

        self.generate_commands(paths, result)
        display.vvv("build_config(), result: %s" % (result))

        return result

