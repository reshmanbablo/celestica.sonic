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
The arg spec for the bgp_ext_community module
"""


class Bgp_ext_communityArgs(object):  # pylint: disable=R0903
    """The arg spec for the bgp_ext_community module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'options': {'ext-community-list': {'elements': 'dict',
                                               'options': {'id': {'required': True,
                                                                  'type': 'str'},
                                                           'sequence-numbers': {'elements': 'dict',
                                                                                'options': {'action': {'choices': ['deny',
                                                                                                                   'permit'],
                                                                                                       'required': True,
                                                                                                       'type': 'str'},
                                                                                            'number': {'required': True,
                                                                                                       'type': 'str'},
                                                                                            'seq': {'required': True,
                                                                                                    'type': 'int'}},
                                                                                'type': 'list'},
                                                           'type': {'choices': ['expanded',
                                                                                'standard'],
                                                                    'type': 'str'}},
                                               'type': 'list'}},
            'type': 'dict'},
 'state': {'choices': ['merged', 'deleted'],
           'default': 'merged',
           'type': 'str'}}  # pylint: disable=C0301
