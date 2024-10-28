#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# config_utils
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.config_click_cli import (
    SonicConfigClickCli,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.config_sonic_cli import (
    SonicConfigSonicCli,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    to_list,
    remove_empties,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.sonic import (
    run_commands,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.facts import Facts
import ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils as cmn
from ansible.utils.display import Display

display = Display()

# Get internal config instance
def get_config_inst_internal(config_inst):
    result = None

    # Get the node OS type (CLS or AF-CLS)
    os_type = cmn.get_os_type(config_inst._module)
    # Get the command mode based on module_ref & node OS type
    cmd_mode = cmn.get_command_mode(config_inst._module)

    # Get config internal instance
    if cmd_mode is cmn.CMD_MODE_CLICK_CLI:
        result = SonicConfigClickCli(config_inst)
    elif cmd_mode is cmn.CMD_MODE_FRR_CLI:
        result = SonicConfigFrrCli(config_inst)
    elif cmd_mode is cmn.CMD_MODE_SONIC_CLI:
        result = SonicConfigSonicCli(config_inst)
    else: pass

    return result

# Get facts_internal
def get_facts_internal(config_inst, resource_name):
    """ Get the 'facts' (the current configuration)

    :rtype: A dictionary
    :returns: The current configuration as a dictionary
    """
    facts, _warnings = Facts(config_inst._module).get_facts(config_inst.gather_subset,
                                                             config_inst.gather_network_resources)
    resource_facts = facts['ansible_network_resources'].get(resource_name)
    return resource_facts

def execute_module_internal(config_inst, resource_name):
    """ Execute the module

    :rtype: A dictionary
    :returns: The result from module execution
    """
    result = {'changed': False}
    warnings = list()
    commands = list()

    existing_facts = get_facts_internal(config_inst, resource_name)

    commands.extend(set_config_internal(config_inst, existing_facts))
    cmd_mode = cmn.get_command_mode(config_inst._module)
    if commands:
        if not config_inst._module.check_mode:
            response = run_commands(config_inst._module, mode=cmd_mode,
                                    commands=commands, config=True)
        result['changed'] = True
    result['commands'] = commands

    result['before'] = existing_facts
    if result['changed']:
        changed_facts = get_facts_internal(config_inst, resource_name)
        result['after'] = changed_facts

    result['warnings'] = warnings
    return result

def set_config_internal(config_inst, existing_facts):
    """ Collect the configuration from the args passed to the module,
        collect the current configuration (as a dict from facts)

    :rtype: A list
    :returns: the commands necessary to migrate the current configuration
              to the desired configuration
    """
    want = remove_empties(config_inst._module.params['config'])
    have = existing_facts
    commands = build_config(config_inst, want, have)
    return to_list(commands)

# Build configurations based on want & have facts
def build_config(config_inst, want, have):
    result = list()

    # cmn.log_vars(want=want, have=have)
    # 1. Get state from playbook
    state = config_inst._module.params.get(cmn.Constant.STATE_NAME, None)
    if not state:
        cmn.log(f"state is missing in playbook")
        return

    # 2. Get internal config instance
    config_inst_internal = get_config_inst_internal(config_inst)
    if not config_inst_internal:
        msg=to_text("Failed to create internal config object")
        config_inst._module.fail_json(msg=msg, errors="surrogate_then_replace")

    result = config_inst_internal.build_config(want, have, state)

    return result

