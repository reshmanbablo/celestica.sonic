#
# -*- coding: utf-8 -*-
# Copyright 2024 Celestica Inc. All Rights Reserved.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The facts class for celestica.sonic
this file validates each subset of facts and selectively
calls the appropriate facts gathering function
"""

from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.argspec.facts.facts import FactsArgs
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.facts.facts import (
    FactsBase,
)
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.radius.radius import RadiusFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.ntp.ntp import NtpFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.interface.interface import InterfaceFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.vlan.vlan import VlanFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.snmp.snmp import SnmpFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.tacacs.tacacs import TacacsFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.l2_interface.l2_interface import L2_interfaceFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.l3_interface.l3_interface import L3_interfaceFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.mclag.mclag import MclagFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.sag.sag import SagFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.vrf.vrf import VrfFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.portchannel.portchannel import PortchannelFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.vxlan.vxlan import VxlanFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.router.router import RouterFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.loopback.loopback import LoopbackFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.prefix_list.prefix_list import Prefix_listFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.tunnel.tunnel import TunnelFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.route_map.route_map import Route_mapFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.bgp_af.bgp_af import Bgp_afFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.bgp_af_neighbor.bgp_af_neighbor import Bgp_af_neighborFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.bgp.bgp import BgpFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.bgp_neighbor.bgp_neighbor import Bgp_neighborFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.vrf_router.vrf_router import Vrf_routerFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.l3_access_list.l3_access_list import L3_access_listFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.bgp_community.bgp_community import Bgp_communityFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.bgp_ext_community.bgp_ext_community import Bgp_ext_communityFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.bgp_large_community.bgp_large_community import Bgp_large_communityFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.access_list_ipv4.access_list_ipv4 import Access_list_ipv4Facts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.access_list_ipv6.access_list_ipv6 import Access_list_ipv6Facts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.access_list_mac.access_list_mac import Access_list_macFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.qos_buffer.qos_buffer import Qos_bufferFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.qos_map.qos_map import Qos_mapFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.qos_scheduler.qos_scheduler import Qos_schedulerFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.qos_wred.qos_wred import Qos_wredFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.sflow.sflow import SflowFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.mirror_session.mirror_session import Mirror_sessionFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.lldp.lldp import LldpFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.system.system import SystemFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.dot1x.dot1x import Dot1xFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.edge_security.edge_security import Edge_securityFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.syslog.syslog import SyslogFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.crm.crm import CrmFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.stp.stp import StpFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.poe.poe import PoeFacts
from ansible_collections.celestica.sonic.plugins.module_utils.network.sonic.facts.feature.feature import FeatureFacts

LEGACY_SUBSETS = {}
RESOURCE_SUBSETS = dict(
    radius=RadiusFacts,
    ntp=NtpFacts,
    interface=InterfaceFacts,
    vlan=VlanFacts,
    snmp=SnmpFacts,
    tacacs=TacacsFacts,
    l2_interface=L2_interfaceFacts,
    l3_interface=L3_interfaceFacts,
    mclag=MclagFacts,
    sag=SagFacts,
    vrf=VrfFacts,
    portchannel=PortchannelFacts,
    vxlan=VxlanFacts,
    router=RouterFacts,
    loopback=LoopbackFacts,
    prefix_list=Prefix_listFacts,
    tunnel=TunnelFacts,
    route_map=Route_mapFacts,
    bgp_af=Bgp_afFacts,
    bgp_af_neighbor=Bgp_af_neighborFacts,
    bgp=BgpFacts,
    bgp_neighbor=Bgp_neighborFacts,
    vrf_router=Vrf_routerFacts,
    l3_access_list=L3_access_listFacts,
    bgp_community=Bgp_communityFacts,
    bgp_ext_community=Bgp_ext_communityFacts,
    bgp_large_community=Bgp_large_communityFacts,
    access_list_ipv4=Access_list_ipv4Facts,
    access_list_ipv6=Access_list_ipv6Facts,
    access_list_mac=Access_list_macFacts,
    qos_buffer=Qos_bufferFacts,
    qos_map=Qos_mapFacts,
    qos_scheduler=Qos_schedulerFacts,
    qos_wred=Qos_wredFacts,
    sflow=SflowFacts,
    mirror_session=Mirror_sessionFacts,
    lldp=LldpFacts,
    system=SystemFacts,
    dot1x=Dot1xFacts,
    edge_security=Edge_securityFacts,
    syslog=SyslogFacts,
    crm=CrmFacts,
    stp=StpFacts,
    poe=PoeFacts,
    feature=FeatureFacts,
)


class Facts(FactsBase):
    """ The fact class for celestica.sonic
    """

    VALID_LEGACY_SUBSETS = frozenset(LEGACY_SUBSETS.keys())
    VALID_RESOURCE_SUBSETS = frozenset(RESOURCE_SUBSETS.keys())

    def __init__(self, module):
        super(Facts, self).__init__(module)

    def get_facts(self, legacy_facts_type=None, resource_facts_type=None, data=None):
        """ Collect the facts for celestica.sonic

        :param legacy_facts_type: List of legacy facts types
        :param resource_facts_type: List of resource fact types
        :param data: previously collected conf
        :rtype: dict
        :return: the facts gathered
        """
        if self.VALID_RESOURCE_SUBSETS:
            self.get_network_resources_facts(RESOURCE_SUBSETS, resource_facts_type, data)

        if self.VALID_LEGACY_SUBSETS:
            self.get_network_legacy_facts(LEGACY_SUBSETS, legacy_facts_type)

        return self.ansible_facts, self._warnings
