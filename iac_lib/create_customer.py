import lib.fortigate as FortiGate
import lib.vmware as VMware
import lib.cisco as Cisco


if __name__ == "__main__":

    forti = FortiGate.FortiGate()
    forti.create_address()
    forti.create_interface(addr_obj=True)
    forti.create_policy()
    # Fortigate VPN Section
    forti.create_ldap_server()
    forti.create_user_group()
    forti.create_address_range()
    forti.create_ssl_vpn_portal()
    forti.add_tunnel_pools()
    forti.add_groups_and_portals()
    forti.create_vpn_policy()
    
    cisco = Cisco.CiscoSwitch()
    cisco.add_vlan_id()
    cisco.disconnect()
    
    vm = VMware.VMware()
    vm.create_dvs()
    vm.create_dv_portgroup()
    vm.disconnect()
    