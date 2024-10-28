#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: command
author: Celestica SONiC Ansible Team (@dharmaraj-gurusamy)
short_description: Run arbitrary commands on a Celestica SONiC device.
description:
- Sends an arbitrary set of commands to a Celestica SONiC node and returns the results read from
  the device.  This module includes an argument that will cause the module to wait
  for a specific condition before returning or timing out if the condition is not
  met.
version_added: 1.0.0
notes:
- Tested against Celestica SONiC 3.0
- Tested against Advanced Celestica SONiC 2.0
- Celestica SONiC version supports C(click_cli) and C(frr_cli) only in mode.
- Advanced Celestica SONiC version supports C(click_cli) and C(sonic_cli) only in mode.
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
  commands:
    description:
    - The commands to send to the remote device.  The resulting output from the command is returned.
      If the I(wait_for) argument is provided, the module is not returned until the condition is
      satisfied or the number of I(retries) has been exceeded.  Commands may be represented either
      as simple strings or as dictionaries as described below.
      Refer to the EXAMPLES section for some common uses.
    required: true
    type: list
    elements: raw
    suboptions:
      command:
        description:
        - The command to send to the remote network device.  The resulting output from
          the command is returned, unless I(sendonly) is set.
        required: true
        type: str
      prompt:
        description:
        - A single regex pattern or a sequence of patterns to evaluate the expected prompt
          from I(command).
        required: false
        type: list
        elements: str
      answer:
        description:
        - The answer to reply with if I(prompt) is matched.  The value can be a single
          answer or a list of answer for multiple prompts.  In case the command execution
          results in multiple prompts the sequence of the prompt and excepted answer should
          be in same order.
        required: false
        type: list
        elements: str
      sendonly:
        description:
        - The boolean value, that when set to true will send I(command) to the device
          but not wait for a result.
        type: bool
        default: false
        required: false
      newline:
        description:
        - The boolean value, that when set to false will send I(answer) to the device
          without a trailing newline.
        type: bool
        default: true
        required: false
      check_all:
        description:
        - By default if any one of the prompts mentioned in C(prompt) option is matched
          it won't check for other prompts.  This boolean flag, that when set to I(True)
          will check for all the prompts mentioned in C(prompt) option in the given order.
          If the option is set to I(True) all the prompts should be received from remote
          host if not it will result in timeout.
        type: bool
        default: false
  wait_for:
    description:
    - Specifies what to evaluate from the output of the command and what conditionals
      to apply.  This argument will cause the task to wait for a particular conditional
      to be true before moving forward.   If the conditional is not true by the configured
      retries, the task fails.  Note - With I(wait_for) the value in C(result['stdout'])
      can be accessed using C(result), that is to access C(result['stdout'][0]) use
      C(result[0]) See EXAMPLES.
    type: list
    elements: str
    aliases:
    - waitfor
  match:
    description:
    - The I(match) argument is used in conjunction with the I(wait_for) argument to
      specify the match policy.  Valid values are C(all) or C(any).  If the value
      is set to C(all) then all conditionals in the I(wait_for) must be satisfied.  If
      the value is set to C(any) then only one of the values must be satisfied.
    type: str
    default: all
    choices:
    - any
    - all
  retries:
    description:
    - Specifies the number of retries a command should be tried before it is considered
      failed.  The command is run on the target device every retry and evaluated against
      the I(wait_for) conditionals.
    default: 10
    type: int
  interval:
    description:
    - Configures the interval in seconds to wait between retries of the command.  If
      the command does not pass the specified conditional, the interval indicates
      how to long to wait before trying the command again.
    default: 1
    type: int
"""

EXAMPLES = r"""
- name: Run show version on remote devices with click_cli mode
  celestica.sonic.command:
    mode: click_cli
    commands: show version

- name: Run show version on remote devices with sonic_cli mode
  celestica.sonic.command:
    mode: sonic_cli
    commands: show version

- name: Run show running-config bgp on remote devices with frr_cli mode
  celestica.sonic.command:
    mode: frr_cli
    commands: show running-config bgp

- name: Run show version and check to see if output contains advanced_celestica_sonic with click_cli mode
  celestica.sonic.command:
    mode: click_cli
    commands: show version
    wait_for: result[0] contains advanced_celestica_sonic

- name: Run show version and check to see if output contains advanced_celestica_sonic with sonic_cli mode
  celestica.sonic.command:
    mode: sonic_cli
    commands: show version
    wait_for: result[0] contains advanced_celestica_sonic

- name: Run show running-config bgp and check to see if output contains 'router bgp' with frr_cli mode
  celestica.sonic.command:
    mode: frr_cli
    commands: show running-config bgp
    wait_for: result[0] contains 'router bgp'

- name: Run multiple commands on remote nodes with click_cli mode
  celestica.sonic.command:
    mode: click_cli
    commands:
      - show feature status
      - show interfaces status

- name: Run multiple commands on remote nodes with sonic_cli mode
  celestica.sonic.command:
    mode: sonic_cli
    commands:
      - show feature status
      - show interface status

- name: Run multiple commands on remote nodes with frr_cli mode
  celestica.sonic.command:
    mode: frr_cli
    commands:
      - show bgp summary
      - show ip route

- name: Run multiple commands and evaluate the output with click_cli mode
  celestica.sonic.command:
    mode: click_cli
    commands:
      - show version
      - show interfaces status
    wait_for:
      - result[0] contains SONiC
      - result[1] contains Ethernet0

- name: Run multiple commands and evaluate the output with sonic_cli mode
  celestica.sonic.command:
    mode: sonic_cli
    commands:
      - show version
      - show interface status
    wait_for:
      - result[0] contains SONiC
      - result[1] contains Ethernet0

- name: Run multiple commands and evaluate the output with frr_cli mode
  celestica.sonic.command:
    mode: frr_cli
    commands:
      - show bgp summary
      - show ip route
    wait_for:
      - result[0] contains 'local ASN number 1'
      - result[1] contains 'directly connected'

- name: Check whether the switch status is ready, with 8 retries
    and 2 second interval between retries
  celestica.sonic.command:
    mode: sonic_cli
    commands: show system status
    wait_for: result[0] contains 'System is ready'
    interval: 2
    retries: 8

- name: Run a command that requires a confirmation. Note that prompt
    takes regexes, and so strings containing characters like brackets
    need to be escaped.
  celestica.sonic.command:
    mode: click_cli
    commands:
      - command: sudo sonic-installer cleanup
        prompt: [continue?]
        answer: y

- name: Run a command that requires a confirmation. Note that prompt
    takes regexes, and so strings containing characters like brackets
    need to be escaped.
  celestica.sonic.command:
    mode: sonic_cli
    commands:
      - command: image remove all
        prompt: [continue?]
        answer: n
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import time

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.parsing import (
    Conditional,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_lines

from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.sonic import (
    run_commands,
    transform_commands,
)


def parse_commands(module, warnings):
    commands = transform_commands(module)

    if module.check_mode:
        for item in list(commands):
            if not item["command"].startswith("show"):
                warnings.append(
                    "Only show commands are supported when using check mode, not "
                    "executing %s" % item["command"],
                )
                commands.remove(item)

    return commands


def main():
    """entry point for module execution"""
    argument_spec = dict(
        mode=dict(type="str", required=True, choices=["click_cli", "frr_cli", "sonic_cli"]),
        commands=dict(type="list", required=True, elements="raw"),
        wait_for=dict(type="list", aliases=["waitfor"], elements="str"),
        match=dict(default="all", choices=["all", "any"]),
        retries=dict(default=10, type="int"),
        interval=dict(default=1, type="int"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    warnings = list()
    result = {"changed": False, "warnings": warnings}
    commands = parse_commands(module, warnings)
    wait_for = module.params["wait_for"] or list()

    try:
        conditionals = [Conditional(c) for c in wait_for]
    except AttributeError as exc:
        module.fail_json(msg=to_text(exc))

    mode = module.params["mode"]
    retries = module.params["retries"]
    interval = module.params["interval"]
    match = module.params["match"]

    while retries > 0:
        responses = run_commands(module, mode, commands)

        for item in list(conditionals):
            if item(responses):
                if match == "any":
                    conditionals = list()
                    break
                conditionals.remove(item)

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = "One or more conditional statements are not satisfied"
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update(
        {"stdout": responses, "stdout_lines": list(to_lines(responses))},
    )

    module.exit_json(**result)


if __name__ == "__main__":
    main()
