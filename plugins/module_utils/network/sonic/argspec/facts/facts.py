#
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
The argument spec for the facts module.
"""

class FactsArgs(object):  # pylint: disable=R0903
    """ The argument spec for the sonic facts module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list'),
        'gather_network_resources': dict(type='list'),
        'available_network_resources': dict(default='false',
                                         type='bool'),
    }
