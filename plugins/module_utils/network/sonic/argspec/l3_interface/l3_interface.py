#
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The arg spec for the l3_interface module
"""


class L3_interfaceArgs(object):  # pylint: disable=R0903
    """The arg spec for the l3_interface module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'options': {'interface': {'elements': 'dict',
                                      'options': {'ipv4': {'options': {'addresses': {'elements': 'dict',
                                                                                     'options': {'address': {'required': True,
                                                                                                             'type': 'str'}},
                                                                                     'type': 'list'}},
                                                           'type': 'dict'},
                                                  'ipv6': {'options': {'addresses': {'elements': 'dict',
                                                                                     'options': {'address': {'required': True,
                                                                                                             'type': 'str'}},
                                                                                     'type': 'list'},
                                                                       'link-local-only': {'type': 'bool'}},
                                                           'type': 'dict'},
                                                  'name': {'required': True,
                                                           'type': 'str'}},
                                      'type': 'list'}},
            'type': 'dict'},
 'state': {'choices': ['merged', 'deleted'],
           'default': 'merged',
           'type': 'str'}}  # pylint: disable=C0301
