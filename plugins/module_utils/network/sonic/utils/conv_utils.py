#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# conv_utils
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from enum import IntEnum
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.utils.common_utils import (
    Constant,
    log,
    log_vars
)

# Globals
class Constant(IntEnum):
    CONFIG_TO_FACTS = 1
    FACTS_TO_CONFIG = 2

# Translate method exposed to consumers
def translate(method, val, xType):
    result = None
    global translate_methods
    if method in translate_methods:
        func = translate_methods.get(method)
        result = func(val, xType)

    return result

# bool (True / False) to (enable / disable) conversion
def bool_to_enable_disable(inVal, xType):
    result = None
    data = None

    if inVal is None:
        return result

    if xType is Constant.CONFIG_TO_FACTS:
        data = {'enable': True, 'disable': False}
    elif xType is Constant.FACTS_TO_CONFIG:
        data = {True: 'enable', False: 'disable'}
    else:
        log(f"Unknown translation type {xType}")

    if data:
        if inVal in data:
            result = data[inVal]

    # log_vars(inVal=inVal, xType=xType, data=data, result=result)
    return result

# bool (True / False) to (enabled / disabled) conversion
def bool_to_enabled_disabled(inVal, xType):
    result = None
    data = None

    if inVal is None:
        return result

    if xType is Constant.CONFIG_TO_FACTS:
        data = {'enabled': True, 'disabled': False}
    elif xType is Constant.FACTS_TO_CONFIG:
        data = {True: 'enabled', False: 'disabled'}
    else:
        log(f"Unknown translation type {xType}")

    if data:
        if inVal in data:
            result = data[inVal]

    # log_vars(inVal=inVal, xType=xType, data=data, result=result)
    return result

# bool (True / False) to (on / off) conversion
def bool_to_on_off(inVal, xType):
    result = None
    data = None

    if inVal is None:
        return result

    if xType is Constant.CONFIG_TO_FACTS:
        data = {'on': True, 'off': False}
    elif xType is Constant.FACTS_TO_CONFIG:
        data = {True: 'on', False: 'off'}
    else:
        log(f"Unknown translation type {xType}")

    if data:
        if inVal in data:
            result = data[inVal]

    # log_vars(inVal=inVal, xType=xType, data=data, result=result)
    return result

# Translate case (lower case in facts to upper case in config & vice versa)
def lower_to_upper(inVal, xType):
    result = None

    if xType is Constant.CONFIG_TO_FACTS:
        result = inVal.lower()
    elif xType is Constant.FACTS_TO_CONFIG:
        result = inVal.upper()
    else:
        log(f"Unknown translation type {xType}")

    # log_vars(inVal=inVal, xType=xType, result=result)
    return result

# Translate snmp access values
def translate_snmp_access(inVal, xType):
    result = None
    data = None

    if xType is Constant.CONFIG_TO_FACTS:
        data = {'RO': 'read-only', 'RW': 'read-write'}
    elif xType is Constant.FACTS_TO_CONFIG:
        data = {'read-only': 'RO', 'read-write': 'RW'}
    else:
        log(f"Unknown translation type {xType}")

    if data:
        if inVal in data:
            result = data[inVal]

    # log_vars(inVal=inVal, xType=xType, data=data, result=result)
    return result

# Translate QoS ECN values
def translate_qos_ecn(inVal, xType):
    result = None
    data = None

    if xType is Constant.CONFIG_TO_FACTS:
        data = {'ecn_green': 'green', 'ecn_yellow': 'yellow', 'ecn_red': 'red', 'ecn_green_yellow': 'green-yellow', 'ecn_green_red': 'green-red', 'ecn_yellow_red': 'yellow-red', 'ecn_all': 'all'}
    elif xType is Constant.FACTS_TO_CONFIG:
        data = {'green': 'ecn_green', 'yellow': 'ecn_yellow', 'red': 'ecn_red', 'green-yellow': 'ecn_green_yellow', 'green-red': 'ecn_green_red', 'yellow-red': 'ecn_yellow_red', 'all': 'ecn_all'}
    else:
        log(f"Unknown translation type {xType}")

    if data:
        if inVal in data:
            result = data[inVal]

    # log_vars(inVal=inVal, xType=xType, data=data, result=result)
    return result

# Methods dict
translate_methods = {
    'bool_to_enable_disable': bool_to_enable_disable,
    'bool_to_enabled_disabled': bool_to_enabled_disabled,
    'bool_to_on_off': bool_to_on_off,
    'lower_to_upper': lower_to_upper,
    'translate_snmp_access': translate_snmp_access,
    'translate_qos_ecn': translate_qos_ecn,
}

