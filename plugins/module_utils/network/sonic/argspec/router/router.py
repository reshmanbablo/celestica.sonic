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
The arg spec for the router module
"""


class RouterArgs(object):  # pylint: disable=R0903
    """The arg spec for the router module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'options': {'ipv4': {'options': {'next-hop-track': {'elements': 'dict',
                                                                'options': {'protocol': {'choices': ['bgp',
                                                                                                     'connected',
                                                                                                     'kernel',
                                                                                                     'ospf',
                                                                                                     'resolve-via-default',
                                                                                                     'static',
                                                                                                     'table'],
                                                                                         'required': True,
                                                                                         'type': 'str'},
                                                                            'route-map': {'type': 'str'}},
                                                                'type': 'list'},
                                             'protocol': {'elements': 'dict',
                                                          'options': {'name': {'choices': ['any',
                                                                                           'bgp',
                                                                                           'connected',
                                                                                           'kernel',
                                                                                           'ospf',
                                                                                           'static',
                                                                                           'table'],
                                                                               'required': True,
                                                                               'type': 'str'},
                                                                      'route-map': {'type': 'str'}},
                                                          'type': 'list'},
                                             'route': {'elements': 'dict',
                                                       'options': {'destination': {'required': True,
                                                                                   'type': 'str'},
                                                                   'next-hops': {'elements': 'dict',
                                                                                 'options': {'distance': {'type': 'int'},
                                                                                             'interface': {'type': 'str'},
                                                                                             'next-hop': {'required': True,
                                                                                                          'type': 'str'},
                                                                                             'onlink': {'type': 'bool'},
                                                                                             'tag': {'type': 'int'}},
                                                                                 'required_by': {'onlink': ['interface']},
                                                                                 'type': 'list'}},
                                                       'type': 'list'},
                                             'router-id': {'type': 'str'}},
                                 'type': 'dict'},
                        'ipv6': {'options': {'next-hop-track': {'elements': 'dict',
                                                                'options': {'protocol': {'choices': ['bgp',
                                                                                                     'connected',
                                                                                                     'kernel',
                                                                                                     'ospf',
                                                                                                     'resolve-via-default',
                                                                                                     'static',
                                                                                                     'table'],
                                                                                         'required': True,
                                                                                         'type': 'str'},
                                                                            'route-map': {'type': 'str'}},
                                                                'type': 'list'},
                                             'protocol': {'elements': 'dict',
                                                          'options': {'name': {'choices': ['any',
                                                                                           'bgp',
                                                                                           'connected',
                                                                                           'kernel',
                                                                                           'ospf6',
                                                                                           'static',
                                                                                           'table'],
                                                                               'required': True,
                                                                               'type': 'str'},
                                                                      'route-map': {'type': 'str'}},
                                                          'type': 'list'},
                                             'route': {'elements': 'dict',
                                                       'options': {'destination': {'required': True,
                                                                                   'type': 'str'},
                                                                   'next-hops': {'elements': 'dict',
                                                                                 'options': {'distance': {'type': 'int'},
                                                                                             'interface': {'type': 'str'},
                                                                                             'next-hop': {'required': True,
                                                                                                          'type': 'str'},
                                                                                             'onlink': {'type': 'bool'},
                                                                                             'tag': {'type': 'int'}},
                                                                                 'required_by': {'onlink': ['interface']},
                                                                                 'type': 'list'}},
                                                       'type': 'list'},
                                             'router-id': {'type': 'str'}},
                                 'type': 'dict'}},
            'type': 'dict'},
 'state': {'choices': ['merged', 'deleted'],
           'default': 'merged',
           'type': 'str'}}  # pylint: disable=C0301
