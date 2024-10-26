import lib.fortigate as FortiGate
import lib.vmware as VMware
import lib.cisco as Cisco


if __name__ == "__main__":
    forti = FortiGate.FortiGate()
    
    forti.delete_vpn_policy()
    forti.remove_tunnel_pool_ssl_vpn()
    forti.remove_group_and_portal()
    forti.delete_user_group()
    forti.delete_ldap_server()
    forti.delete_ssl_vpn_portal()
    
    
    forti.delete_policy_config()
    forti.delete_address_range_config()
    forti.delete_address_config()
    forti.delete_interface_config(with_address=True)

    cisco = Cisco.CiscoSwitch()
    cisco.delete_vlan_id()
    cisco.disconnect()
    
    # vm = VMware.VMware()
    # vm.delete_portgroup()
