# L3 fabric Topology

## Overview
This document describes the Layer 3 fabric topology for a network consisting of two pods (Pod-1 and Pod-2) and the inter-pod connections. The topology follows a typical Clos network design, providing high bandwidth and redundancy.

**Key Features:**

- **Spine-Leaf Architecture:** Each pod utilizes a spine-leaf architecture, where leaf switches connect to servers and border gateways, while spine switches provide high-speed connectivity between leaf switches within the pod.
- **Inter-Pod Connectivity:** Border leaf switches in each pod are interconnected to facilitate communication between pods.
- **Scalability:** The design allows for easy expansion by adding more leaf switches to a pod or introducing additional pods.

## Topology
The L3 fabric topology is divided into three main sections:

### Pod-1
**Diagram:**
```
         ┌────────────────┐
         │                │
         │Pod-1-Border-   │
         │  -Leaf-01      │
         │                │                                      ┌────────────────┐
         └───────────┬───┬┘                                      │                │
                     │   │                                       │Pod-1-Border-   │
                     │   │                                       │  -Leaf-02      │
                     │   │                                       │                │
                     │   │                                       └┬──────────┬────┘
                     │   │                                        │          │
                     │   │                                        │          │
                     │   └────────────────────────────────────────┼─┐        │
                     │                                            │ │        │
                     │       ┌────────────────────────────────────┘ │        │
                   ┌─┴───────┴────┐                             ┌───┴────────┴─┐
                   │              │                             │              │
                   │              │                             │              │
                   │Pod-1-Spine-01│                             │Pod-1-Spine-02│
                   │              │                             │              │
                   └──┬─────┬─┬─┬─┘                             └──┬───┬──┬──┬─┘
                      │     │ │ │                                  │   │  │  │
                      │     │ │ │                                  │   │  │  │
                      │     │ │ └──────────────────┐               │   │  │  │
           ┌──────────┼─────┼─┼────────────────────┼───────────────┼───┘  │  │
           │          │     │ │                    │               │      │  │
           │          │     │ └────────────────────┼───────────────┼──────┼──┼──┐
       ┌───┼──────────┴     │       ┌──────────────┼───────────────┼──────┘  │  │
       │   │                │       │              │               │         │  │
       │   │                │       │              │         ┌─────┘         │  │
       │   │                │       │              │         │               │  │
 ┌─────┴───┴────┐       ┌───┴───────┴──┐         ┌─┴─────────┴──┐     ┌──────┴──┴────┐
 │              │       │              │         │              │     │              │
 │              ├───────┤              │         │              ├─────┤              │
 │ Pod-1-Leaf-01│       │ Pod-1-Leaf-02│         │Pod-1-Leaf-03 │     │Pod-1-Leaf-04 │
 │              │       │              │         │              │     │              │
 └──────────────┘       └──────────────┘         └──────────────┘     └──────────────┘
```
**Description:**
Pod-1 consists of two spine switches (Pod-1-Spine-01, Pod-1-Spine-02) and four leaf switches (Pod-1-Leaf-01 to Pod-1-Leaf-04). Two border leaf switches (Pod-1-Border-Leaf-01 and Pod-1-Border-Leaf-02) provide connectivity to external networks or other pods.

### PoD-2
**Diagram:**
```
          ┌────────────────┐
          │                │
          │Pod-2-Border-   │
          │  -Leaf-01      │
          │                │                                      ┌────────────────┐
          └───────────┬───┬┘                                      │                │
                      │   │                                       │Pod-2-Border-   │
                      │   │                                       │  -Leaf-02      │
                      │   │                                       │                │
                      │   │                                       └┬──────────┬────┘
                      │   │                                        │          │
                      │   │                                        │          │
                      │   └────────────────────────────────────────┼─┐        │
                      │                                            │ │        │
                      │       ┌────────────────────────────────────┘ │        │
                    ┌─┴───────┴────┐                             ┌───┴────────┴─┐
                    │              │                             │              │
                    │              │                             │              │
                    │Pod-2-Spine-01│                             │Pod-2-Spine-02│
                    │              │                             │              │
                    └──┬─────┬─┬─┬─┘                             └──┬───┬──┬──┬─┘
                       │     │ │ │                                  │   │  │  │
                       │     │ │ │                                  │   │  │  │
                       │     │ │ └──────────────────┐               │   │  │  │
            ┌──────────┼─────┼─┼────────────────────┼───────────────┼───┘  │  │
            │          │     │ │                    │               │      │  │
            │          │     │ └────────────────────┼───────────────┼──────┼──┼──┐
        ┌───┼──────────┴     │       ┌──────────────┼───────────────┼──────┘  │  │
        │   │                │       │              │               │         │  │
        │   │                │       │              │         ┌─────┘         │  │
        │   │                │       │              │         │               │  │
  ┌─────┴───┴────┐       ┌───┴───────┴──┐         ┌─┴─────────┴──┐     ┌──────┴──┴────┐
  │              │       │              │         │              │     │              │
  │              ├───────┤              │         │              ├─────┤              │
  │ Pod-2-Leaf-01│       │ Pod-2-Leaf-02│         │Pod-2-Leaf-03 │     │Pod-2-Leaf-04 │
  │              │       │              │         │              │     │              │
  └──────────────┘       └──────────────┘         └──────────────┘     └──────────────┘
```
**Description:**
Pod-2 mirrors the structure of Pod-1, with two spine switches and four leaf switches, including two border leaf switches for external connectivity.

### Inter-Pod Network
**Diagram:**
```
                                                  ┌────────────────┐
  ┌────────────────┐                              │                │
  │                ├──────────────────────────────┤Pod-2-Border-   │
  │Pod-1-Border-   │                              │  -Leaf-01      │      ┌────────────────┐
  │  -Leaf-01      │      ┌────────────────┐      │                ├──────┤                │
  │                ├──────┤                │      └───────────┬───┬┘      │Pod-2-Border-   │
  └───────────┬───┬┘      │Pod-1-Border-   ├──────────────────┼───┼───────┤  -Leaf-02      │
              │   │       │  -Leaf-02      │                  │   │       │                │
              │   │       │                │                  │   │       └┬──────────┬────┘
              │   │       └┬──────────┬────┘                  │   │        │          │
              │   │        │          │                       │   │        │          │
              │   │        │          │                       │   │
              │   │
```
**Description:**
Border leaf switches from Pod-1 and Pod-2 are directly interconnected to establish communication between the two pods. This connection ensures high bandwidth and low latency for inter-pod traffic.

### Platforms

This table outlines the Celestica network switches used in Pod-1 and Pod-2.

| Role        | Platform |
|-------------|----------|
| Border Leaf | DS2000   |
| Leaf        | DS2000   |
| Spine       | DS3000   |

## Using the playbooks
This section explains how to use the provided Ansible playbooks to configure and deploy the L3 fabric topology.

- **Prerequisites:**
  - Ansible control node installed and configured.
  - Inventory file containing the IP addresses and credentials of all network devices (spines, leafs, border leafs).
  - Necessary Ansible roles and modules for network automation.
  - Management VRF shall be configured already.
- **Playbook Structure:**
  - Common Playbook: Provisions the common configurations on all switches.
  - Spine Playbook: Configures the spine switches (e.g., `spine.yml`).
  - Leaf Playbook: Configures the leaf switches (e.g., `leaf.yml`).
  - Border Leaf Playbook: Configures the border leaf switches (e.g., `border_leaf.yml`).
  - All Playbook: Configures the entire topology (`common.yml`, `leaf.yml`, `spine.yml` and `border_leaf.yml`)
- **Execution:**
  - Modify the inventory file `inventory.yml` with your device information.
  - Update the playbook variables as needed (e.g., VLANs, IP addresses).

    | Playbook | Variable | Description | File |
    |---|---|---|---|
    | Common | `tacacs_server_ip` | IP address of the TACACS+ server. | `group_vars/all.yml` |
    | Common | `encrypted_passkey` | Encrypted password for the TACACS+ server. | `group_vars/all.yml` |
    | Common | `tacacs_vrf` | VRF for the TACACS+ server. | `group_vars/all.yml` |
    | Common | `ntp_source_interface` | Source interface for NTP. | `group_vars/all.yml` |
    | Common | `ntp_vrf` | VRF for NTP. | `group_vars/all.yml` |
    | Common | `ntp_server_ips` | List of NTP server IP addresses. | `group_vars/all.yml` |
    | Common | `snmp_community` | SNMPv2 community string. | `group_vars/all.yml` |
    | Common | `snmp_community_access` | Access level for SNMPv2 community. | `group_vars/all.yml` |
    | Common | `snmpv3_users` | List of SNMPv3 user dictionaries. Each dictionary should contain keys for `username`, `auth_password`, `encrypt_password`, `auth_protocol`, and `encrypt_protocol`. | `group_vars/all.yml` |
    | Common | `snmpv3_user_type` | Type of SNMPv3 user (e.g., 'Priv'). | `group_vars/all.yml` |
    | Common | `snmpv3_auth_algorithm` | Authentication algorithm for SNMPv3 (e.g., 'SHA'). | `group_vars/all.yml` |
    | Common | `snmpv3_encrypt_algorithm` | Encryption algorithm for SNMPv3 (e.g., 'AES'). | `group_vars/all.yml` |
    | Common | `snmpv3_access` | Access level for SNMPv3 users. | `group_vars/all.yml` |
    | Spine | `border_leaf__neighbor_tag` | BGP neighbor tag for border leaf switches. | `group_vars/spine_group.yml` |
    | Spine | `leaf_neighbor_tag` | BGP neighbor tag for leaf switches. | `group_vars/spine_group.yml` |
    | Spine | `border_leaf__going_interfaces` | List of interfaces connecting to border leaf switches. | `group_vars/spine_group.yml` |
    | Spine | `leaf_going_interfaces` | List of interfaces connecting to leaf switches. | `group_vars/spine_group.yml` |
    | Spine | `underlay_lb_ip` | Underlay loopback IP address for the spine switch. | Respective host_vars file (e.g., `host_vars/Pod-1-Spine-01.yml`) |
    | Spine | `underlay_lb_ip_mask` | Subnet mask for the underlay loopback IP address. | Respective host_vars file |
    | Spine | `spine_asn` | ASN for the spine switches. | Respective host_vars file |
    | Leaf | `spine_neighbor_tag` | BGP neighbor tag for spine switches. | `group_vars/leaf_group.yml` |
    | Leaf | `spine_going_interfaces` | List of interfaces connecting to spine switches. | `group_vars/leaf_group.yml` |
    | Leaf | `tenant_vrf` | Name of the tenant VRF. | `group_vars/leaf_group.yml` |
    | Leaf | `sag_mac` | Static Anycast Gateway (SAG) MAC address. | `group_vars/leaf_group.yml` |
    | Leaf | `mclag_domain_id` | MCLAG domain ID. | `group_vars/leaf_group.yml` |
    | Leaf | `peer_link` | Interface used for peer link. | `group_vars/leaf_group.yml` |
    | Leaf | `vtep_number` | VXLAN Tunnel Endpoint (VTEP) number. | `group_vars/leaf_group.yml` |
    | Leaf | `tunnel_vlan` | VLAN ID for VXLAN tunnel traffic. | `group_vars/leaf_group.yml` |
    | Leaf | `underlay_lb_ip` | Underlay loopback IP address for the leaf switch. | Respective host_vars file (e.g., `host_vars/Pod-1-Leaf-01.yml`) |
    | Leaf | `underlay_lb_ip_mask` | Subnet mask for the underlay loopback IP address. | Respective host_vars file |
    | Leaf | `overlay_ident_lb_ip` | Overlay identifier loopback IP address. | Respective host_vars file |
    | Leaf | `overlay_ident_lb_ip_mask` | Subnet mask for the overlay identifier loopback IP address. | Respective host_vars file |
    | Leaf | `leaf_asn` | ASN for the leaf switch. | Respective host_vars file |
    | Leaf | `peer_underlay_lb_ip` | Underlay loopback IP address of the peer leaf switch. | Respective host_vars file |
    | Leaf | `system_mac` | System MAC address of the leaf switch. | Respective host_vars file |
    | Leaf | `peer_switch_physical_mac` | Physical MAC address of the peer leaf switch. | Respective host_vars file |
    | Leaf | `l2_tenant_vlans` | List of L2 tenant VLAN IDs. | Respective host_vars file |
    | Leaf | `l3_tenant_vlans` | List of L3 tenant VLAN IDs. | Respective host_vars file |
    | Leaf | `trunk_vlan_members` | List of Trunk VLAN members. | Respective host_vars file |
    | Leaf | `access_vlan_members` | List of Access VLAN members. | Respective host_vars file |
    | Border Leaf | `tenant_vrf` | Name of the tenant VRF. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `vrf_vni` | VXLAN Network Identifier (VNI) for the tenant VRF. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `tunnel_vlan` | VLAN ID for VXLAN tunnel traffic. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `other_site_border_leaf_interface` | Interface connecting to the border leaf switch at the other site. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `same_site_border_leaf_interface` | Interface connecting to the border leaf switch at the same site. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `spine_interfaces` | List of interfaces connecting to spine switches. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `vtep_number` | VXLAN Tunnel Endpoint (VTEP) number. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `sdwan_ip_address` | SD-WAN IP address. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `sdwan_asn` | SD-WAN ASN. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `firewall_vlans` | List of firewall VLAN IDs. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `mclag_domain_id` | MCLAG domain ID. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `peer_link` | Interface used for peer link. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `lag_members` | Link aggregation group members. | `group_vars/border_leaf_group.yml` |
    | Border Leaf | `underlay_lb_ip` | Underlay loopback IP address for the border leaf switch. | Respective host_vars file (e.g., `host_vars/Pod-1-Border-Leaf-01.yml`) |
    | Border Leaf | `peer_underlay_lb_ip` | Underlay loopback IP address for the peer border leaf switch. | Respective host_vars file |
    | Border Leaf | `underlay_lb_ip_mask` | Subnet mask for the underlay loopback IP address. | Respective host_vars file |
    | Border Leaf | `overlay_ident_tun_lb_ip` | Overlay identifier tunnel loopback IP address. | Respective host_vars file |
    | Border Leaf | `overlay_ident_tun_lb_ip_mask` | Subnet mask for the overlay identifier tunnel loopback IP address. | Respective host_vars file |
    | Border Leaf | `overlay_unique_lb_ip` | Overlay unique loopback IP address. | Respective host_vars file |
    | Border Leaf | `overlay_unique_lb_ip_mask` | Subnet mask for the overlay unique loopback IP address. | Respective host_vars file |
    | Border Leaf | `border_leaf_asn` | ASN for the border leaf switch. | Respective host_vars file |
    | Border Leaf | `tenant_asn` | ASN for the tenant network. | Respective host_vars file |
    | Leaf | `system_mac` | System MAC address of the border leaf switch. | Respective host_vars file |
  - Execute the `all.yml` playbook.
    ```
    ansible-playbook all.yml
    ```

## Leaf Switch Physical MAC Address Mapping

This table outlines the assumed physical MAC addresses for the leaf switches in Pod-1 and Pod-2.

**Please update these values in the respective host_vars files with the actual physical MAC addresses of your devices.**

| Pod | Leaf Switch | Assumed Physical MAC Address | Host Vars File |
|---|---|---|---|
| Pod-1 | Pod-1-Leaf-01 | 00:00:00:00:AA:01 | `host_vars/Pod-1-Leaf-02.yml` |
| Pod-1 | Pod-1-Leaf-02 | 00:00:00:00:AA:02 | `host_vars/Pod-1-Leaf-01.yml` |
| Pod-1 | Pod-1-Leaf-03 | 00:00:00:00:AA:03 | `host_vars/Pod-1-Leaf-04.yml` |
| Pod-1 | Pod-1-Leaf-04 | 00:00:00:00:AA:04 | `host_vars/Pod-1-Leaf-03.yml` |
| Pod-2 | Pod-2-Leaf-01 | 00:00:00:00:AB:01 | `host_vars/Pod-2-Leaf-02.yml` |
| Pod-2 | Pod-2-Leaf-02 | 00:00:00:00:AB:02 | `host_vars/Pod-2-Leaf-01.yml` |
| Pod-2 | Pod-2-Leaf-03 | 00:00:00:00:AB:03 | `host_vars/Pod-2-Leaf-04.yml` |
| Pod-2 | Pod-2-Leaf-04 | 00:00:00:00:AB:04 | `host_vars/Pod-2-Leaf-03.yml` |

**Important:** Failure to update these MAC addresses with the correct values is considered as network configuration error and may result in traffic failures.

## Add new device
This section provides instructions on how to add a new device (spine, leaf, or border leaf) to the existing L3 fabric.

- **Inventory Update:** Add the new device's IP address, credentials, and group (spine, leaf, border_leaf) to the Ansible inventory file.
- **Variable Configuration:** Update the relevant playbook variables to include the new device's configuration (e.g., IP address, VLAN assignments).
- **Playbook Execution:** Run the corresponding playbook (spine, leaf, or border_leaf) to configure the new device and integrate it into the fabric.

**Example:**

To add a new leaf switch to Pod-1:

- Add the new leaf switch details to the inventory file under the `leaf_group`.
- Add new host_vars file for the node (e.g., `host_vars/Pod-1-Leaf-05.yml`)
- Add required variables in `host_vars/Pod-1-Border-Leaf-05.yml` file
- Execute the `leaf.yml` playbook to configure the new leaf switch.