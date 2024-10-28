#
# Copyright (c) 2024 Celestica Inc.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.terminal import TerminalBase

DOCUMENTATION = """
short_description: Terminal plugin module for SONiC CLI based modules
version_added: 1.0.0
"""


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:#) ?$"),
        re.compile(br"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$"),
        re.compile(br"\$ ?$")
    ]

    terminal_stderr_re = [
        re.compile(br"% ?Error"),
        re.compile(br" ?Error:"),
        re.compile(br" ?Usage:"),
        re.compile(br"% ?Bad secret"),
        re.compile(br"Syntax error:"),
        re.compile(br"invalid input", re.I),
        re.compile(br"(?:incomplete|ambiguous|unknown) command", re.I),
        re.compile(br"connection timed out", re.I),
        re.compile(br"[^\r\n]+ not found", re.I),
        re.compile(br"'[^']' +returned error code: ?\d+"),
        re.compile(br"Root privileges are required for this operation", re.I),
    ]

    def on_open_shell(self):
        return

    def on_become(self, passwd=None):
        return

    def on_unbecome(self):
        return
