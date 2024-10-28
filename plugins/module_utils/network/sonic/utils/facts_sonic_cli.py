#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# facts_utils
import os
from copy import deepcopy

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

from ansible.utils.display import Display
display = Display()

SONIC_CLI_NAME = 'sonic_cli'
CREATE_NAME = 'create'
DELETE_NAME = 'delete'
DELIMITER_REF_LINE = ' '
DELIMITER_REF_LINE_WORD = '='
DELIMITER_ANSIBLE_WORD = '&'
DELIMITER_ANSIBLE_WORD_TOKENS = ':'
PARAMETER_INDICATOR = '$'
DOUBLE_QUOTE_CHAR = '"'
DELIMITER_CLI_COMMAND_WORD = ' '


LIST_INDICATOR = 'LIST'
SKIP_INDICATOR = 'SKIP'
KEYS_INDICATOR = 'KEYS'
MODE_INDICATOR = 'MODE'
NAME_INDICATOR = 'NAME'
ANSIBLE_NODE_NAME = 'ANISBLE_NODE'
TRANSLATE_METHOD_NAME = 'TRANSLATE_METHOD'

class RefLine(object):

    # Constructor
    def __init__(self, line):
        self.line = line
        self.list_name = None
        self.list_keys = None
        self.positional_keys = list()
        self.found_first_param = False
        self.mode_based = False
        self.command_to_search = ''
        self.cli_to_ansible_map = dict()
        self.parse(line)
        display.vvv(f"RefLine() - cli_to_ansible_map: {self.cli_to_ansible_map}")
        display.vvv(f"RefLine() - command_to_search: {self.command_to_search}")

    def append_to_command_search(self, word):
        # Stop forming the partial command when the first parameter token is found
        if self.found_first_param:
            return

        if self.command_to_search:
            self.command_to_search = self.command_to_search + DELIMITER_CLI_COMMAND_WORD
        self.command_to_search = self.command_to_search + word

    def parse(self, line):
        display.vvv(f"parse() - line: {line}")
        # Return when line is empty
        if not line:
            return

        # Extract one token at a time with DELIMITER_REF_LINE
        line_parts = line.split(DELIMITER_REF_LINE, 1)
        display.vvv(f"parse() - line_parts: {line_parts}")
        first_part = line_parts[0]
        second_part = None
        if len(line_parts) > 1:
            second_part = line_parts[1]

        # Process first_part
        second_part = self.parse_word(first_part, second_part)

        # If second_part is empty, return
        if not second_part:
            return

        # If the second_part is param node,
        # proceed until a non-param node is found
        if second_part.startswith(PARAMETER_INDICATOR):
            line_left = self.parse_param_node(first_part, second_part)
            if line_left:
                self.parse(line_left)
        # If the second_part is non-param node, call recursively
        else:
            self.parse(second_part)

        return

    def parse_word(self, word, line):

        line_left = line
        ansible_node_name = None

        # Process based on DELIMITER_REF_LINE_WORD
        if DELIMITER_REF_LINE_WORD in word:
            word_parts = word.split(DELIMITER_REF_LINE_WORD)
            display.vvv(f"parse_word() - word_parts: {word_parts}")
            cli_word = word_parts[0]
            ansible_word = word_parts[1]
            ansible_node_name, line_left = self.parse_ansible_word(cli_word, ansible_word, line)
            if line_left != line:
                return line_left
        else:
            cli_word = word
            ansible_node_name = word

        # Form the partial command to search, stop until first parameter is found
        if cli_word.startswith(PARAMETER_INDICATOR):
            self.found_first_param = True
        else:
            self.append_to_command_search(cli_word)
            # Update cli_to_ansible_map
            node = {cli_word: ansible_node_name}
            self.cli_to_ansible_map.update(node)

        return line_left

    def parse_ansible_word(self, cli_word, word, line):
        ansible_node_name = None
        list_name = None
        list_keys = None
        mode_based = False
        line_left = line

        # Process based on DELIMITER_REF_LINE_WORD
        word_parts = word.split(DELIMITER_ANSIBLE_WORD)
        for word_part in word_parts:
            tokens = word_part.split(DELIMITER_ANSIBLE_WORD_TOKENS)
            token_type = tokens[0]
            # NAME:<ansible-node-name> - Name of ansible node
            if token_type == NAME_INDICATOR:
                ansible_node_name = tokens[1]
            # LIST:<ansible-node-name>, Name of ansible node, type as list
            if token_type == LIST_INDICATOR:
                list_name = tokens[1]
            # KEYS:<ansible-node-name>[|<ansible-node-name>], List of key nodes
            if token_type == KEYS_INDICATOR:
                list_keys = tokens[1]
            # SKIP - Indicates that no ansible node to respective cli_word
            if token_type == SKIP_INDICATOR:
                ansible_node_name = SKIP_INDICATOR
            # MODE - Indicates that respective cli_word is MODE based or not
            if token_type == MODE_INDICATOR:
                mode_based = True

        if word_parts:
            display.vvv(f"parse_ansible_word() - ansible_node_name: {ansible_node_name}, list_name: {list_name}, list_keys: {list_keys}, mode_based: {mode_based}")
        # Parse list
        if list_name:
            # Update cli_to_ansible_map
            node = {cli_word: ansible_node_name}
            self.cli_to_ansible_map.update(node)
            self.append_to_command_search(cli_word)
            self.list_name = list_name
            self.list_keys = list_keys
            self.mode_based = mode_based
            line_left = self.parse_list(line)
        # Parse mode - TODO

        return ansible_node_name, line_left

    def parse_param_node(self, param_node_name, line):
        display.vvv(f"parse_param_node() - line: {line}")
        param_nodes = list()
        line_left = line
        while(True):
            # Break the loop when non-param node is found
            # Break the loop when the line_left is empty, end of line, return
            if not line_left or not line_left.startswith(PARAMETER_INDICATOR):
                break
            # Continue extracting one token at a time
            line_parts = line_left.split(DELIMITER_REF_LINE, 1)
            # Append first_part to param_nodes
            first_part = line_parts[0]
            param_nodes.append(first_part)
            # Extract the second_part
            second_part = None
            if len(line_parts) > 1:
                second_part = line_parts[1]
            line_left = second_part
            # Mark the first_param_found flag
            self.found_first_param = True

        # Append to cli_to_ansible_map
        node = {param_node_name: param_nodes}
        display.vvv(f"parse_param_node() - node: {node}, line_left: {line_left}")
        self.cli_to_ansible_map.update(node)

        return line_left

    def parse_list(self, line):
        display.vvv(f"parse_list() - line: {line}")
        line_left = line
        # List handling, skip the immediate set of key parameter nodes
        # Typically all key parameter nodes will follow the cli_word of list
        if self.list_name:
            while True:
                line_parts = line_left.split(DELIMITER_REF_LINE, 1)
                display.vvv(f"parse_list() - line_parts: {line_parts}")
                first_part = line_parts[0]
                second_part = None
                if len(line_parts) > 1:
                    second_part = line_parts[1]
                self.positional_keys.append(first_part)
                line_left = second_part
                # Continue until end of line or until found a non-param node
                if not second_part or not second_part.startswith(PARAMETER_INDICATOR):
                    break
        # Mark indication that first param is found
        if self.positional_keys:
            self.found_first_param = True
        display.vvv(f"parse_list() - positional_keys: {self.positional_keys}, line_left: {line_left}")
        return line_left

    def find_matching_commands(self, nw_config):
        found = False

        if self.command_to_search:
            self.matching_commands = nw_config.get_object_partial([self.command_to_search], False)

        if self.matching_commands:
            found = True

        display.vvv(f"find_matching_commands() - matching_commands: {self.matching_commands}")
        return found

    def build_facts(self, root_node):
        facts = dict()
        if not self.matching_commands:
            return

        # Iterate each matching command & form the facts
        for matching_command in self.matching_commands:
            self.build_facts_single_command(matching_command, root_node)

    def build_facts_single_command(self, command_obj, root_node):
        prev_node = root_node
        command_left = command_obj.line

        # Iterate cli_to_ansible_map & process each item
        while True:
            display.vvv(f"build_facts_single_command() - command_left: {command_left}")
            # Terminate condition
            if not command_left:
                break

            # Remove one token from the command
            command_parts = command_left.split(DELIMITER_CLI_COMMAND_WORD, 1)
            first_part = command_parts[0]
            if len(command_parts) > 1:
                command_left = command_parts[1]

            # Identify cli_word from command & ansible_word from the token
            cli_word = first_part
            if cli_word not in self.cli_to_ansible_map:
                display.vvv(f"build_facts_single_command() - cli_word: {cli_word} not found in map")
                continue
            ansible_word = self.cli_to_ansible_map.get(cli_word)
            if not ansible_word:
                display.vvv(f"build_facts_single_command() - ansible_word for {cli_word} is empty")
                continue
            display.vvv(f"build_facts_single_command() - cli_word: {cli_word}, ansible_word: {ansible_word}")

            if isinstance(ansible_word, list): # Parameters case
                display.vvv(f"build_facts_single_command() - cli_word: {cli_word}, ansible_word: {ansible_word}")
                # Iterate each param, extract value, add to facts
                for param_node in ansible_word:
                    param_node_name = param_node.split(PARAMETER_INDICATOR, 1)[1]
                    param_value, command_left_updated = self.extract_param_value(command_left)
                    display.vvv(f"build_facts_single_command() - param_node_name: {param_node_name}, param_value: {param_value}, command_left_updated: {command_left_updated}")
                    new_node = {param_node_name: param_value}
                    prev_node.update(new_node)
                    command_left = command_left_updated
            else:
                # Create dict and add to root node
                if ansible_word not in prev_node:
                    new_node = {ansible_word: dict()}
                    prev_node.update(new_node)
                # Update prev_node for next iteration
                prev_node = prev_node[ansible_word]

    def extract_param_value(self, command):
        param_val = None
        command_left = None
        if command.startswith(DOUBLE_QUOTE_CHAR): # Quoted string as param value
            param_val = re.findall(r'"([^"]*)"', command)
            command_parts = command.split(DOUBLE_QUOTE_CHAR, 2)
            if len(command_parts) > 1:
                command_left = command_parts[1]
        else:
            command_parts = command.split(DELIMITER_CLI_COMMAND_WORD, 1)
            param_val = command_parts[0]
            if len(command_parts) > 1:
                command_left = command_parts[1]

        return param_val, command_left

class SonicFactsSonicCli(object):

    # Constructor
    def __init__(self, facts_inst, module_ref):
        self.facts_inst = facts_inst
        self.module_ref = module_ref
        self.resource_tree = None

    def get_resource_tree(self):
        return self.resource_tree

    def process_ref_line(self, line):
        ref_line_obj = RefLine(line)
        return ref_line_obj

    def generate_facts(self, node, db_data):
        # TODO: Remove reading config from temp file
        TEST_CONFIG_FILE = '/tmp/show-run-test'
        result = dict()
        facts = dict()
        config_response = ''
        # 1) Get current running config
        if os.path.isfile(TEST_CONFIG_FILE):
            with open(TEST_CONFIG_FILE) as f:
                for line in f:
                    config_response = config_response + line
        else:
            config_response = cmn.get_config(self.facts_inst._module, cmn.CMD_MODE_SONIC_CLI)
        # cmn.log_vars(config_response=config_response)

        if not config_response:
            return result, facts

        # 2) Load running config into SonicNetworkConfig class for easy parsing
        nw_cfg_obj = SonicNetworkConfig()
        nw_cfg_obj.load(config_response)
        #for cfg_line_obj in nw_cfg_obj._items:
        #    display.vvv("generate_facts(), cfg_line_obj.raw: %s" % (cfg_line_obj.raw))
        #    display.vvv("generate_facts(), cfg_line_obj.text: %s" % (cfg_line_obj.text))
        #    display.vvv("generate_facts(), cfg_line_obj.children: %s" % (cfg_line_obj.children))
        #    display.vvv("generate_facts(), cfg_line_obj._children: %s" % (cfg_line_obj._children))
        #    display.vvv("generate_facts(), cfg_line_obj._parents: %s" % (cfg_line_obj._parents))

        # Load SONIC_CLI_NAME from module_ref content
        module_ref_sonic_cli = self.module_ref.get(SONIC_CLI_NAME)
        if not module_ref_sonic_cli:
            return result, facts
        #display.vvv("generate_facts(), module_ref_sonic_cli: %s" % (module_ref_sonic_cli))
        #display.vvv("generate_facts(), __name__: %s" % (inspect.__name__))
        cmn.log_vars(module_ref_sonic_cli=module_ref_sonic_cli)

        self.resource_tree = RootNode()
        self.resource_tree.buildTree(module_ref_sonic_cli)
        self.resource_tree.dump()
        self.resource_tree.buildCmdsToSearch()
        self.resource_tree.generateFacts(nw_cfg_obj, facts)
        if facts:
            facts = {'config': facts}
        # cmn.log_vars(facts=facts)
        # Locate the CREATE block inside SONIC_CLI_NAME, this is meant for building the facts
        # module_ref_lines = module_ref_sonic_cli.get(CREATE_NAME)
        # if not module_ref_lines:
        #     return result, facts

        #display.vvv("generate_facts(), module_ref_lines: %s" % (module_ref_lines))
        # Start processing all lines from module_ref, For each line,
        # for line in module_ref_lines:
        #     display.vvv(f"generate_facts(), line: {line}")
            #ref_line = RefLine(line)
            #ref_line.find_matching_commands(nw_cfg_obj)
            #ref_line.build_facts(facts)
        # cmn.log_vars(result=result, facts=facts)
        return (result, facts)

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        result = None
        config = deepcopy(conf)
        result = remove_empties(config)
        #cmn.log_vars(result=result)
        return result

