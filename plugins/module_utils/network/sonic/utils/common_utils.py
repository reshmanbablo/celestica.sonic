#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# common_utils

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re, os
import inspect
from enum import StrEnum
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.sonic import (
    run_commands,
)
from ansible.module_utils.six import iteritems
from ansible.utils.display import Display

from ansible.utils.display import Display
display = Display()

# Constants
DB_VAL_NAME = 'db_val'
DB_FIELD_NAME = 'db_field'
DB_KEY_NAME = 'db_key'
DB_TABLE_NAME = 'db_table'
DB_VAL_TRANSLATED_NAME = 'db_val_translated'
DB_TRANSLATE_METHOD_NAME = 'db_translate_method'
CLICK_CLI_TOKEN_NAME = 'click_cli_token'
TYPE_NAME = 'type'
LIST_NAME = 'list'

OS_TYPE_CLS = 'CLS'
OS_TYPE_ADV_CLS = 'ADV-CLS'
COMMAND_MODES_NAME = 'command_modes'
CMD_MODE_CLICK_CLI = 'click_cli'
CMD_MODE_FRR_CLI = 'frr_cli'
CMD_MODE_SONIC_CLI = 'sonic_cli'

SRC_RUNNING_NAME = 'running'
SHOW_RUN_CFG_CLCK_CMD = 'show runningconfiguration all'
SHOW_RUN_CFG_FRR_CMD = 'show running-config no-header'
SHOW_RUN_CFG_SONIC_CLI_CMD = 'show running-config'
SHOW_STARTUP_CFG_CLCK_CMD = 'show startupconfiguration'
SHOW_STARTUP_CFG_FRR_CMD = 'show startup-config'
SHOW_STARTUP_CFG_SONIC_CLI_CMD = 'show startup-config'

class Constant(StrEnum):
    SONIC_CLI_NAME = 'sonic_cli'
    CREATE_NAME = 'create'
    DELETE_NAME = 'delete'
    DELIMITER_REF_LINE = ' '
    INDICATOR_ANSIBLE_WORD = '='
    DELIMITER_ANSIBLE_WORD = '&'
    DELIMITER_ANSIBLE_WORD_TOKEN = ':'
    PARAMETER_INDICATOR = '$'
    DOUBLE_QUOTE_CHAR = '"'
    DELIMITER_CLI_COMMAND_WORD = ' '
    DELIMITER_LIST_PATH = '/'
    DELIMITER_LIST_KEYS = '|'
    DELIMITER_LIST_KEY_PAIR = '='
    CLI_COMMAND_NO_KEYWORD_TOKEN = 'no'
    BASE_VAL_STR = 'base_val'
    COMPARABLE_VAL_STR = 'comparable_val'

    # LIST_KEY_OPEN_CHAR & LIST_KEY_CLOSE_CHAR are meant to mark list node in 
    # list path. During expandFacts & compressFacts, need to differentiate
    # list node and non-list node
    LIST_KEY_OPEN_CHAR= '['
    LIST_KEY_CLOSE_CHAR= ']'
    LIST_INDICATOR = 'LIST'
    LIST_GROUP_INDICATOR = 'LIST_GROUP'
    INTERFACE_LIST_INDICATOR = 'INTERFACE_LIST'
    INTERFACE_PARAM_INDICATOR = 'INTERFACE_PARAM'
    SKIP_INDICATOR = 'SKIP'
    OPTIONAL_INDICATOR = 'OPTIONAL'
    KEYS_INDICATOR = 'KEYS'
    VALUE_INDICATOR = 'VALUE'
    NAME_INDICATOR = 'NAME'
    EMPTY_INDICATOR = 'EMPTY'
    NOT_EMPTY_INDICATOR = 'NOT_EMPTY'
    PARENT_NAME_INDICATOR = 'PARENT_NAME'
    TRANSLATE_METHOD_INDICATOR = 'TRANSLATE_METHOD'
    VALUE_CHECK_METHOD_INDICATOR = 'VALUE_CHECK_METHOD'
    NO_PARAM_INDICATOR = 'NO_PARAM'
    # TODO : Revisit replacing below with single flag
    IGN_VAL_FOR_DEL_INDICATOR = 'IGN_VAL_FOR_DEL'
    IGN_WORD_FOR_DEL_INDICATOR = 'IGN_WORD_FOR_DEL'
    NEGATE_CMD_INDICATOR = 'NEGATE_CMD'
    NEGATE_CMD_ALLOW = 'ALLOW'
    NEGATE_CMD_SKIP = 'SKIP'
    MERGE_AS_REPLACE = 'MERGE_AS_REPLACE'
    ANSIBLE_NODE_NAME = 'ANISBLE_NODE'
    TRANSLATE_METHOD_NAME = 'TRANSLATE_METHOD'
    COMMAND_INDICATOR = 'command'
    SUBCOMMAND_INDICATOR = 'subcommand'
    EXIT_CMD_INDICATOR = 'EXIT_CMD'
    IF_PARENT_VAL_INDICATOR = 'IF_PARENT_VAL'
    IF_FACTS_PRESENT_INDICATOR = 'IF_FACTS_PRESENT'
    IF_NEXT_VAL_INDICATOR = 'IF_NEXT_VAL'
    DELIMITER_IF_NEXT_VAL = '@'

    # Interface names
    IF_NAME_VXLAN = 'vxlan'
    VTEP_PREFIX = 'vtep'

    # state values
    STATE_NAME = 'state'
    STATE_MERGED = 'merged'
    STATE_DELETED = 'deleted'
    STATE_REPLACED = 'replaced'
    STATE_OVERRIDDEN = 'overridden'

meta_attrs_g = [DB_TABLE_NAME, DB_KEY_NAME, DB_FIELD_NAME, DB_TRANSLATE_METHOD_NAME, CLICK_CLI_TOKEN_NAME, TYPE_NAME, COMMAND_MODES_NAME]

# Find OS type of current node
def find_os_type(module):
    result = None

    cmd = 'show version'
    response = run_commands(module, mode=CMD_MODE_CLICK_CLI, commands=cmd)
    # Run commands returns list, so extract the result alone
    if not response:
        return result
    cmd_response = response[0]

    cmd_response_lines = cmd_response.split('\n')
    line = None
    for line in cmd_response_lines:
        if line.startswith('SONiC Software Version:'):
            break
    if line:
        if "SONiC-OS-celestica_sonic" in line:
            result = OS_TYPE_CLS
        elif "SONiC-OS-advanced_celestica_sonic" in line:
            result = OS_TYPE_ADV_CLS
        else: pass

    # log_vars(os_type=result)
    set_os_type(module, result)

    return result

# Find command mode to be used for the current node
def find_command_mode(module):
    result = None

    # Get OS type from current node
    os_type = find_os_type(module)
    # Get module reference data
    module_ref = get_module_ref(module)
    # Extract the supported command modes
    cmd_modes = module_ref.get(COMMAND_MODES_NAME)
    # log_vars(cmd_modes=cmd_modes)

    if os_type and cmd_modes:
        if os_type == OS_TYPE_CLS:
            if CMD_MODE_CLICK_CLI in cmd_modes:
                result = CMD_MODE_CLICK_CLI
            elif CMD_MODE_FRR_CLI in cmd_modes:
                result = CMD_MODE_FRR_CLI
            else: pass
        elif os_type == OS_TYPE_ADV_CLS:
            # For Adv CLS SONiC, sonic-cli is preferred,
            # otherwise fallback as CLS SONiC
            if CMD_MODE_SONIC_CLI in cmd_modes:
                result = CMD_MODE_SONIC_CLI
            elif CMD_MODE_CLICK_CLI in cmd_modes:
                result = CMD_MODE_CLICK_CLI
            elif CMD_MODE_FRR_CLI in cmd_modes:
                result = CMD_MODE_FRR_CLI
            else: pass
        else: pass

    # log_vars(command_mode=result)
    set_command_mode(module, result)

    return result

# Set os type into module object
def set_os_type(module, val):
    module._sonic_os_type = val

# Get os type from module object
def get_os_type(module):
    result = None

    if hasattr(module, '_sonic_os_type'):
        result = module._sonic_os_type
    else:
        result = find_os_type(module)

    return result

# Set command mode into module object
def set_command_mode(module, val):
    module._sonic_command_mode = val

# Get command mode from module object
def get_command_mode(module):
    result = None

    if hasattr(module, '_sonic_command_mode'):
        result = module._sonic_command_mode
    else:
        result = find_command_mode(module)

    return result

# Set resource_tree into module object
def set_resource_tree(module, val):
    module._sonic_resource_tree = val

# Get resource_tree from module object
def get_resource_tree(module):
    result = None
    if hasattr(module, '_sonic_resource_tree'):
        result = module._sonic_resource_tree
    return result

# Set module_ref into module object
def set_module_ref(module, val):
    module._sonic_module_ref = val

# Get module_ref from module object
def get_module_ref(module):
    result = None
    if hasattr(module, '_sonic_module_ref'):
        result = module._sonic_module_ref
    return result

# Set facts_full into module object
def set_facts_full(module, val):
    module._sonic_facts_full = val

# Get facts_full from module object
def get_facts_full(module):
    result = None
    if hasattr(module, '_sonic_facts_full'):
        result = module._sonic_facts_full
    return result


# Copy all meta data related attributes from one dict to another
def copy_meta_attrs(src, dst):
    if not src:
        return
    for attr in meta_attrs_g:
        if attr in src:
            dst.update({attr: src.get(attr)})

# Check whether an attribute is meta data related
def is_meta_attr(name):
    return True if name in meta_attrs_g else False

# Get meta file name for the resource
def get_meta_file_name(resource_name):
    result = None
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # log_vars(dir_path=dir_path)
    if resource_name:
        result = "%s/../meta/%s/%s.yml" % \
                 (dir_path, \
                  resource_name, resource_name)
    return result

# Get module state
def get_module_state(module):
    result = None
    if module and module.params and 'state' in module.params:
        result = module.params.get('state')
    return result

# Check whether mode is click_cli mode or not
def is_click_cli_mode(mode):
    if mode and mode == CMD_MODE_CLICK_CLI:
        return True
    else:
        return False

# Check whether mode is frr_cli mode or not
def is_frr_cli_mode(mode):
    if mode and mode == CMD_MODE_FRR_CLI:
        return True
    else:
        return False

# Check whether mode is sonic_cli mode or not
def is_sonic_cli_mode(mode):
    if mode and mode == CMD_MODE_SONIC_CLI:
        return True
    else:
        return False

# Form get_config command
def form_get_config_command(mode, src, config_module):
    result = None
    if is_click_cli_mode(mode):
        if src == SRC_RUNNING_NAME:
           result = SHOW_RUN_CFG_CLCK_CMD
        else:
           result = SHOW_STARTUP_CFG_CLCK_CMD
    elif is_frr_cli_mode(mode):
        if src == SRC_RUNNING_NAME:
           result = SHOW_RUN_CFG_FRR_CMD
        else:
           result = SHOW_STARTUP_CFG_FRR_CMD
        if config_module:
           result = 'do ' + result
    elif is_sonic_cli_mode(mode):
        if src == SRC_RUNNING_NAME:
           result = SHOW_RUN_CFG_SONIC_CLI_CMD
        else:
           result = SHOW_STARTUP_CFG_SONIC_CLI_CMD

    return result

def get_config(module, mode):
    result = None

    cmd = form_get_config_command(mode, SRC_RUNNING_NAME, False)
    if not cmd:
        return result

    response = run_commands(module, mode=mode, commands=cmd)
    # Run commands returns list, so extract the result alone
    if not response:
        return result

    result = response[0]

    #display.vvv("get_config(), result: %s" % (result))
    return result

def log(args):
    className = None
    if "self" in inspect.stack()[1][0].f_locals:
        className = inspect.stack()[1][0].f_locals["self"].__class__.__name__
    funcName = inspect.stack()[1][3]
    if className:
        display.vvv(f"{className}.{funcName}: {args}")
    else:
        display.vvv(f"{funcName}: {args}")

def log_vars(**kwargs):
    varStr = ""
    className = None
    if "self" in inspect.stack()[1][0].f_locals:
        className = inspect.stack()[1][0].f_locals["self"].__class__.__name__
    funcName = inspect.stack()[1][3]
    for key, value in kwargs.items():
        if varStr:
            varStr += ", "
        varStr += key + ": " + str(value)
    if className:
        display.vvv(f"{className}.{funcName}: {varStr}")
    else:
        display.vvv(f"{funcName}: {varStr}")

