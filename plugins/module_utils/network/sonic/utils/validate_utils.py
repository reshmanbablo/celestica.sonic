#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# validate_utils
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from enum import StrEnum
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils import (
    Constant,
    log,
    log_vars
)

import re

# Globals
class ValueCheckConstant(StrEnum):
    NEGATE_CHAR = '!'

# Validate method exposed to consumers
def validate(method, val):
    result = None
    methodName = None
    negateResult = False
    global validate_methods

    if method.startswith(ValueCheckConstant.NEGATE_CHAR):
        methodName = method.split(ValueCheckConstant.NEGATE_CHAR)[1]
        negateResult = True
    else:
        methodName = method

    if methodName in validate_methods:
        func = validate_methods.get(methodName)
        result = func(val)

    if negateResult:
        result = not result

    return result

# Validate whether input is valid MAC address format or not
def isMACAddress(inVal):
    result = False

    if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", inVal.lower()):
        result = True

    # log_vars(inVal=inVal, result=result)
    return result

# Validate whether input is integer or not
def isInterface(inVal):
    result = False

    intfPatterns = ['Ethernet', 'PortChannal', 'Vlan', 'Loopback', 'Management', 'Tunnel', 'vxlan']

    # Return immediately when input is None
    if not inVal: return result

    for pattern in intfPatterns:
        if inVal.startswith(pattern):
            result = True
            break

    # log_vars(inVal=inVal, result=result)
    return result

# Validate whether input is integer or not
def isInt(inVal):
    result = False

    # Return immediately when input is None
    if not inVal: return result

    try:
        tmp = int(inVal)
        result = True
    except ValueError:
        pass

    # log_vars(inVal=inVal, result=result)
    return result

# Validate whether input is bool or not
def isBool(inVal):
    result = False

    # Return immediately when input is None
    if not inVal: return result

    ANSIBLE_BOOL_VALS = ["true", "false"]
    if inVal.lower() in ANSIBLE_BOOL_VALS:
        result = True

    log_vars(inVal=inVal, result=result)
    return result


# Methods dict
# All validate methods are expected to return True / False only
# Negate of validation (using !) is allowed
validate_methods = {
    'bool': isBool,
    'integer': isInt,
    'interface': isInterface,
    'macaddress': isMACAddress,
}

