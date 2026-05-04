# NX-OS MCP Server — Prompt Library

## Tool Domain Map

The NX-OS MCP server communicates directly with **Cisco Nexus switches via NX-API**, supporting both CLI text and structured JSON output modes. Unlike the IOS-XE server which targets a single device, the NX-OS server is designed for **multi-device parallel execution** — a critical capability for spine-leaf fabric operations

| Domain | Core Tools |
|---|---|
| **CLI Execution** | `run_nxos_command`, `run_nxos_commands_parallel`, `run_config_command`, `send_nxapi_request` |
| **Interface Operations** | `get_interfaces`, `get_interface_counters`, `get_interface_brief`, `get_port_channels` |
| **Routing** | `get_bgp_summary`, `get_bgp_neighbors`, `get_ospf_neighbors`, `get_ip_routes`, `get_route_detail` |
| **VXLAN / EVPN** | `get_nve_peers`, `get_vxlan_vni`, `get_evpn_evi`, `get_l2route_evpn`, `get_vtep_summary` |
| **vPC** | `get_vpc_summary`, `get_vpc_peer_status`, `get_vpc_consistency`, `get_vpc_members` |
| **Fabric Extender** | `get_fex_list`, `get_fex_detail`, `get_fex_interfaces` |
| **VLAN & L2** | `get_vlan_list`, `get_vlan_detail`, `get_mac_address_table`, `get_stp_summary` |
| **VRF** | `get_vrf_list`, `get_vrf_detail`, `get_vrf_route_table` |
| **Device Health** | `get_system_resources`, `get_environment`, `get_module_info`, `get_platform` |
| **Security** | `get_acl_list`, `get_acl_detail`, `get_copp_statistics` |
| **Configuration** | `get_running_config`, `push_config`, `diff_config`, `backup_config` |
| **HSRP / VRRP** | `get_hsrp_summary`, `get_vrrp_detail` |
| **Logging** | `get_logging_buffer`, `get_syslog`, `get_event_history` |

> ⚠️ **Multi-device safety:** When using parallel command execution across multiple Nexus devices, always **confirm target device list** before running any configuration push or write operation. Read-only show commands are safe to run in parallel freely.

***

## 🏢 Category 1 — Device Health & Platform Diagnostics

For **NOC Teams and DC Operations Engineers** performing real-time health checks across Nexus fleets.

1. **"Run `show system resources` on all Nexus 9000 spine switches simultaneously. Return CPU utilization, memory utilization (used vs. free), and process count per device. Flag any spine with CPU 1-minute average above 70% or memory utilization above 85%."**

2. **"Run `show environment` on `DC-LEAF-101` and `DC-LEAF-102`. Show power supply status, fan tray status, and all temperature sensor readings. Flag any sensor above its warning threshold."**

3. **"Get the module inventory for all switches in the `DC-CORE` group. Show each module slot, card type, serial number, hardware revision, and operational state. Flag any module not in the `ok` state."**

4. **"What is the platform summary and NX-OS software version running on each Nexus device in the fabric? I need a complete version matrix — run `show version` across all devices in parallel and compare results."**

5. **"Run `show logging last 100` on `DC-SPINE-01` and `DC-SPINE-02`. Filter for SEVERITY levels CRITICAL, ERROR, and WARNING. Show timestamp, facility, and message. Flag any messages related to hardware faults, ASIC errors, or link instability."**

6. **"Run `show hardware capacity` on all Nexus 9000 leaf switches. Show LPM (Longest Prefix Match) route table utilization, ACL TCAM usage, and MAC table usage. Flag any resource exceeding 75% capacity — these are scale limit warnings."**

***

## 🔌 Category 2 — Interface & Port Channel Operations

For **DC Network Engineers** managing physical and logical interfaces on Nexus platforms.

7. **"Run `show interface status` on `DC-LEAF-103` and return all interfaces. Group by state — show connected, notconnect, and err-disabled ports separately. For err-disabled ports, show the error-disable reason."**

8. **"Get the detailed interface statistics for `Ethernet1/1` through `Ethernet1/4` on `DC-SPINE-01`. Show input/output rates in Mbps, input/output errors, CRC count, and giants/runts. Flag any interface with non-zero CRC or error counters."**

9. **"Show all port-channel interfaces on `DC-LEAF-101`. For each port-channel, show member interfaces, LACP mode, port-channel state, individual member states, and whether all members are bundled. Flag any port-channel with a member in suspended state."**

10. **"Run `show interface counters errors` across all leaf switches in parallel. Return a ranked list of the top 10 interfaces by total error count across the entire fabric — I need to identify the most error-prone physical links."**

11. **"Which interfaces on `DC-LEAF-104` have input utilization above 80%? Run `show interface` and calculate per-interface bandwidth utilization. Flag uplink interfaces approaching saturation — these are congestion risks."**

12. **"Run `show cdp neighbors detail` on `DC-LEAF-105`. Show all CDP-discovered neighbors — their device ID, platform, local interface, remote interface, and software version. I need this for fabric topology verification after a new leaf was added."**

***

## 🗺️ Category 3 — BGP & Routing Protocol Operations

For **DC Network Architects and Operations Teams** managing BGP fabric control planes.

13. **"Run `show bgp summary` on all spine switches simultaneously. For each spine, show all BGP neighbors, their AS number, state, uptime, prefixes received, and prefixes sent. Flag any neighbor not in the `Established` state across any spine."**

14. **"Get the BGP EVPN summary from `DC-SPINE-01`. Show all leaf VTEP peers in BGP EVPN, their state, number of EVPN routes exchanged (Type-2 MAC/IP, Type-3 Inclusive Multicast, Type-5 IP Prefix), and whether any leaf is missing from the EVPN control plane."**

15. **"Run `show ip route summary` on all Nexus devices in parallel. How many total routes are in each device's RIB? Show breakdown by protocol (BGP, OSPF, Static, Connected, Direct). Flag any significant discrepancy between spine and leaf route counts."**

16. **"Show the BGP neighbor detail for underlay peer `169.254.0.1` on `DC-LEAF-101`. I need the full BGP session state — hold timer, keepalive, last reset reason, inbound/outbound route-map applied, and BFD state."**

17. **"Run `show ip ospf neighbors` on `DC-SPINE-01` and `DC-SPINE-02` simultaneously. Are all OSPF neighbor adjacencies in FULL state? Flag any neighbor in EXSTART, EXCHANGE, or 2WAY state — these indicate OSPF convergence issues."**

18. **"On `DC-LEAF-102`, run `show ip route 10.50.100.0/24`. Show the best path selection — next-hop, outgoing interface, administrative distance, metric, and whether ECMP is active across multiple uplinks."**

***

## 🌐 Category 4 — VXLAN BGP EVPN Fabric Operations

For **DC Architects and Overlay Network Engineers** managing VXLAN BGP EVPN deployments. [cisco](https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/102x/configuration/vxlan/cisco-nexus-9000-series-nx-os-vxlan-configuration-guide-release-102x/m_configuring_vxlan_bgp_evpn.html)

19. **"Run `show nve peers` on all leaf switches in parallel. Show each peer's VTEP IP, VNI associations, state, and uptime. Flag any peer that is in a non-UP state or missing from expected peer list — this indicates underlay or EVPN control plane failure."**

20. **"Show the complete NVE interface configuration and status on `DC-LEAF-101`. Show the source interface (loopback), host-reachability protocol, and all member VNIs — both L2 VNIs (with associated VLANs) and L3 VNIs (with associated VRFs)."**

21. **"Run `show vxlan` on all leaf switches and return the VNI-to-VLAN mapping table. Are the VNI assignments consistent across all leaves? Flag any leaf where a VNI is mapped to a different VLAN than its peers — this is a misconfiguration that will cause forwarding black holes."**

22. **"Run `show bgp l2vpn evpn summary` on `DC-SPINE-01`. Show all Type-2 (MAC/IP) route count, Type-3 (IMET) route count, and Type-5 (IP Prefix) route count. Flag if any leaf is advertising significantly fewer Type-2 routes than expected — this may indicate endpoint learning issues."**

23. **"On `DC-LEAF-103`, run `show bgp l2vpn evpn` and filter for MAC address `a4:c3:f0:9b:12:44`. Show the EVPN route detail — originating VTEP IP, associated VNI, VLAN, and BGP path attributes. I need to trace this MAC to its physical host attachment point."**

24. **"Check the anycast gateway configuration across all leaf switches. Run `show ip arp` filtered to the anycast gateway MAC `0000.2222.3333` on each leaf. Confirm the anycast gateway MAC is consistent across all leaves — any discrepancy will cause ARP resolution failures for routed traffic."**

25. **"Run `show l2route evpn mac all` on `DC-LEAF-101` and `DC-LEAF-102`. Compare the MAC tables — are there any MAC addresses learned on both leaves simultaneously without being a vPC-attached host? These are potential MAC flap events in the EVPN fabric."**

***

## 🔁 Category 5 — vPC (Virtual Port-Channel) Operations

For **DC Network Engineers** managing Nexus vPC domains for high-availability host attachment.

26. **"Run `show vpc summary` on all vPC peer pairs simultaneously. For each vPC domain, show the domain ID, peer-keepalive link status, peer-link (MCT) status, number of vPC member port-channels, and overall vPC consistency status. Flag any vPC domain that is not operationally consistent."**

27. **"Show the vPC consistency check detail on the `DC-LEAF-101`/`DC-LEAF-102` vPC pair. Are there any type-1 consistency mismatches (which cause vPC suspension) or type-2 mismatches (which are advisory only)? Show the specific parameter causing each mismatch."**

28. **"Get the vPC peer-link status on `DC-LEAF-101`. Show member interfaces of the peer-link port-channel, their individual states, traffic statistics, and whether the peer-link is carrying any non-vPC traffic (it should be minimal)."**

29. **"Run `show vpc role` on both members of each vPC pair. Confirm each pair has one `primary` and one `secondary` — flag any pair where both members claim the same role, which indicates a split-brain condition."**

30. **"Are there any vPC member port-channels on any leaf pair that are in `suspended` state? Run `show vpc` on all leaf switches in parallel and list any suspended vPC IDs — show the member interfaces and suspension reason."**

***

## 🗂️ Category 6 — VLAN, STP & Layer 2 Fabric

For **DC Operations Teams** managing Layer 2 domains and spanning tree.

31. **"Run `show vlan brief` across all leaf switches in parallel. Compare the VLAN databases — are all production VLANs (100–200) consistently present on all leaves? Flag any leaf missing a VLAN that is present on its peers."**

32. **"Run `show spanning-tree summary` on `DC-LEAF-101` through `DC-LEAF-106`. Are any VLANs still running STP in a VXLAN BGP EVPN fabric? In a properly configured VXLAN fabric, STP should be isolated to access-facing interfaces only — flag any VLAN running STP on uplink or NVE interfaces."**

33. **"Show the MAC address table on `DC-LEAF-103` for VLAN 200. How many MAC addresses are currently learned? Flag if the count exceeds the expected endpoint count for that VLAN — large unexpected MAC counts can indicate a loop or flooding condition."**

34. **"Run `show mac address-table dynamic` on `DC-LEAF-101` and find MAC `b8:27:eb:4f:2a:11`. Show the VLAN, port, and age. Is this MAC also appearing in the EVPN route table? Cross-reference with `show bgp l2vpn evpn` to confirm local vs. remote learning."**

***

## 🔐 Category 7 — VRF & Layer 3 Segmentation

For **Network Engineers** managing VRF-based tenant separation in VXLAN BGP EVPN.

35. **"List all VRFs configured on `DC-LEAF-101`. For each VRF, show the associated L3 VNI, route distinguisher (RD), route target import/export values, and number of routes in the VRF routing table."**

36. **"Run `show ip route vrf PROD` on `DC-LEAF-101` and `DC-LEAF-102`. Compare the route tables — are both leaves seeing the same set of prefixes in the `PROD` VRF? Flag any prefix present on one leaf but missing from the other."**

37. **"Check for VRF route leakage on `DC-CORE-SW-01`. Run `show ip route vrf all` and identify any routes that appear in multiple VRFs with the same next-hop — unintended route leakage between tenant VRFs is a critical security and compliance issue."**

***

## ⚙️ Category 8 — Configuration Read, Audit & Push

For **Senior Engineers and Change Management** managing Nexus configurations.

38. **"Get the running configuration from `DC-SPINE-01` and extract only the BGP configuration section. Show the router BGP AS number, all neighbor statements, address-family configurations, route-maps, and prefix-list references."**

39. **"Compare the running configuration vs. startup configuration on `DC-LEAF-103`. Show any unsaved differences — changes that will be lost on next reload. If there are differences, show the specific lines and prompt for a `copy running-config startup-config` confirmation."**

40. **"Audit the NTP configuration across all Nexus devices in parallel. Run `show run | include ntp` on each device and confirm all devices point to the same NTP servers. Flag any device with a missing or non-standard NTP configuration."**

41. **"Push a new ACL entry to `DC-LEAF-101` blocking inbound traffic from `198.51.100.0/24` on all external-facing interfaces. Show the complete configuration block that will be applied, confirm the target interfaces, and await confirmation before executing."**

***

## 🔒 Category 9 — Security & CoPP

For **Security Engineers** managing Nexus data plane security.

42. **"Run `show ip access-lists` on `DC-CORE-SW-01`. List all ACLs, their entry count, and cumulative hit counts. Flag any ACL with zero hits on all entries — these may be stale or misconfigured ACLs not matching any real traffic."**

43. **"Show the CoPP (Control Plane Policing) statistics on `DC-SPINE-01`. Which CoPP classes are currently dropping packets? Show the class name, configured rate, conforming packets, and dropped packets. CoPP drops indicate the control plane is being rate-limited."**

44. **"Run `show system internal acl feature` on `DC-LEAF-101` to check TCAM allocation for ACL features. Show which features are consuming TCAM slices — flag any feature at or above 90% of its allocated TCAM region."**

***

## 🏭 Vertical-Specific Prompt Packs

### Financial Services / Low-Latency Trading
- *"Run `show interface ethernet 1/1` on all Nexus switches connected to trading infrastructure. Return the output queue depth, input/output rate in packets-per-second, and any tail-drop or WRED drop counters. In trading environments, even microsecond-level congestion drops are unacceptable — flag any non-zero drop counter."*

### Multi-Tenant Data Center / Cloud Provider
- *"List all VRFs across all Nexus devices. For each VRF, show the associated L3 VNI, tenant name (from description field), route count, and whether the VRF is configured on both spines and all leaves. Flag any VRF missing from any device — a missing VRF on a leaf creates a traffic black hole for that tenant."*

### Hyperconverged / VMware vSAN
- *"Show all port-channels and individual ports configured with Jumbo MTU (9000+ bytes) on `DC-LEAF-101` through `DC-LEAF-106`. Confirm MTU consistency across all vSAN-carrying interfaces — MTU mismatches cause silent packet drops for vSAN storage traffic."*

### Service Provider / Internet Exchange
- *"Run `show bgp ipv4 unicast summary vrf default` on all border leaf switches simultaneously. Show all eBGP peers, their AS numbers, state, uptime, and prefix counts. Flag any eBGP peer that is not established or has a prefix count significantly below its historical baseline."*

### DevOps / CI-CD Infrastructure
- *"List all VLANs and VXLANs provisioned on the development fabric leaf switches. Compare against the production fabric leaf switches using parallel execution — flag any VLAN or VNI present in production but absent in development, or vice versa. This helps maintain dev/prod infrastructure parity."*

***

## 🔁 Cross-Ecosystem / Multi-MCP Prompts

The NX-OS MCP server is the **data center switching ground truth** in the suite — where ACI shows the policy model and FMC shows the perimeter policy, NX-OS shows what Nexus hardware is *actually doing* at the forwarding plane. [github](https://github.com/cpaggen/Cisco_NXOS-MCP_Server)

***

### 🔗 NX-OS + ACI — Policy Model vs. Device Reality

45. **"ACI reports that leaf `101` has a fault on BD `App-BD`. Run `show vlan` and `show interface nve1` on `DC-LEAF-101` via the NX-OS MCP server to confirm the VLAN and VNI associated with that BD are actually instantiated in hardware. Sometimes ACI's management plane reports faults before the data plane reflects the issue."**

46. **"ACI's EPG `DB-EPG` should be present on specific leaf ports. Use the NX-OS MCP server to run `show vlan brief` and `show port-channel summary` on those leaves — confirm the VLAN associated with `DB-EPG` is active and the port-channel carrying it is fully bundled. Cross-reference ACI's static binding configuration with the actual hardware state."**

***

### 🔗 NX-OS + FMC — Data Center East-West and Perimeter Firewall

47. **"FMC's contract deny logs show drops between two DC subnets. Run `show ip route` and `show forwarding ipv4 route` on the relevant Nexus leaf switches to confirm the forwarding entries are correct. Is this a routing issue (wrong next-hop in FIB) or a firewall policy issue? Isolate which layer is causing the drop."**

48. **"We are deploying a new FTD firewall service node in the data center. Run `show vpc summary` and `show interface port-channel` on the adjacent Nexus leaves to confirm the service node's port-channel is correctly formed, consistent, and passing traffic before we update FMC policy to redirect flows through it."**

***

### 🔗 NX-OS + ISE — Endpoint Authentication at DC Access Layer

49. **"ISE reports a successful authentication for MAC `b8:27:eb:4f:2a:11` on a Nexus access switch. Run `show mac address-table address b827.eb4f.2a11` on `DC-ACCESS-SW-01` to confirm the MAC is learned on the expected port and VLAN. Then run `show authentication sessions interface` for that port — confirm the ISE-assigned VLAN and dACL are applied in the NX-OS session table."**

***

### 🔗 NX-OS + Catalyst Center — Campus-to-DC Border Handoff

50. **"Catalyst Center is showing a path issue between a campus subnet and a data center server. Use the NX-OS MCP server to run `show ip route <campus-subnet>` on the DC border leaf switches — confirm the campus prefix is being correctly learned via the BGP handoff between Catalyst Center-managed campus core and the Nexus border leaves. Show the full AS path and next-hop."**

***

### 🔗 NX-OS + ThousandEyes — VXLAN Path Validation

51. **"ThousandEyes is showing packet loss between an enterprise agent in the data center and a cloud endpoint. Run `show forwarding ipv4 route <destination>` on `DC-BORDER-LEAF-01` to confirm the correct exit path is in the hardware FIB. Also run `show nve peers` to confirm the VXLAN tunnel to the cloud gateway VTEP is UP and not experiencing packet loss at the overlay level."**

***

### 🔗 NX-OS + Splunk — Syslog & Event History Correlation

52. **"Splunk ingested a burst of NX-OS syslog messages from `DC-LEAF-103` at 02:15 AM — `%BGP-3-NOTIFICATION` events indicating BGP session resets. Run `show bgp event-history errors` and `show bgp event-history notifications` on that device via the NX-OS MCP server. Compare the device-local event history against what Splunk captured — did all BGP events make it to Splunk or were any dropped during the burst?"**

***

### 🔗 NX-OS + ACI + FMC + ISE — Full Data Center Ground Truth Sweep

53. **"We have a P1 outage: workloads in `PROD-Tenant` cannot reach external services. Orchestrate a full ground truth sweep: (1) NX-OS MCP — run `show bgp summary`, `show nve peers`, and `show vpc summary` across all spines and leaves in parallel to confirm fabric health; (2) ACI MCP — check active faults in `PROD-Tenant` and verify contract deny logs for the affected EPGs; (3) FMC MCP — confirm the north-south access policy has no unexpected block rules for `PROD-Tenant` subnets; (4) ISE MCP — confirm no policy change has re-classified the affected endpoints. Produce a ranked incident brief with device-level evidence."**

***

## Prompt Engineering Tips for NX-OS MCP

| Principle | Guidance |
|---|---|
| **Leverage parallel execution** | The NX-OS MCP's killer feature is running commands across multiple Nexus switches simultaneously — always use `run_nxos_commands_parallel` for fleet-wide health checks  [lobehub](https://lobehub.com/mcp/sdntechforum-nxos-mcp) |
| **Request structured JSON output** | NX-API supports JSON output for most `show` commands — request `output_format=json` for prompts where data will be processed or compared programmatically  |
| **Scope write operations to single device** | Config push and `run_config_command` should always be scoped to a single, named device with explicit confirmation — never run write operations in parallel across a fleet |
| **Always check vPC before interface changes** | Before modifying any port-channel or member interface on a leaf, run `show vpc summary` — modifying a vPC member without understanding consistency state can cause traffic loss |
| **Use event-history for BGP/OSPF forensics** | For routing protocol incidents, `show bgp event-history` and `show ospf event-history` on NX-OS contain far more detail than standard `show logging` — always use these for protocol-level RCA |
| **VXLAN troubleshooting sequence** | For VXLAN issues, follow this order: (1) underlay reachability (`show ip route loopback`), (2) BGP EVPN sessions (`show bgp l2vpn evpn summary`), (3) NVE peer state (`show nve peers`), (4) VNI programming (`show vxlan`) — the NX-OS MCP can automate all four steps in one prompt |
| **Complement ACI with NX-OS** | ACI's management plane and NX-OS's data plane sometimes diverge during faults — always cross-check ACI object state with NX-OS hardware state for any production issue |

***

The NX-OS MCP server is the **data center fabric's hardware-level truth engine**. While ACI provides the policy intent and APIC health model, NX-OS exposes the actual forwarding state that underlies it — FIB entries, NVE peer states, vPC consistency checks, and real-time interface counters that APIC's management plane abstracts away. In any DC incident, the NX-OS server is the definitive final check that confirms whether the control plane's intent has been correctly programmed into the data plane hardware. [lobehub](https://lobehub.com/mcp/sdntechforum-nxos-mcp)
