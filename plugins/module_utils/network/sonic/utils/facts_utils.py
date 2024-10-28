#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# facts_utils
import os
import yaml
import json
from copy import deepcopy

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible.module_utils._text import to_text
from ansible.utils.display import Display
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    remove_empties,
    validate_config,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.facts_click_cli import (
    SonicFactsClickCli,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.facts_sonic_cli import (
    SonicFactsSonicCli,
)
import ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils as cmn

# Get resource name
def get_resource_name(facts_inst):
    result = None
    if hasattr(facts_inst, '_resource_name'):
        result = facts_inst._resource_name

    return result

# Set resource name
def set_resource_name(facts_inst, name):
    facts_inst._resource_name = name

# Get internal facts instance
def get_facts_inst_internal(facts_obj, meta_ref):
    result = None

    # Get the node OS type (CLS or AF-CLS)
    os_type = cmn.get_os_type(facts_obj._module)
    # Get the command mode based on meta_ref & node OS type
    cmd_mode = cmn.get_command_mode(facts_obj._module)

    # cmn.log_vars(cmd_mode=cmd_mode)
    # Get facts internal instance
    if cmd_mode is cmn.CMD_MODE_CLICK_CLI:
        result = SonicFactsClickCli(facts_obj, meta_ref)
    elif cmd_mode is cmn.CMD_MODE_FRR_CLI:
        result = SonicFactsFrrCli(facts_obj, meta_ref)
    elif cmd_mode is cmn.CMD_MODE_SONIC_CLI:
        result = SonicFactsSonicCli(facts_obj, meta_ref)
    else: pass

    return result

def init_facts_internal(facts_inst, resource_name, module,
                        subspec, options, argument_spec):
        set_resource_name(facts_inst, resource_name)
        facts_inst._module = module
        facts_inst.argument_spec = argument_spec
        spec = deepcopy(facts_inst.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        facts_inst.generated_spec = utils.generate_dict(facts_argument_spec)

def populate_facts(facts_obj, connection, ansible_facts, data=None):
    result = dict()
    facts = dict()
    facts_full = None
    facts_validated = None
    facts_tmp = None
    resource_name = None

    # 1. Get resource name
    resource_name = get_resource_name(facts_obj)
    if not resource_name:
        msg=to_text("Failed to locate resource name")
        facts_obj._module.fail_json(msg=msg, errors="surrogate_then_replace")

    if connection:  # just for linting purposes, remove
        pass

    # 2. Load meta file for the resource
    meta_file = cmn.get_meta_file_name(resource_name)
    if not os.path.exists(meta_file):
        msg=to_text("Failed to locate meta file : %s" % (meta_file))
        facts_obj._module.fail_json(msg=msg, errors="surrogate_then_replace")

    module_ref = None
    with open(meta_file) as f:
        try:
            module_ref = yaml.safe_load(f)
        except yaml.YAMLError as e:
            facts_obj._module.fail_json(msg=to_text(e), errors="surrogate_then_replace")

    if not module_ref:
        msg=to_text("Failed to load meta file : %s" % (meta_file))
        facts_obj._module.fail_json(msg=msg, errors="surrogate_then_replace")
    # Update module ref in module object for future use
    cmn.set_module_ref(facts_obj._module, module_ref)

    # Fetch db content
    # Build db dict
    # Convert db content into module args
    module_ref_tmp = deepcopy(module_ref)
    if not module_ref:
        msg=to_text("Failed to build meta blueprint")
        facts_obj._module.fail_json(msg=msg, errors="surrogate_then_replace")

    # Get internal facts instance
    facts_inst_internal = get_facts_inst_internal(facts_obj, module_ref)
    if not facts_inst_internal:
        msg=to_text("Failed to create internal facts object")
        facts_obj._module.fail_json(msg=msg, errors="surrogate_then_replace")

    facts_full, facts_tmp = facts_inst_internal.generate_facts(module_ref_tmp, None)
    # display.vvv("populate_facts(), facts_full: %s facts_tmp: %s" % (facts_full, facts_tmp))
    #if not facts_full:
    #    return result

    if facts_tmp:
        # Render config
        facts_tmp = facts_inst_internal.render_config(facts_tmp)
        #display.vvv("facts_tmp : %s" % (facts_tmp))
    else:
        facts[resource_name] = dict()

    if facts_tmp:
        # Validate config
        params = validate_config(facts_obj.argument_spec, facts_tmp)
        # cmn.log_vars(params=params)
        if params:
            facts_validated = remove_empties(params)
        parsed_pretty = json.dumps(facts_validated, indent=4)
        # display.vvv(f"{parsed_pretty}")
        # cmn.log_vars(facts_validated=facts_validated)
        # validate_config will inject state as part of facts input,
        # so remove the state key
        if cmn.Constant.STATE_NAME in facts_validated:
            facts_validated.pop(cmn.Constant.STATE_NAME, None)
        facts[resource_name] = facts_validated

    # Update facts_full in module object for future use
    cmn.set_facts_full(facts_obj._module, facts_validated)
    # Update resource tree in module object for future use
    cmn.set_resource_tree(facts_obj._module, facts_inst_internal.get_resource_tree())

    ansible_facts['ansible_network_resources'].update(facts)
    # cmn.log_vars(ansible_facts=ansible_facts)
    return ansible_facts

