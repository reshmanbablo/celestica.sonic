#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# utils
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.six import iteritems
from ansible.utils.display import Display

display = Display()

def list_dict_diff(base, comparable):
    # Throw error when base is not list
    if not isinstance(base, list):
        for item in base:
            if not isinstance(item, dict):
                raise AssertionError("`base` must be of type <list(dict)>")
    # Throw error when comparable is not list
    if not isinstance(comparable, list):
        for item in comparable:
            if not isinstance(item, dict):
                raise AssertionError("`comparable` must be of type <list(dict)>")

    # Iterate over base list
    for base_val in base:
        base_val_keys = base_val.keys()
        #display.vvv("base_val: %s" % base_val)
    for comp_val in comparable:
        comp_val_keys = comp_val.keys()
        #display.vvv("comp_val: %s" % comp_val)

def sort_list(val):
    if isinstance(val, list):
        if isinstance(val[0], dict):
            sorted_keys = [tuple(sorted(dict_.keys())) for dict_ in val]
            #display.vvv("sort_list(), sorted_keys: %s" % (sorted_keys));
            # All keys should be identical
            if len(set(sorted_keys)) != 1:
                raise ValueError("dictionaries do not match")

            result = sorted(
                val, key=lambda d: tuple(d[k] for k in sorted_keys[0])
            )
            #display.vvv("sort_list(), result: %s" % (result));
            return result
        return sorted(val)
    return val

def dict_diff(base, comparable):
    """Generate a dict object of differences

    This function will compare two dict objects and return the difference
    between them as a dict object.  For scalar values, the key will reflect
    the updated value.  If the key does not exist in `comparable`, then then no
    key will be returned.  For lists, the value in comparable will wholly replace
    the value in base for the key.  For dicts, the returned value will only
    return keys that are different.

    :param base: dict object to base the diff on
    :param comparable: dict object to compare against base

    :returns: new dict object with differences
    """
    if not isinstance(base, dict):
        raise AssertionError("`base` must be of type <dict>")
    if not isinstance(comparable, dict):
        if comparable is None:
            comparable = dict()
        else:
            raise AssertionError("`comparable` must be of type <dict>")

    updates = dict()

    for key, value in iteritems(base):
        #display.vvv("dict_diff(), Processing key: %s, value: %s" % (key, value));
        if isinstance(value, dict):
            item = comparable.get(key)
            if item is not None:
                sub_diff = dict_diff(value, comparable[key])
                if sub_diff:
                    updates[key] = sub_diff
        else:
            comparable_value = comparable.get(key)
            #display.vvv("dict_diff(), comparable value: %s" % (comparable_value));
            if comparable_value is not None:
                if isinstance(value, list) and isinstance(comparable_value, list):
                    list_dict_diff(value, comparable_value)
                if sort_list((value)) != sort_list(str(comparable_value)):
                    updates[key] = comparable_value

    for key in set(comparable.keys()).difference(base.keys()):
        updates[key] = comparable.get(key)

    return updates

