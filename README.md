# Celestica SONiC Ansible Collection

The Ansible Celestica SONiC collection includes a variety of Ansible content to help automate the management of Celestica SONiC network appliances.

This collection has been tested against Advanced Celestica SONiC 2.0.0

### Supported connections
The Celestica SONiC collection supports ``network_cli`` connection.

## Included content

<!--start collection content-->
### Cliconf plugins
| Name | Description |
| --- | --- |
| [network_cli](https://github.com/ansible-collections/celestica.sonic)|Use cliconf to run command on Celestica SONiC platform |

### Collection core modules
| Name | Description | Connection type |
| --- | --- | --- |
| [**command**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/command/)|Run arbitrary commands through the CLI|network_cli |
| [**config**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/config)|Manage configuration through the CLI|network_cli |

### Collection network resource modules
Listed are the Celestica SONiC Ansible network resource modules which need ***network_cli*** as the connection type. Supported operations are ***merged*** and ***deleted***.

| Name | Description |
| --- | --- |
| [**access_list_ipv4**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/access_list_ipv4/)| Manage IPv4 access-list configurations |
| [**access_list_ipv6**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/access_list_ipv6/)| Manage IPv6 access-list configurations |
| [**access_list_mac**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/access_list_mac/)| Manage MAC access-list configurations |
| [**bgp**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/bgp/)| Manage BGP configurations |
| [**bgp_af**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/bgp_af/)| Manage BGP address family configurations |
| [**bgp_af_neighbor**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/bgp_af_neighbor/)| Manage BGP neighbor in address family configurations |
| [**bgp_community**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/bgp_community/)| Manage BGP community configurations |
| [**bgp_ext_community**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/bgp_ext_community/)| Manage BGP extended community configurations |
| [**bgp_large_community**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/bgp_large_community/)| Manage BGP large community configurations |
| [**bgp_neighbor**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/bgp_neighbor/)| Manage BGP neighbor configurations |
| [**crm**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/crm/)| Manage CRM (Critical Resource Monitoring) configurations |
| [**dot1x**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/dot1x/)| Manage dot1x configurations |
| [**edge_security**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/edge_security/)| Manage edge-security configurations |
| [**feature**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/feature/)| Manage feature configurations |
| [**interface**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/interface/)| Manage Ethernet interface configurations |
| [**l2_interface**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/l2_interface/)| Manage interface to VLAN association based on access or trunk mode configurations |
| [**l3_access_list**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/l3_access_list/)| Manage Layer3 access-list configurations |
| [**l3_interface**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/l3_interface/)| Manage Layer2 interface configurations |
| [**lldp**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/lldp/)| Manage LLDP configurations |
| [**loopback**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/loopback/)| Manage loopback interface configurations |
| [**mclag**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/mclag/)| Manage McLAG configurations |
| [**mirror_session**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/mirror_session/)| Manage mirror session configurations |
| [**ntp**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/ntp/)| Manage NTP configurations |
| [**poe**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/poe/)| Manage PoE configurations |
| [**portchannel**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/portchannel/)| Manage Portchannel interface configurations |
| [**prefix_list**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/prefix_list/)| Manage prefix-list configurations |
| [**qos_buffer**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/qos_buffer/)| Manage QoS buffer configurations |
| [**qos_map**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/qos_map/)| Manage QoS map configurations |
| [**qos_scheduler**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/qos_scheduler/)| Manage QoS scheduler configurations |
| [**qos_wred**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/qos_wred/)| Manage QoS WRED configurations |
| [**radius**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/radius/)| Manage RADIUS configurations |
| [**route_map**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/route_map/)| Manage route map configurations |
| [**router**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/router/)| Manage router with default VRF configurations |
| [**sag**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/sag/)| Manage SAG configurations |
| [**sflow**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/sflow/)| Manage sFlow configurations |
| [**snmp**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/snmp/)| Manage SNMP configurations |
| [**stp**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/stp/)| Manage STP configurations |
| [**syslog**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/syslog/)| Manage syslog configurations |
| [**system**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/system/)| Manage global system specific configurations |
| [**tacacs**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/tacacs/)| Manage TACACS+ configurations |
| [**tunnel**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/tunnel/)| Manage Tunnel interface configurations |
| [**vlan**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/vlan/)| Manage VLAN interface configurations |
| [**vrf**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/vrf/)| Manage VRF configurations |
| [**vrf_router**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/vrf_router/)| Manage router with VRF configurations |
| [**vxlan**](https://galaxy.ansible.com/ui/repo/published/celestica/sonic/content/module/vxlan/)| Manage VxLAN interface configurations |

### Use case playbooks
The playbooks directory includes the below sample playbooks for end-to-end use cases.

| Name | Description |
| --- | --- |
| [**Layer 3 fabric**](https://github.com/ansible-collections/celestica.sonic/blob/main/playbooks/l3_fabric/README.md)|Sample playbook to build a Layer 3 leaf-spine fabric |
<!--end collection content-->

## Installing this collection

You can install the Celestica SONiC collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install celestica.sonic

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: celestica.sonic
```

## Using this collection

This collection includes [network resource modules](https://docs.ansible.com/ansible/latest/network/user_guide/network_resource_modules.html).

### Sample playbooks

You can use modules by their Fully Qualified Collection Namespace (FQCN), such as `celestica.sonic.l2_interface` as depicted below.

***command_module_sample_playbook.yaml***

```yaml
---
- name: Command module - sample playbook
  hosts: all
  gather_facts: no

  tasks:

    - name: Run show version on remote devices with click_cli mode
    celestica.sonic.command:
        mode: click_cli
        commands: show version

    - name: Run show version and check to see if output contains advanced_celestica_sonic with sonic_cli mode
    celestica.sonic.command:
        mode: sonic_cli
        commands: show version
        wait_for: result[0] contains advanced_celestica_sonic

    - name: Run show running-config bgp on remote devices with frr_cli mode
    celestica.sonic.command:
        mode: frr_cli
        commands: show running-config bgp
```

***config_module_sample_playbook.yaml***

```yaml
---
- name: Config module - sample playbook
  hosts: all
  gather_facts: no

  tasks:

    - name: Configure vlan & vlan members and save as startup-config
    celestica.sonic.config:
        mode: click_cli
        lines:
        - config vlan member add 10 Ethernet0
        - config vlan member del 10 Ethernet0
        before:
        - config vlan add 10
        - config vlan add 20
        save_when: always

    - name: Configure BGP and save as startup-config when changed
    celestica.sonic.config:
        mode: frr_cli
        lines:
        - router bgp 1
        - address-family ipv4 unicast
        - network 1.0.0.0/8
        save_when: changed

    - name: Configuer ACL rules with exact match
    celestica.sonic.config:
        mode: sonic_cli
        lines:
        - 10 permit ip 191.0.2.1/32 any
        - 20 permit ip 191.0.2.2/32 any
        - 30 permit ip 191.0.2.3/32 any
        - 40 permit ip 191.0.2.4/32 any
        - 50 permit ip 191.0.2.5/32 any
        parents: ip access-list test
        before: no ip access-list test
        match: exact
```

***network_resource_module_sample_playbook.yaml***

```yaml
---
- name: Network resource module - sample playbook
  hosts: all
  gather_facts: no

  tasks:

    - name: Configure access and trunk VLANs
      celestica.sonic.l2_interface:
        config:
          interface:
            - name: Ethernet0
              access:
                vlan: 101
              trunk:
                - vlan: 102
            - name: Ethernet1
              access:
                vlan: 102
            - name: PortChannel11
              access:
                vlan: 102
              trunk:
                - vlan: 101
```

***inventory.ini***
```
[leaf]
leaf_1 ansible_host=100.108.81.130

[spine]
spine_1 ansible_host=100.108.81.131

[leaf:vars]
ansible_connection=ansible.netcommon.network_cli
ansible_network_os=celestica.sonic.sonic

[spine:vars]
ansible_connection=ansible.netcommon.network_cli
ansible_network_os=celestica.sonic.sonic
```

## Code of Conduct
This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).

## Changelogs
<!--Add a link to a changelog.md file or an external docsite to cover this information. -->
## Release notes

Release notes are available [here](https://github.com/ansible-collections/celestica.sonic/blob/main/CHANGELOG.rst).

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

- [Ansible network resources](https://docs.ansible.com/ansible/latest/network/getting_started/network_resources.html)
- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
