#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: config
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
short_description: Manage Celestica SONiC configuration sections
description:
- Celestica SONiC configurations use a simple block indent file syntax for segmenting configuration
  into sections. This module provides an implementation for working with Celestica SONiC configuration
  sections in a deterministic way.
version_added: 1.0.0
notes:
- Tested against Celestica SONiC 3.0
- Tested against Advanced Celestica SONiC 2.0
- Celestica SONiC version supports C(click_cli) and C(frr_cli) only in mode.
- Advanced Celestica SONiC version supports C(click_cli) and C(sonic_cli) only in mode.
- For config commands in C(click_cli) mode, module adds sudo keyword internally, hence skip sudo for config commands
options:
  mode:
    description:
    - Specifies the type of commands to be executed
      Celestica SONiC supports three command modes (Click CLI, FRR commands & sonic-cli commands).
      Click CLI commands are executed on bash prompt, based on Click python module.
      FRR commands are executed on vtysh.
      sonic-cli commands are executed on sonic-cli.
      Note - C(frr_cli) is not applicable for Advanced Celestica SONiC version, use C(sonic_cli) instead.
      See EXAMPLES.
    required: true
    type: str
    choices: [click_cli, frr_cli, sonic_cli]
  lines:
    description:
    - The ordered set of commands that should be configured in the section. The commands
      must be the exact same commands as found in the device running-config to ensure idempotency
      and correct diff. Be sure to note the configuration command syntax as some commands are
      automatically modified by the device config parser.
    type: list
    aliases:
    - commands
    elements: str
  parents:
    description:
    - The ordered set of parents that uniquely identify the section or hierarchy the
      commands should be checked against.  If the parents argument is omitted, the
      commands are checked against the set of top level or global commands.
    type: list
    elements: str
  src:
    description:
    - The I(src) argument provides a path to the configuration file to load into the
      remote system.  The path can either be a full system path to the configuration
      file if the value starts with / or relative to the root of the implemented role
      or playbook. This argument is mutually exclusive with the I(lines) and I(parents)
      arguments. The configuration lines in the source file should be similar to how it
      will appear if present in the running-configuration of the device including indentation
      to ensure idempotency and correct diff.
    type: path
  before:
    description:
    - The ordered set of commands to push on to the command stack if a change needs
      to be made.  This allows the playbook designer the opportunity to perform configuration
      commands prior to pushing any changes without affecting how the set of commands
      are matched against the system.
    type: list
    elements: str
  after:
    description:
    - The ordered set of commands to append to the end of the command stack if a change
      needs to be made.  Just like with I(before) this allows the playbook designer
      to append a set of commands to be executed after the command set.
    type: list
    elements: str
  match:
    description:
    - Instructs the module on the way to perform the matching of the set of commands
      against the current device config.  If match is set to I(line), commands are
      matched line by line.  If match is set to I(strict), command lines are matched
      with respect to position.  If match is set to I(exact), command lines must be
      an equal match.  Finally, if match is set to I(none), the module will not attempt
      to compare the source configuration with the running configuration on the remote
      device.
    default: line
    choices: [line, strict, exact, none]
    type: str
  save_when:
    description:
    - When changes are made to the device running-configuration, the changes are not
      copied to non-volatile storage by default.  Using this argument will change
      that before.  If the argument is set to I(always), then the running-config will
      always be copied to the startup-config and the I(modified) flag will always
      be set to True.  If the argument is set to I(modified), then the running-config
      will only be copied to the startup-config if it has changed since the last save
      to startup-config.  If the argument is set to I(never), the running-config will
      never be copied to the startup-config.  If the argument is set to I(changed),
      then the running-config will only be copied to the startup-config if the task
      has made a change. I(changed) was added in Ansible 2.6.
    default: never
    choices: [always, never, modified, changed]
    type: str
notes:
- To ensure idempotency and correct diff the configuration lines in the relevant module options should be similar to how they
  appear if present in the running configuration on device including the indentation.
- Idempotency is not supported for C(click_cli) mode.
"""

EXAMPLES = """
- name: Configure hostname and save as startup-config
  celestica.sonic.config:
    mode: click_cli
    lines: hostname {{ inventory_hostname }}
    save_when: modified

- name: Configure vlan & vlan members and save as startup-config
  celestica.sonic.config:
    mode: click_cli
    lines:
      - config vlan member add 10 Ethernet0
      - config vlan member del 10 Ethernet0
    before:
      - config vlan add 10
      - config vlan add 20
    save_when: always

- name: Configure BGP and save as startup-config when changed
  celestica.sonic.config:
    mode: frr_cli
    lines:
      - router bgp 1
      - address-family ipv4 unicast
      - network 1.0.0.0/8
    save_when: changed

- name: Configuer ACL rules with exact match
  celestica.sonic.config:
    mode: sonic_cli
    lines:
      - 10 permit ip 191.0.2.1/32 any
      - 20 permit ip 191.0.2.2/32 any
      - 30 permit ip 191.0.2.3/32 any
      - 40 permit ip 191.0.2.4/32 any
      - 50 permit ip 191.0.2.5/32 any
    parents: ip access-list test
    before: no ip access-list test
    match: exact

- name: Configuer ACL rules with parents and remove existing rule before applying the config
  celestica.sonic.config:
    mode: sonic_cli
    lines:
      - 10 permit ip 191.0.2.1/32 any
      - 20 permit ip 191.0.2.2/32 any
      - 30 permit ip 191.0.2.3/32 any
      - 40 permit ip 191.0.2.4/32 any
    parents: ip access-list test
    before: no ip access-list test

- name: For idempotency, use full-form commands
  celestica.sonic.config:
    mode: sonic_cli
    lines:
      - shutdown
    parents: interface Ethernet 0
"""

RETURN = """
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname foo', 'interface vlan 100', 'description Vlan100']
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname foo', 'interface vlan 100', 'description Vlan100']
saved:
  description: Returns whether the configuration is saved to the startup
               configuration or not.
  returned: When not check_mode.
  type: bool
  sample: True
"""
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import (
    NetworkConfig,
    dumps,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list

from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.sonic import (
    get_config,
    get_connection,
    run_commands,
)
import ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils as cmn

from ansible.utils.display import Display

display = Display()

def is_changed(mode, commands):
    result = False
    for command in commands:
        if cmn.is_click_cli_mode(mode):
            if command.startswith('config ') or command.startswith('sudo config '):
                result = True
                break
        elif cmn.is_frr_cli_mode(mode) or cmn.is_sonic_cli_mode(mode):
            if not command.startswith('show ') and not command.startswith('do '):
                result = True
                break
        else: pass

    return result

def get_candidate(module):
    mode = module.params['mode']
    candidate = ""
    if module.params["src"]:
        candidate = module.params["src"]
    elif module.params["lines"]:
        candidate_obj = NetworkConfig(indent=2)
        parents = module.params["parents"] or list()
        if cmn.is_click_cli_mode(mode):
            candidate_obj.add(module.params["lines"])
        else:
            candidate_obj.add(module.params["lines"], parents=parents)
        candidate = dumps(candidate_obj, "raw")
    return candidate


def form_save_config_command(mode):
    result = None
    if cmn.is_click_cli_mode(mode):
        result = list()
        result.append('config save -y')
    elif cmn.is_frr_cli_mode(mode):
        result = list()
        result.append('end')
        result.append('exit')
        result.append('sudo config save -y')
        result.append('vtysh')
        result.append('configure terminal')
    elif cmn.is_sonic_cli_mode(mode):
        result = list()
        result.append('copy running-config startup-config')
    return result


def save_config(module):
    result = False
    if not module.check_mode:
        mode = module.params['mode']
        cmds = form_save_config_command(mode)
        if cmds:
            run_commands(module, mode, cmds)
            result = True
    else:
        module.warn(
            "Skipping save_when due to check_mode.",
        )

    return result


def main():
    """main entry point for module execution"""
    argument_spec = dict(
        mode=dict(type="str", required=True, choices=["click_cli", "frr_cli", "sonic_cli"]),
        src=dict(type="path"),
        lines=dict(aliases=["commands"], type="list", elements="str"),
        parents=dict(type="list", elements="str"),
        before=dict(type="list", elements="str"),
        after=dict(type="list", elements="str"),
        match=dict(default="line", choices=["line", "strict", "exact", "none"]),
        save_when=dict(
            choices=["always", "never", "modified", "changed"],
            default="never",
        ),
    )

    mutually_exclusive = [("lines", "src"), ("parents", "src")]

    required_if = [
        ("match", "strict", ["lines", "src"], True),
        ("match", "exact", ["lines", "src"], True),
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
        supports_check_mode=True,
    )

    warnings = list()

    result = {"changed": False, "warnings": warnings}

    config = None

    mode = module.params["mode"]
    path = module.params["parents"]
    connection = get_connection(module)
    contents = None
    flags = ["all"] if "defaults" in module.params else []

    # Get running config before processing the commands
    running_before = get_config(module, flags=flags)

    if any((module.params["src"], module.params["lines"])):
        match = module.params["match"]

        commit = not module.check_mode
        candidate = get_candidate(module)
        try:
            response = connection.get_diff(
                mode=mode,
                candidate=candidate,
                running=running_before,
                diff_match=match,
                path=path,
            )
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))

        config_diff = response["config_diff"]
        if config_diff:
            commands = config_diff.split("\n")

            if module.params["before"]:
                commands[:0] = module.params["before"]

            if module.params["after"]:
                commands.extend(module.params["after"])

            result["commands"] = commands
            result["updates"] = commands

            if commit:
                run_commands(module, mode, commands, True)
                result["changed"] = is_changed(mode, commands)


    result["saved"] = False
    if module.params["save_when"] == "always":
        if save_config(module):
            result["saved"] = True
    elif module.params["save_when"] == "modified":
        running_config_before = NetworkConfig(
            contents=running_before,
        )

        # Get running config after processing the commands
        running_after = get_config(module, flags=[])
        running_config_after = NetworkConfig(
            contents=running_after,
        )

        if running_config_before.sha1 != running_config_after.sha1:
            if save_config(module):
                result["saved"] = True
    elif module.params["save_when"] == "changed" and result["changed"]:
        if save_config(module):
            result["saved"] = True
    else:
        pass

    if result.get("changed") and any((module.params["src"], module.params["lines"])):
        msg = (
            "To ensure idempotency and correct diff the input configuration lines should be"
            " similar to how they appear if present in"
            " the running configuration on device"
        )
        if module.params["src"]:
            msg += " including the indentation"
        if "warnings" in result:
            result["warnings"].append(msg)
        else:
            result["warnings"] = msg

        # Add warning for click_cli mode
        # Cases : parent & mode are ignored
        if cmn.is_click_cli_mode(mode):
            if path:
                msg = "'parent' value is ignored for click_cli mode"
                result["warnings"].append(msg)
            if match:
                msg = "'match' value is ignored for click_cli mode"
                result["warnings"].append(msg)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
