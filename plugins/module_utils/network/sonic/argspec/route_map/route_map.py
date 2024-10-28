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
The arg spec for the route_map module
"""


class Route_mapArgs(object):  # pylint: disable=R0903
    """The arg spec for the route_map module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'options': {'route-map': {'elements': 'dict',
                                      'options': {'action': {'choices': ['deny',
                                                                         'permit'],
                                                             'required': True,
                                                             'type': 'str'},
                                                  'call': {'type': 'str'},
                                                  'match': {'options': {'as-path': {'type': 'str'},
                                                                        'community': {'type': 'str'},
                                                                        'community-exact-match': {'type': 'bool'},
                                                                        'extended-community': {'type': 'str'},
                                                                        'interface': {'type': 'str'},
                                                                        'ip': {'options': {'address': {'mutually_exclusive': [['access-list',
                                                                                                                               'access-list-number']],
                                                                                                       'options': {'access-list': {'type': 'str'},
                                                                                                                   'access-list-number': {'type': 'str'},
                                                                                                                   'prefix-length': {'type': 'int'},
                                                                                                                   'prefix-list': {'type': 'str'}},
                                                                                                       'type': 'dict'},
                                                                                           'next-hop': {'mutually_exclusive': [['access-list',
                                                                                                                                'access-list-number']],
                                                                                                        'options': {'access-list': {'type': 'str'},
                                                                                                                    'access-list-number': {'type': 'str'},
                                                                                                                    'address': {'type': 'str'},
                                                                                                                    'prefix-length': {'type': 'int'},
                                                                                                                    'prefix-list': {'type': 'str'},
                                                                                                                    'type': {'choices': ['blackhole'],
                                                                                                                             'type': 'str'}},
                                                                                                        'type': 'dict'}},
                                                                               'type': 'dict'},
                                                                        'ipv6': {'options': {'address': {'options': {'access-list': {'type': 'str'},
                                                                                                                     'prefix-length': {'type': 'int'},
                                                                                                                     'prefix-list': {'type': 'str'}},
                                                                                                         'type': 'dict'},
                                                                                             'next-hop': {'options': {'address': {'type': 'str'},
                                                                                                                      'type': {'choices': ['blackhole'],
                                                                                                                               'type': 'str'}},
                                                                                                          'type': 'dict'}},
                                                                                 'type': 'dict'},
                                                                        'large-community': {'type': 'str'},
                                                                        'large-community-exact-match': {'type': 'bool'},
                                                                        'local-preference': {'type': 'int'},
                                                                        'metric': {'type': 'int'},
                                                                        'origin': {'choices': ['egp',
                                                                                               'igp',
                                                                                               'incomplete'],
                                                                                   'type': 'str'},
                                                                        'peer': {'type': 'str'},
                                                                        'source-instance': {'type': 'int'},
                                                                        'source-protocol': {'choices': ['bgp',
                                                                                                        'connected',
                                                                                                        'kernel',
                                                                                                        'ospf',
                                                                                                        'ospf6',
                                                                                                        'static',
                                                                                                        'table'],
                                                                                            'type': 'str'},
                                                                        'source-vrf': {'type': 'str'},
                                                                        'tag': {'type': 'int'}},
                                                            'required_by': {'community-exact-match': ['community'],
                                                                            'large-community-exact-match': ['large-community']},
                                                            'type': 'dict'},
                                                  'name': {'required': True,
                                                           'type': 'str'},
                                                  'on-match': {'mutually_exclusive': [['goto',
                                                                                       'next']],
                                                               'options': {'goto': {'type': 'int'},
                                                                           'next': {'type': 'bool'}},
                                                               'type': 'dict'},
                                                  'seq': {'required': True,
                                                          'type': 'int'},
                                                  'set': {'options': {'aggregator': {'options': {'asn-number': {'type': 'str'},
                                                                                                 'ip-addr': {'type': 'str'}},
                                                                                     'required_together': [['asn-number',
                                                                                                            'ip-addr']],
                                                                                     'type': 'dict'},
                                                                      'as-path': {'options': {'exclude': {'type': 'str'},
                                                                                              'prepend': {'type': 'str'}},
                                                                                  'type': 'dict'},
                                                                      'atomic-aggregate': {'type': 'bool'},
                                                                      'community-list': {'type': 'str'},
                                                                      'community-list-additive': {'type': 'bool'},
                                                                      'delete-community-list': {'type': 'str'},
                                                                      'delete-large-community-list': {'type': 'str'},
                                                                      'distance': {'type': 'int'},
                                                                      'ext-community': {'options': {'bandwidth': {'type': 'str'},
                                                                                                    'non-transitive': {'type': 'bool'},
                                                                                                    'rt': {'type': 'str'},
                                                                                                    'soo': {'type': 'str'}},
                                                                                        'type': 'dict'},
                                                                      'forwarding-address': {'type': 'str'},
                                                                      'ipv4-next-hop': {'mutually_exclusive': [['peer-address',
                                                                                                                'unchanged']],
                                                                                        'options': {'address': {'type': 'str'},
                                                                                                    'peer-address': {'type': 'bool'},
                                                                                                    'unchanged': {'type': 'bool'}},
                                                                                        'type': 'dict'},
                                                                      'ipv4-vpn-next-hop': {'type': 'str'},
                                                                      'ipv6-next-hop': {'options': {'global-address': {'type': 'str'},
                                                                                                    'local-address': {'type': 'str'},
                                                                                                    'peer-address': {'type': 'bool'},
                                                                                                    'prefer-global': {'type': 'bool'}},
                                                                                        'type': 'dict'},
                                                                      'ipv6-vpn-next-hop': {'type': 'str'},
                                                                      'large-community-list': {'type': 'str'},
                                                                      'large-community-list-additive': {'type': 'bool'},
                                                                      'local-preference': {'type': 'str'},
                                                                      'metric': {'type': 'str'},
                                                                      'metric-type': {'choices': ['type-1',
                                                                                                  'type-2'],
                                                                                      'type': 'str'},
                                                                      'origin': {'choices': ['egp',
                                                                                             'igp',
                                                                                             'incomplete'],
                                                                                 'type': 'str'},
                                                                      'originator-id': {'type': 'str'},
                                                                      'source-address': {'type': 'str'},
                                                                      'table': {'type': 'int'},
                                                                      'tag': {'type': 'int'},
                                                                      'weight': {'type': 'int'}},
                                                          'type': 'dict'}},
                                      'type': 'list'}},
            'type': 'dict'},
 'state': {'choices': ['merged', 'deleted'],
           'default': 'merged',
           'type': 'str'}}  # pylint: disable=C0301
