# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import re

from ansible.module_utils._text import to_text
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    to_list,
    ComplexList
)
from ansible.module_utils.connection import Connection, ConnectionError
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import NetworkConfig, ConfigLine
from ansible.utils.display import Display

_DEVICE_CONNECTION = None

display = Display()

def get_connection(module):
    global _DEVICE_CONNECTION
    if not _DEVICE_CONNECTION:
        connection_proxy = Connection(module._socket_path)
        cap = json.loads(connection_proxy.get_capabilities())
        if cap["network_api"] == "cliconf":
            conn = Cli(module)
        else:
            module.fail_json(msg="Invalid connection type %s" % network_api)
        _DEVICE_CONNECTION = conn
    return _DEVICE_CONNECTION

def to_command(module, commands):
    transform = ComplexList(
        dict(
            command=dict(key=True),
            prompt=dict(type="list"),
            answer=dict(type="list"),
            newline=dict(type="bool", default=True),
            sendonly=dict(type="bool", default=False),
            check_all=dict(type="bool", default=False),
        ),
        module,
    )

    return transform(to_list(commands))


def transform_commands(module):
    transform = ComplexList(
        dict(
            command=dict(key=True),
            output=dict(),
            prompt=dict(type="list"),
            answer=dict(type="list"),
            newline=dict(type="bool", default=True),
            sendonly=dict(type="bool", default=False),
            check_all=dict(type="bool", default=False),
        ),
        module,
    )

    return transform(module.params["commands"])


def get_config(module, flags=None):
    mode = module.params['mode']

    connection = get_connection(module)
    try:
        out = connection.get_config(flags=flags)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))
    cfg = to_text(out, errors="surrogate_then_replace").strip()
    return cfg


def run_commands(module, mode=None, commands=None, config=False, check_rc=True):
    connection = get_connection(module)
    try:
        return connection.run_commands(mode, commands, config, check_rc)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def edit_config(module, commands, skip_code=None):
    return run_commands(module, commands)

def is_config_module(name):
    result = True if name.endswith('.config') else False
    return result

class Cli:
    def __init__(self, module):
        self._module = module
        self._connection = None
        self._config_module = is_config_module(module._name)

    def _get_connection(self):
        if self._connection:
            return self._connection
        self._connection = Connection(self._module._socket_path)

        return self._connection

    def load_config(self, config, return_error=False, opts=None, replace=None):
        """Sends configuration commands to the remote device"""
        response = []
        try:
            response = self.run_commands(config, check_rc=True)
        except ConnectionError as exc:
            self._module.fail_json(
                msg=to_text(exc, errors="surrogate_then_replace"),
            )

        return response

    def get_config(self, source='running', flags=None, format='text'):
        """Retrieves the current config from the device or cache"""

        mode = self._module.params['mode']

        conn = self._get_connection()
        try:
            out = conn.get_config(mode,
                                  config_module=self._config_module, 
                                  source=source, 
                                  flags=flags, 
                                  format=format)
        except ConnectionError as exc:
            self._module.fail_json(
                msg=to_text(exc, errors="surrogate_then_replace"),
            )

        cfg = to_text(out, errors="surrogate_then_replace").strip()
        return cfg

    def get_diff(
        self,
        mode=None,
        candidate=None,
        running=None,
        diff_match="line",
        path=None,
    ):
        """Generates the diff between and candidate and running config"""
        mode = self._module.params["mode"]
        connection = self._get_connection()
        try:
            response = connection.get_diff(
                mode=mode,
                candidate=candidate,
                running=running,
                diff_match=diff_match,
                path=path,
            )
        except ConnectionError as exc:
            self._module.fail_json(
                msg=to_text(exc, errors="surrogate_then_replace"),
            )
        return response

    def edit_config(self, commands, check_rc=True):
        """Run list of commands on remote device and return results"""
        try:
            response = self.run_commands(
                commands=commands,
                check_rc=check_rc,
            )
        except ConnectionError as exc:
            self._module.fail_json(
                msg=to_text(exc, errors="surrogate_then_replace"),
            )
        return response

    def run_commands(self, mode=None, commands=None, config=False, check_rc=True):
        """Run list of commands on remote device and return results"""
        # Read mode from module params if not passed
        # Command and Config modules have mode as parameter
        # Network module pass this internally
        if not mode:
            mode = self._module.params["mode"]
        connection = self._get_connection()
        try:
            response = connection.run_commands(
                mode=mode,
                commands=commands,
                config=config,
                check_rc=check_rc,
            )
        except ConnectionError as exc:
            self._module.fail_json(
                msg=to_text(exc, errors="surrogate_then_replace"),
            )
        return response

    def get_capabilities(self):
        """Returns platform info of the remove device"""
        if hasattr(self._module, "_capabilities"):
            return self._module._capabilities

        connection = self._get_connection()
        try:
            capabilities = connection.get_capabilities()
        except ConnectionError as exc:
            self._module.fail_json(
                msg=to_text(exc, errors="surrogate_then_replace"),
            )
        self._module._capabilities = json.loads(capabilities)
        return self._module._capabilities

