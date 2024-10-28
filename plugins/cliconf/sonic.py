#
# Copyright (c) 2024 Celestica Inc.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
name: sonic
short_description: Use sonic cliconf to run command on Celestica SONiC platform
description:
  - This plugin provides abstraction apis for executing CLI commands
    in Celestica SONiC network devices.
"""

import re
import json

from itertools import chain

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import (
    NetworkConfig,
    dumps,
)
from ansible.plugins.cliconf import CliconfBase, enable_mode
import ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils as cmn
from ansible.utils.display import Display

_command_mode_list_g_ = ['click_cli', 'frr_cli', 'sonic_cli']
_show_cmds_with_sudo_access_g_ = ['show system-health']
display = Display()

# Common utilities
def is_click_prompt(prompt):
    if prompt and prompt.endswith(b'$ '):
        return True
    else:
        return False

# Validate the command mode
def validate_command_mode(mode):
    global _command_mode_list_g_
    if mode in _command_mode_list_g_:
        return True
    else:
        return False

def is_sudo_access_required(cmd):
    global _show_cmds_with_sudo_access_g_
    result = False

    for tmp in _show_cmds_with_sudo_access_g_:
        if tmp in cmd:
            result = True
            break
        else:
            result = False

    if not result and not cmd.startswith('show '):
        result = True

    return result

def prefix_sudo(mode, cmd_in):
    result = cmd_in
    if cmn.is_click_cli_mode(mode) and \
       is_sudo_access_required(cmd_in) and \
       not cmd_in.startswith('sudo '):
           result = 'sudo ' + cmd_in
    return result


# Cliconf plugin
class Cliconf(CliconfBase):

    def __init__(self, *args, **kwargs):
        super(Cliconf, self).__init__(*args, **kwargs)

    def get_device_info(self):
        result = {}

        result['network_os'] = 'sonic'
        reply = self.get('show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'SONiC Software Version(\S+)', data)
        if match:
            result['network_os_version'] = match.group(1)

        return result

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)

    def get_device_operations(self):
        return {
            "supports_commit": False,
            "supports_rollback": False,
            "supports_defaults": True,
            "supports_onbox_diff": False,
            "supports_commit_comment": False,
            "supports_multiline_delimiter": False,
            "supports_diff_match": True,
            "supports_diff_ignore_lines": True,
            "supports_generate_diff": True,
            "supports_replace": True,
        }

    def get_option_values(self):
        return {
            "format": ["text", "json"],
            "output": ["text", "json"],
            "diff_match": ["line", "strict", "exact", "none"],
        }

    def _get_command_with_output(self, mode, command, output):
        options_values = self.get_option_values()
        if output not in options_values["output"]:
            raise ValueError(
                "'output' value %s is invalid. Valid values are %s"
                % (output, ",".join(options_values["output"])),
            )

        if output == "json":
            if cmn.is_click_cli_mode(mode):
                raise ValueError(
                    "'output' value %s is not supported for mode %s"
                    % (output, mode),
                )
            elif cmn.is_frr_cli_mode(mode):
                if not command.endswith(" json"):
                    cmd = "%s json" % command
            elif cmn.is_sonic_cli_mode(mode):
                if not command.endswith("| display-json"):
                    cmd = "%s | display-json" % command
            else:
                cmd = command
        else:
            cmd = command
        return cmd

    def get_diff(
        self,
        mode=None,
        candidate=None,
        running=None,
        diff_match="line",
        path=None,
    ):
        diff = {}
        device_operations = self.get_device_operations()
        option_values = self.get_option_values()

        if mode is None:
            raise ValueError("'mode' value is required")

        if candidate is None and device_operations["supports_generate_diff"]:
            raise ValueError("candidate configuration is required to generate diff")

        if diff_match not in option_values["diff_match"]:
            raise ValueError(
                "'match' value %s in invalid, valid values are %s"
                % (diff_match, ", ".join(option_values["diff_match"])),
            )

        # prepare candidate configuration
        candidate_obj = NetworkConfig(indent=2)
        candidate_obj.load(candidate)

        if cmn.is_click_cli_mode(mode):
            configdiffobjs = candidate_obj.items
            diff["config_diff"] = dumps(configdiffobjs, "commands") if configdiffobjs else ""
        elif cmn.is_frr_cli_mode(mode) or cmn.is_sonic_cli_mode(mode):
            if running and diff_match != "none":
                # running configuration
                running_obj = NetworkConfig(indent=2, contents=running)
                configdiffobjs = candidate_obj.difference(
                    running_obj,
                    path=path,
                    match=diff_match,
                )

            else:
                configdiffobjs = candidate_obj.items
            diff["config_diff"] = dumps(configdiffobjs, "commands") if configdiffobjs else ""

        return diff

    def get_config(self, mode=None,
                   source='running', config_module=False,
                   flags=None, format='text'):
        if mode is None:
            raise ValueError("'mode' value is required")

        if source not in ('running', 'startup'):
            return self.invalid_params("Invalid configuration source '%s'" % source)
        cmd = cmn.form_get_config_command(mode, source, config_module)

        if not cmd:
            return self.invalid_params("Failed to form get_config request")

        return self.run_commands(mode, commands=cmd)

    def edit_config(self, commands, check_rc=True):
        for cmd in to_list(commands):
            display.vvv("Executing Command : %s" % (cmd))
            self.send_command(to_bytes(cmd))

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def run_commands(self, mode=None, commands=None, config=True, check_rc=True):
        if mode is None:
            raise ValueError("'mode' value is required")

        if commands is None:
            raise ValueError("'commands' value is required")

        if not validate_command_mode(mode):
            raise ValueError("Invalid mode : %s" % (mode))

        # Setup the command mode
        self.setup_command_mode(mode, config)

        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, Mapping):
                cmd = {"command": cmd}

            # Prefix 'sudo ' for commands that requires root privilege
            tmp_cmd = cmd.pop("command", None)
            tmp_cmd = prefix_sudo(mode, tmp_cmd)
            cmd['command'] = tmp_cmd

            output = cmd.pop("output", None)
            if output:
                cmd["command"] = self._get_command_with_output(mode, cmd["command"], output)

            display.vvv("Executing Command : %s" % (cmd))
            try:
                out = self.send_command(**cmd)
            except AnsibleConnectionFailure as e:
                # Call clear_command_mode before raising the exception
                self.clear_command_mode()
                if check_rc is True:
                    raise
                out = getattr(e, "err", e)

            if out:
                try:
                    out = to_text(out, errors="surrogate_or_strict").strip()
                except UnicodeError:
                    # Call clear_command_mode before raising the exception
                    self.clear_command_mode()
                    raise ConnectionError(
                        message="Failed to decode output from %s: %s" % (cmd, to_text(out)),
                    )

                try:
                    out = json.loads(out)
                except ValueError:
                    pass

                responses.append(out)

        # Exit from the command mode
        self.clear_command_mode()

        return responses

    def get_command_mode(self):
        return self._command_mode

    def setup_command_mode(self, mode, config_module):
        cmd = None
        page_cmd = None
        config_mode_cmd = None
        self._command_mode = mode

        prompt = self._connection.get_prompt()

        if not is_click_prompt(prompt):
            raise ConnectionError("Terminal is not in Click CLI prompt, current prompt : '%s'" % (prompt))

        if cmn.is_click_cli_mode(mode):
            pass
        elif cmn.is_frr_cli_mode(mode):
            cmd = b'vtysh'
            page_cmd = b'terminal length 0'
            if config_module:
                config_mode_cmd = 'configure terminal'
        elif cmn.is_sonic_cli_mode(mode):
            cmd = b'sonic-cli'
            page_cmd = b'terminal length 0'
            if config_module:
                config_mode_cmd = 'configure terminal'
        else:
            raise ConnectionError("Invalid command mode : '%s'" % (mode))

        if cmd:
            self.send_command(cmd)
        if page_cmd:
            self.send_command(page_cmd)
        if config_mode_cmd:
            self.send_command(config_mode_cmd)

        return

    def clear_command_mode(self):
        result = True
        mode = self._command_mode

        prompt = self._connection.get_prompt()

        if cmn.is_click_cli_mode(mode):
            pass
        elif cmn.is_frr_cli_mode(mode):
            self.send_command(b'end')
            self.send_command(b'exit')
        elif cmn.is_sonic_cli_mode(mode):
            if b'conf' in prompt:
                self.send_command(b'end')
            self.send_command(b'exit')
        else:
            raise ConnectionError("Invalid command mode : '%s'" % (mode))

        self._command_mode = None

        # Ensure whether terminal is restored to Click prompt
        prompt = self._connection.get_prompt()
        if not is_click_prompt(prompt):
            raise ConnectionError("Terminal is not restored to Click CLI prompt, current prompt : '%s'" % (prompt))

        return result
