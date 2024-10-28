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
The arg spec for the bgp module
"""


class BgpArgs(object):  # pylint: disable=R0903
    """The arg spec for the bgp module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'options': {'bgp': {'elements': 'dict',
                                'mutually_exclusive': [['vrf', 'view']],
                                'options': {'always-compare-med': {'type': 'bool'},
                                            'asn': {'required': True,
                                                    'type': 'str'},
                                            'bestpath': {'options': {'as-path': {'options': {'confed': {'type': 'bool'},
                                                                                             'multipath-relax': {'type': 'bool'},
                                                                                             'multipath-relax-as-set': {'type': 'bool'}},
                                                                                 'required_by': {'multipath-relax-as-set': ['multipath-relax']},
                                                                                 'type': 'dict'},
                                                                     'bandwidth': {'choices': ['default-weight-for-missing',
                                                                                               'ignore',
                                                                                               'skip-missing'],
                                                                                   'type': 'str'},
                                                                     'compare-routerid': {'type': 'bool'},
                                                                     'med': {'options': {'confed': {'type': 'bool'},
                                                                                         'missing-as-worst': {'type': 'bool'}},
                                                                             'type': 'dict'},
                                                                     'peer-type-multipath-relax': {'type': 'bool'}},
                                                         'required_by': {'med-confed-missing-as-worst': ['med-confed']},
                                                         'type': 'dict'},
                                            'client-to-client-reflection': {'type': 'bool'},
                                            'cluster-id': {'type': 'str'},
                                            'coalesce-time': {'type': 'int'},
                                            'confederation': {'options': {'identifier': {'type': 'int'},
                                                                          'peers': {'type': 'int'}},
                                                              'type': 'dict'},
                                            'default': {'options': {'ipv4-unicast': {'type': 'bool'},
                                                                    'local-preference': {'type': 'int'},
                                                                    'shutdown': {'type': 'bool'}},
                                                        'type': 'dict'},
                                            'deterministic-med': {'type': 'bool'},
                                            'disable-ebgp-connected-route-check': {'type': 'bool'},
                                            'ebgp-requires-policy': {'type': 'bool'},
                                            'fast-external-failover': {'type': 'bool'},
                                            'graceful-restart': {'options': {'disable-eor': {'type': 'bool'},
                                                                             'preserve-fw-state': {'type': 'bool'},
                                                                             'restart-time': {'type': 'int'},
                                                                             'rib-stale-time': {'type': 'int'},
                                                                             'select-defer-time': {'type': 'int'},
                                                                             'stalepath-time': {'type': 'int'}},
                                                                 'type': 'dict'},
                                            'graceful-restart-disable': {'type': 'bool'},
                                            'graceful-shutdown': {'type': 'bool'},
                                            'listen': {'options': {'limit': {'type': 'int'},
                                                                   'range': {'elements': 'dict',
                                                                             'options': {'address': {'type': 'str'},
                                                                                         'peer-group': {'type': 'str'}},
                                                                             'type': 'list'}},
                                                       'type': 'dict'},
                                            'log-neighbor-changes': {'type': 'bool'},
                                            'max-med': {'options': {'administrative': {'type': 'bool'},
                                                                    'administrative-max': {'type': 'int'},
                                                                    'on-startup': {'options': {'startup-max': {'type': 'int'},
                                                                                               'startup-period': {'type': 'int'}},
                                                                                   'type': 'dict'}},
                                                        'type': 'dict'},
                                            'network-import-check': {'type': 'bool'},
                                            'reject-as-sets': {'type': 'bool'},
                                            'route-map-delay-timer': {'type': 'int'},
                                            'router-id': {'type': 'str'},
                                            'router-reflector-allow-outbound-policy': {'type': 'bool'},
                                            'session-dscp': {'type': 'int'},
                                            'shutdown': {'type': 'bool'},
                                            'shutdown-message': {'type': 'str'},
                                            'timers': {'options': {'hold': {'type': 'int'},
                                                                   'keep-alive': {'type': 'int'}},
                                                       'required_together': [['keep-alive',
                                                                              'hold']],
                                                       'type': 'dict'},
                                            'update-delay-establish-wait': {'type': 'int'},
                                            'update-delay-max-delay': {'type': 'int'},
                                            'view': {'type': 'str'},
                                            'vrf': {'type': 'str'}},
                                'required_together': [['update-delay-max-delay',
                                                       'update-delay-establish-wait']],
                                'type': 'list'}},
            'type': 'dict'},
 'state': {'choices': ['merged', 'deleted'],
           'default': 'merged',
           'type': 'str'}}  # pylint: disable=C0301
