import requests
import urllib3
import warnings
import configparser
import json
import pprint
import ipaddress
import os
pp = pprint.PrettyPrinter(indent=4)

class FortiGate:
    def __init__(self) -> None:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # Configparser
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'config.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
            os.path.join(config_folder, 'forticonfig.cfg'),
            os.path.join(config_folder, 'vpnconfig.cfg'),
            os.path.join(config_folder, 'hostconfig.cfg'),
        ]      
        self.config.read(config_files)
        # Fortigate auth
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {self.config.get("Fortigate", "token")}'
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['Accept'] = 'application/json' 
        # For testing status code  
        self.mgmt_ip = self.config.get('Fortigate', 'mgmtIP')
        self.port = self.config.get('Fortigate', 'port')

        res = self.session.get(f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/system/status', verify=False)
        print(f"Status Code Fortigate: {res.status_code}")
        if res.status_code != 200:
            raise Exception(f"Could not login to Fortigate: {res.text}")
            
            
    def create_address(self):
        # Create address if you need addres without interface just leave addressInterface empty in forticonfig
        for section in self.config.sections():
            if section.startswith('Fortiaddress'):
                address_name = self.config.get(section, "addressName")
                address_type_sub = self.config.get(section, "addressType")
                address_subnet = self.config.get(section, "addressSubnet")
                address_interface = self.config.get(section, "addressInterface")
                address_data = {
                    'name': address_name,
                    'type': address_type_sub,
                    'subnet': address_subnet,
                    'associated-interface': address_interface 
                }
                #print(address_interface)
        
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/address?vdom=root'
                response = self.session.post(endpoint, data=json.dumps(address_data), verify=False)
                if response.status_code == 200:
                    print(f"Address {address_name} created successfully.")
                else:
                    print(f"Failed to create address {address_name}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
                    
    
    def create_address_range(self):
        # Create address if you need address without interface, just leave addressInterface empty in forticonfig
        for section in self.config.sections():
            if section.startswith('Fortirangeaddress'):
                address_name = self.config.get(section, "addressName")
                address_type_sub = self.config.get(section, "addressType")
                start_ip = self.config.get(section, "startIP")
                end_ip = self.config.get(section, "endIP")
                address_interface = self.config.get(section, "addressInterface")
                
                address_data = {
                    'name': address_name,
                    'type': 'iprange',
                    'start-ip': start_ip,
                    'end-ip': end_ip,
                    'associated-interface': address_interface
                }
                
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/address?vdom=root'
                response = self.session.post(endpoint, data=json.dumps(address_data), verify=False)
                
                if response.status_code == 200:
                    print(f"Address range {address_name} created successfully.")
                else:
                    print(f"Failed to create address range {address_name}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
                
            
    def create_address_manual(self, name, subnet, address_type, interface=None,):
        if interface == None:
            address_data = {
            'name': name,
            'subnet': subnet,
            'type': address_type,
        }
        else:
            address_data = {
                'name': name,
                'type': address_type,
                'subnet': subnet,
                'associated-interface': interface 
            }

        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/address?vdom=root'
        response = self.session.post(endpoint, data=json.dumps(address_data), verify=False)
        if response.status_code == 200:
            print(f"Address {name} created successfully.")
        else:
            print("Failed to create address (Interface_Subnet).")
            print("Status code:", response.status_code)
            print("Response:", response.text)
        
    
    def get_address_info(self, name):
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/address/{name}?vdom=root'
        response = self.session.get(endpoint, verify=False)
        
        if response.status_code == 200:
            address_info = response.json()
            print("Address information retrieved successfully.")
            print(json.dumps(address_info, indent=4))
        else:
            print("Failed to retrieve address information.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
     

    def delete_address(self, name):
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/address/{name}?vdom=root'
        response = self.session.delete(endpoint, verify=False)
        if response.status_code == 200:
            print("Adresse is delted successfully.")
        else:
            print(f"Failed to delete address {name}.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
            
            
    def delete_address_config(self):
        for section in self.config.sections():
            if section.startswith('Fortiaddress'):
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/address/{self.config.get(section, "addressName")}?vdom=root'
                response = self.session.delete(endpoint, verify=False)
                if response.status_code == 200:
                    print(f"Adresse {self.config.get(section, "addressName")} is delted successfully.")
                else:
                    print(f"Failed to delete address {self.config.get(section, "addressName")}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
                    
    
    def delete_address_range_config(self):
        for section in self.config.sections():
            if section.startswith('Fortirangeaddress'):
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/address/{self.config.get(section, "addressName")}?vdom=root'
                response = self.session.delete(endpoint, verify=False)
                if response.status_code == 200:
                    print(f"Adresse {self.config.get(section, "addressName")} is delted successfully.")
                else:
                    print(f"Failed to delete address {self.config.get(section, "addressName")}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)


    def get_policy_by_id(self, policy_id):
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/policy/{policy_id}?vdom=root'
        response = self.session.get(endpoint, verify=False)
        if response.status_code == 200:
            res_json = response.json()
            print(json.dumps(res_json, indent=4))
        else:
            print(f"Failed to get policy ID: {policy_id}.")
            print("Status code:", response.status_code)
            print("Response:", response.text)        
    
    
    def get_policy_by_name(self, policy_name):
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/policy?vdom=root&filter=name=={policy_name}'
        response = self.session.get(endpoint, verify=False)
        if response.status_code == 200:
            res_json = response.json()
            # Assuming the API returns a list of policies, even if there's only one match
            if res_json['results']:
                #print(json.dumps(res_json['results'][0], indent=4))
                #print(json.dumps(res_json['results'][0]['policyid']))
                # Return policy ID
                return json.dumps(res_json['results'][0]['policyid'])
            else:
                print(f"No policy found with name: {policy_name}.")
        else:
            print(f"Failed to get policy with name: {policy_name}.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
    
            
    def create_policy(self):
        # Endpoint for creating a new policy
        for section in self.config.sections():
            if section.startswith('Fortipolicy'):
                policy_name = self.config.get(section, "policyName")
                source_int = self.config.get(section, "sourceInterface")
                destination_int = self.config.get(section, "destinationInterface")
                source_address = self.config.get(section, "sourceAdresse")
                destination_address = self.config.get(section, "destinationAddress")
                services = self.config.get(section, "services")
                nat = self.config.get(section, "nat")
                comment = self.config.get(section, "comment")
                policy_data = {
                    "name": policy_name,
                    "srcintf": [{"name": source_int}],
                    "dstintf": [{"name": destination_int}],
                    "srcaddr": [{"name": source_address}],
                    "dstaddr": [{"name": destination_address}],
                    "service": [{"name": services}],
                    "schedule": "always",
                    "nat": nat,
                    "action": "accept",
                    "comments": comment
                    }
                #pp.pprint(policy_data)
        
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/policy?vdom=root'
                response = self.session.post(endpoint, data=json.dumps(policy_data), verify=False)

                #print("Response:", response.text)
                response_data = response.json()
                mkey = response_data.get("mkey")
                #print(mkey)
                
                # Handle response
                if response.status_code == 200:
                    print(f"Policy ID: {mkey} created successfully.")
                else:
                    print(f"Failed to create policy {policy_name}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
    
    
    def create_policy_manual(self, name, srcintf, dstintf, srcaddr, dstaddr, service, nat, comments):
        # Endpoint for creating a new policy
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/policy?vdom=root'
        policy_data = {
            "name": name,
            "srcintf": [{"name": srcintf}],
            "dstintf": [{"name": dstintf}],
            "srcaddr": [{"name": srcaddr}],
            "dstaddr": [{"name": dstaddr}],
            "service": [{"name": service}],
            "schedule": "always",
            "nat": nat,
            "action": "accept",
            "comments": comments
        }

        response = self.session.post(endpoint, data=json.dumps(policy_data), verify=False)
        response_data = response.json()
        mkey = response_data.get("mkey")
        print(mkey)
        
        # Handle response
        if response.status_code == 200:
            print(f"Policy ID: {mkey} created successfully.")
        else:
            print(f"Failed to create policy {name}.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
        
    
    def delete_policy(self, policy_id):
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/policy/{policy_id}?vdom=root'
        response = self.session.delete(endpoint, verify=False)
        if response.status_code == 200:
            print(f"Policy {policy_id} is delted successfully.")
        else:
            print("Failed to delete Policy.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
            
            
    def delete_policy_config(self):
        for section in self.config.sections():
            if section.startswith('Fortipolicy'):
                get_policy_id = self.get_policy_by_name(self.config.get(section, "policyName"))
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/policy/{get_policy_id}?vdom=root'
                response = self.session.delete(endpoint, verify=False)
                if response.status_code == 200:
                    print(f"Policy {self.config.get(section, "policyName")} is delted successfully.")
                else:
                    print("Failed to delete Policy.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)


    def get_service(self, service_name):
        # URL is fucked !!!
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall.service/custom/{service_name}?vdom=root'
        response = self.session.get(endpoint, verify=False)
        if response.status_code == 200:
            res_json = response.json()
            print(json.dumps(res_json, indent=4))
        else:
            print(f"Failed to get policy ID: {service_name}.")
            print("Status code:", response.status_code)
            print("Response:", response.text)   
    
    
    def create_service(self):
        # OBS protocol is ONLY TCP or IP no UDP 
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall.service/custom?vdom=root'
        for section in self.config.sections():
            if section.startswith('Fortiservice'):
                service_name = self.config.get(section, "serviceName")
                protocol = self.config.get(section, "protocol").upper()
                tcp_portrange = self.config.get(section, "tcpPortrange")
                udp_portrange = self.config.get(section, "udpPortrange")
                category = self.config.get(section, "category")
                comment = self.config.get(section, "comment")
        
                service_data = {
                    "name": service_name,
                    "protocol": protocol,
                    "tcp-portrange": tcp_portrange,
                    "udp-portrange": udp_portrange,
                    "category": category,
                    "comment": comment,
                    }
                response = self.session.post(endpoint, data=json.dumps(service_data), verify=False)
                # Handle response
                response_data = response.json()
                #print(response.text)
                mkey = response_data.get("mkey")
                #print(mkey)
                if response.status_code == 200:
                    print(f"Service Name: '{mkey}' created successfully.")
                else:
                    print("Failed to create service.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
        
    
    def create_service_manual(self, name, protocol, category="", comment="", tcp_portrange="",  udp_portrange=""):
        """
        Posts a new service to the FortiGate firewall.

        Args:
            name (str): The name of the service.
            protocol (str): The protocol used by the service (e.g., "TCP", "IP").
            tcp_portrange (str): The TCP Port range (e.g., 8080-8080). Defaults to an empty string 
            udp_portrange (str): The TCP Port range (e.g., 8080-8080). Defaults to an empty string
            category (str): The category of the service. (e.g. Network Services) if left empty defaults to Uncategorized
            comment (str, optional): A comment or description for the service. Defaults to an empty string.

        Returns:
            None
        """
        
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall.service/custom?vdom=root'
        protocol = protocol.upper()
        service_data = {
            "name": name,
            "protocol": protocol,
            "tcp-portrange": tcp_portrange,
            "udp-portrange": udp_portrange,
            "category": category,
            "comment": comment,
            }
        print(service_data)
        response = self.session.post(endpoint, data=json.dumps(service_data), verify=False)
        # Handle response
        response_data = response.json()
        #print(response.text)
        mkey = response_data.get("mkey")
        #print(mkey)
        if response.status_code == 200:
            print(f"Service Name: '{mkey}' created successfully.")
        else:
            print("Failed to create service.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
    
    
    def delete_service(self, service_name):
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall.service/custom/{service_name}?vdom=root'
        response = self.session.delete(endpoint, verify=False)
        if response.status_code == 200:
            print(f"Service {service_name} is delted successfully.")
        else:
            print(f"Failed to delete Service {service_name}.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
    
    
    def get_interface(self, interface_name):
        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/system/interface/{interface_name}?vdom=root'
        response = self.session.get(endpoint, verify=False)
        
        if response.status_code == 200:
            res_json = response.json()
            print(json.dumps(res_json, indent=4))
        else:
            print(f"Failed to get interface: {interface_name}.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
    
    
    def create_interface(self, addr_obj = False):
        # Create vlan interface if addr_obj = True it creates matching address
        for section in self.config.sections():
            if section.startswith('Fortiinterface'):
                interface_name = self.config.get(section, "interfaceName")
                vdom = self.config.get(section, "vdom")
                vlanid = self.config.get(section, "vlanID")
                allow_access = self.config.get(section, "allowAccess")
                role = self.config.get(section, "role")
                interface = self.config.get(section, "interface")
                ip_adr = self.config.get(section, "ip")
                int_type = self.config.get(section, "type")
                description = self.config.get(section, "description")
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/system/interface?vdom=root'
                vlan_data = {
                    "name": interface_name,
                    "vdom": vdom,
                    "vlanid": vlanid,
                    "allowaccess": allow_access,
                    "role": role,
                    "interface": interface,
                    "ip": ip_adr,
                    "type": int_type,
                    "description": description,
                }
        
                response = self.session.post(endpoint, data=json.dumps(vlan_data), verify=False)
                # Handle response
                response_data = response.json()
                #print(response.text)
                mkey = response_data.get("mkey")
                #print(mkey)
                if response.status_code == 200:
                    print(f"Interface: '{mkey}' created successfully.")
                    if addr_obj:
                        addr_name = f"{interface_name} address"
                        ip_address, sub_address = ip_adr.split()
                        self.network = ipaddress.IPv4Network(f"{ip_address}/{sub_address}", strict=False)
                        first_ip_no_sub = self.network.network_address
                        first_ip_with_sub = f"{first_ip_no_sub} {sub_address}"
                        
                        addr_type = "ipmask"
                        
                        print(first_ip_with_sub)
                        self.create_address_manual(addr_name, first_ip_with_sub, addr_type, interface_name)
                else:
                    print(f"Failed to create interface {interface_name}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
    
    
    def delete_interface(self, interface_name, with_address = False):
        # Importen if there is a address object, set the with_address flag to True, )
        if with_address:
            # Remove address first 
            int_addr = f"{interface_name} address"
            self.delete_address(name=int_addr)
            endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/system/interface/{interface_name}?vdom=root'
            response = self.session.delete(endpoint, verify=False)
            if response.status_code == 200:
                print(f"Service {interface_name} is delted successfully.")
            else:
                print(f"Failed to delete Interface {interface_name}.")
                print("Status code:", response.status_code)
                print("Response:", response.text)
        else:
            endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/system/interface/{interface_name}?vdom=root'
            response = self.session.delete(endpoint, verify=False)
            if response.status_code == 200:
                print(f"Service {interface_name} is delted successfully.")
            else:
                print(f"Failed to delete Interface {interface_name}.")
                print("Status code:", response.status_code)
                print("Response:", response.text)
        
        
    def delete_interface_config(self, with_address = False):
        # Use with_address if the interface is build with a address object
        if with_address:
            for section in self.config.sections():
                if section.startswith('Fortiinterface'):
                    int_addr = f"{self.config.get(section, "interfaceName")} address"
                    self.delete_address(name=int_addr)
                    endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/system/interface/{self.config.get(section, "interfaceName")}?vdom=root'
                    response = self.session.delete(endpoint, verify=False)
                    if response.status_code == 200:
                        print(f"Service {self.config.get(section, "interfaceName")} is delted successfully.")
                    else:
                        print(f"Failed to delete interface {int_addr}.")
                        print("Status code:", response.status_code)
                        print("Response:", response.text)
        else:
            for section in self.config.sections():
                if section.startswith('Fortiinterface'):
                    endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/system/interface/{self.config.get(section, "interfaceName")}?vdom=root'
                    response = self.session.delete(endpoint, verify=False)
                    if response.status_code == 200:
                        print(f"Service {self.config.get(section, "interfaceName")} is delted successfully.")
                    else:
                        print(f"Failed to delete interface {self.config.get(section, "interfaceName")}.")
                        print("Status code:", response.status_code)
                        print("Response:", response.text)
                        
                        
    def create_ldap_server(self):
        # Create an LDAP server configuration
        ldap_dn = self.config.get('Customerinfo', "uniqueId")
        for section in self.config.sections():
            if section.startswith('Fortildap'):
                ldap_name = self.config.get(section, "name")
                ldap_server = self.config.get(section, "server")
                ldap_cnid = self.config.get(section, "cnid")
                #ldap_dn = self.config.get(section, "dn")
                ldap_pass = self.config.get(section, "password")
                ldap_user = self.config.get(section, "username")

                ldap_data = {
                    'name': ldap_name,
                    'server': ldap_server,
                    'secondary-server': "",
                    'tertiary-server': "",
                    'server-identity-check': 'enable',
                    'source-ip': '',
                    'source-port': 0,
                    'cnid': ldap_cnid,
                    'dn': f'ou={ldap_dn},ou=customers,dc=cloudcubes,dc=gg',
                    'type': 'regular',
                    'two-factor': 'disable',
                    'username': ldap_user,
                    'password': ldap_pass,
                    'group-member-check': 'user-attr',
                    'group-search-base': '',
                    'group-object-filter': '(&(objectcategory=group)(member=*))',
                    'secure': 'disable',
                    'ssl-min-proto-version': 'default',
                    'port': 389,
                    'password-expiry-warning': 'disable',
                    'password-renewal': 'disable',
                    'member-attr': 'memberOf',
                    'account-key-processing': 'same',
                    'account-key-cert-field': 'othername',
                    'account-key-filter': '(&(userPrincipalName=%s)(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))',
                    'obtain-user-info': 'enable',
                    'interface-select-method': 'auto',
                    'interface': '',
                    'antiphish': 'disable',
                    'password-attr': 'userPassword'
                }

                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/user/ldap?vdom=root'
                response = self.session.post(endpoint, data=json.dumps(ldap_data), verify=False)
                if response.status_code == 200:
                    print(f"LDAP server {ldap_name} created successfully.")
                else:
                    print(f"Failed to create LDAP server {ldap_name}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
      
                    
    def delete_ldap_server(self):
        # Remove an LDAP server configuration        
        for section in self.config.sections():
            if section.startswith('Fortildap'):
                ldap_server_name = self.config.get(section, "name")

                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/user/ldap/{ldap_server_name}?vdom=root'
                
                response = self.session.delete(endpoint, verify=False)
                if response.status_code == 200:
                    print(f"LDAP server {ldap_server_name} removed successfully.")
                else:
                    print(f"Failed to remove LDAP server {ldap_server_name}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
            
    
    def create_user_group(self):
        # Create Group with LDAP server in it
        for section in self.config.sections():
            if section.startswith('Fortildap'):
                group_name = self.config.get(section, "groupName")
                ldap_server_name = self.config.get(section, "name")      
        
                group_data = {
                    'name': group_name,
                    'id': 0,
                    'group-type': 'firewall',
                    'authtimeout': 0,
                    'auth-concurrent-override': 'disable',
                    'auth-concurrent-value': 0,
                    'member': [
                        {
                            'name': ldap_server_name  
                        }
                    ],
                    'match': [],
                    'user-id': 'email',
                    'password': 'auto-generate',
                    'user-name': 'disable',
                    'sponsor': 'optional',
                    'company': 'optional',
                    'email': 'enable',
                    'mobile-phone': 'disable',
                    'sms-server': 'fortiguard',
                    'sms-custom-server': '',
                    'expire-type': 'immediately',
                    'expire': 14400,
                    'max-accounts': 0,
                    'multiple-guest-add': 'disable',
                    'guest': []
                }

                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/user/group?vdom=root'
                response = self.session.post(endpoint, data=json.dumps(group_data), verify=False)
                
                if response.status_code == 200:
                    print(f"User group {group_name} created successfully with LDAP server {ldap_server_name}.")
                else:
                    print(f"Failed to create user group {group_name}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
       
                    
    def delete_user_group(self):
        # Remove Group with the specified name
        for section in self.config.sections():
            if section.startswith('Fortildap'):
                group_name = self.config.get(section, "groupName")
                
                # FortiGate API endpoint for deleting user group
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/user/group/{group_name}?vdom=root'
                
                response = self.session.delete(endpoint, verify=False)
                
                if response.status_code == 200:
                    print(f"User group {group_name} removed successfully.")
                else:
                    print(f"Failed to remove user group {group_name}.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)
    
            
    def create_ssl_vpn_portal(self):
        # Add SSL-VPN Portal
        portal_name = self.config.get("Fortiportal-vpn", "portalName")
        ip_pool_name = self.config.get("Fortirangeaddress-vpn", "addressName")
        
        ssl_vpn_data = {
            "name": portal_name,
            "tunnel-mode": "enable",
            "ip-mode": "range",
            "dhcp-ip-overlap": "use-new",
            "auto-connect": "disable",
            "keep-alive": "disable",
            "save-password": "disable",
            "ip-pools": [
                {
                    "name": ip_pool_name
                }
            ],
            "exclusive-routing": "disable",
            "service-restriction": "disable",
            "split-tunneling": "disable",
            "split-tunneling-routing-negate": "disable",
            "split-tunneling-routing-address": [],
            "dns-server1": "0.0.0.0",
            "dns-server2": "0.0.0.0",
            "wins-server1": "0.0.0.0",
            "wins-server2": "0.0.0.0",
            "client-src-range": "disable",
            "web-mode": "disable",
            "display-bookmark": "enable",
            "user-bookmark": "enable",
            "allow-user-access": "web ftp smb sftp telnet ssh vnc rdp ping",
            "default-protocol": "web",
            "bookmark-group": [
                {
                    "name": "gui-bookmarks",
                    "bookmarks": []
                }
            ],
            "display-connection-tools": "enable",
            "display-history": "enable",
            "display-status": "enable",
            "heading": "SSL-VPN Portal",
            "theme": "security-fabric",
            "forticlient-download": "disable",
            "skip-check-for-unsupported-os": "enable",
            "skip-check-for-browser": "enable",
            "hide-sso-credential": "enable"
        }

        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/vpn.ssl.web/portal?vdom=root'
        response = self.session.post(endpoint, data=json.dumps(ssl_vpn_data), verify=False)

        if response.status_code == 200 or response.status_code == 201:
            print(f"SSL VPN portal '{portal_name}' created successfully with IP pool '{ip_pool_name}'.")
        else:
            print(f"Failed to create SSL VPN portal '{portal_name}'.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
            
    
    def delete_ssl_vpn_portal(self):
        portal_name = self.config.get("Fortiportal-vpn", "portalName")

        endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/vpn.ssl.web/portal/{portal_name}?vdom=root'
        
        response = self.session.delete(endpoint, verify=False)

        if response.status_code == 200:
            print(f"SSL VPN portal '{portal_name}' deleted successfully.")
        elif response.status_code == 404:
            print(f"SSL VPN portal '{portal_name}' not found.")
        else:
            print(f"Failed to delete SSL VPN portal '{portal_name}'.")
            print("Status code:", response.status_code)
            print("Response:", response.text)
    

    def add_tunnel_pools(self, vdom="root"):
        # Add new tunnel pools to the SSL-VPN settings.
        url = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/vpn.ssl/settings'
        
        # Get the current settings first
        response = self.session.get(url, params={"vdom": vdom}, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch SSL-VPN settings: {response.text}")
        
        # Print the full response for debugging
        # print("Response JSON:", response.json())
        
        if 'results' not in response.json():
            raise Exception("The response does not contain 'results'. Response: {}".format(response.text))
        
        current_data = response.json()["results"]
        
        # Add new tunnel pools to the existing ones
        current_pools = current_data.get("tunnel-ip-pools", [])
        vpn_range = self.config.get("Fortirangeaddress-vpn", "addressName")
        new_tunnel_pools = [
            {"name": f"{vpn_range}"}
            ]
        
        # Ensure the new pools are properly formatted as dictionaries
        for pool in new_tunnel_pools:
            if isinstance(pool, dict) and "name" in pool:
                # Add q_origin_key for the new pools if not provided
                if "q_origin_key" not in pool:
                    pool["q_origin_key"] = pool["name"]
                current_pools.append(pool)
            else:
                raise ValueError(f"Invalid tunnel pool format: {pool}")
        
        updated_data = current_data
        updated_data["tunnel-ip-pools"] = current_pools
        
        update_response = self.session.put(
            url,
            params={"vdom": vdom},
            data=json.dumps(updated_data),
            verify=False
        )
        
        if update_response.status_code == 200:
            print("Tunnel pools updated successfully.")
        else:
            raise Exception(f"Failed to update tunnel pools: {update_response.text}")
        
    
    def remove_tunnel_pool_ssl_vpn(self, vdom="root"):
        url = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/vpn.ssl/settings'
        
        # Get the current SSL-VPN settings
        response = self.session.get(url, params={"vdom": vdom}, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch SSL-VPN settings: {response.text}")
        
        # Parse the response JSON
        current_data = response.json().get("results", {})
        if not current_data:
            raise Exception(f"SSL-VPN settings not found: {response.text}")
        
        # Get the current tunnel pools
        current_pools = current_data.get("tunnel-ip-pools", [])
        if not current_pools:
            print("No existing tunnel IP pools found.")
            return
        
        # Get the VPN range (addressName) from the config file
        vpn_range = self.config.get("Fortirangeaddress-vpn", "addressName")
        
        # Remove the pool that matches the VPN range from the config file
        updated_pools = [pool for pool in current_pools if pool.get("name") != vpn_range]
        
        if len(updated_pools) == len(current_pools):
            print(f"No matching tunnel pool found for '{vpn_range}'.")
            return
        
        # Update the SSL-VPN settings with the modified list of tunnel pools
        current_data["tunnel-ip-pools"] = updated_pools
        
        # Send the updated settings back to the FortiGate
        update_response = self.session.put(
            url,
            params={"vdom": vdom},
            data=json.dumps(current_data),
            verify=False
        )
        
        if update_response.status_code == 200:
            print(f"Tunnel pool '{vpn_range}' removed successfully.")
        else:
            raise Exception(f"Failed to remove tunnel pool '{vpn_range}': {update_response.text}")
            
        
    def add_groups_and_portals(self, vdom="root"):
        # Add new groups and portals to the SSL-VPN settings.
        url = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/vpn.ssl/settings'
        
        # Get the current settings first
        response = self.session.get(url, params={"vdom": vdom}, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch SSL-VPN settings: {response.text}")

        # Print the full response for debugging
        # print("Response JSON:", response.json())
        
        # Access the 'results' key
        if 'results' not in response.json():
            raise Exception("The response does not contain 'results'. Response: {}".format(response.text))
        
        current_data = response.json()["results"]
        
        # Prepare the existing authentication rules
        current_auth_rules = current_data.get("authentication-rule", [])
        vpn_group = self.config.get("Fortildap", "groupName")
        portal_name = self.config.get("Fortiportal-vpn", "portalName")
        
        new_auth_rules = [    {
        "groups": [{"name": f"{vpn_group}"}],
        "portal": {"name": f"{portal_name}"}
        },
                          ]

        # Add new authentication rules
        for rule in new_auth_rules:
            if isinstance(rule, dict) and "groups" in rule and "portal" in rule:
                # Ensure each group and portal is correctly formatted
                if isinstance(rule["portal"], dict):
                    portal_key = rule["portal"].get("q_origin_key", rule["portal"]["name"])
                    rule["portal"] = {"q_origin_key": portal_key}
                
                # Append the new rule to the current authentication rules
                current_auth_rules.append(rule)
            else:
                raise ValueError(f"Invalid authentication rule format: {rule}")

        # Prepare the updated data
        updated_data = current_data
        updated_data["authentication-rule"] = current_auth_rules

        # Send a PUT request to update the settings
        update_response = self.session.put(
            url,
            params={"vdom": vdom},
            data=json.dumps(updated_data),
            verify=False
        )
        
        if update_response.status_code == 200:
            print("Groups and portals updated successfully.")
        else:
            raise Exception(f"Failed to update groups and portals: {update_response.text}")
        
    
    def remove_group_and_portal(self, vdom="root"):
        url = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/vpn.ssl/settings'

        # Get the current SSL-VPN settings
        response = self.session.get(url, params={"vdom": vdom}, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch SSL-VPN settings: {response.text}")

        current_data = response.json().get("results", {})
        current_auth_rules = current_data.get("authentication-rule", [])

        vpn_group = self.config.get("Fortildap", "groupName")
        portal_name = self.config.get("Fortiportal-vpn", "portalName")

        # Filter out the authentication rules with the specified group and portal
        updated_auth_rules = []
        for rule in current_auth_rules:
            # Check for matching group
            group_match = any(group["name"] == vpn_group for group in rule.get("groups", []))
            
            # Check for matching portal, handling both dict and string cases
            portal = rule.get("portal")
            if isinstance(portal, dict):
                portal_match = portal.get("name") == portal_name
            elif isinstance(portal, str):
                portal_match = portal == portal_name
            else:
                portal_match = False

            # If both group and portal match, skip this rule, otherwise keep it
            if not (group_match and portal_match):
                updated_auth_rules.append(rule)

        # If no changes then return 
        if len(updated_auth_rules) == len(current_auth_rules):
            print(f"No matching group '{vpn_group}' and portal '{portal_name}' found to remove.")
            return

        # Prepare the updated data
        updated_data = current_data
        updated_data["authentication-rule"] = updated_auth_rules

        update_response = self.session.put(
            url,
            params={"vdom": vdom},
            data=json.dumps(updated_data),
            verify=False
        )

        if update_response.status_code == 200:
            print(f"Group '{vpn_group}' and portal '{portal_name}' removed successfully.")
        else:
            raise Exception(f"Failed to update SSL-VPN settings: {update_response.text}")
        
    
    def create_vpn_policy(self):
        for section in self.config.sections():
            if section.startswith('Fortivpnpolicy'):
                try:
                    # Read values from the configuration file
                    policy_name = self.config.get(section, "policyName")
                    source_int = self.config.get(section, "sourceInterface")  # Ensure this is correct
                    destination_int = self.config.get(section, "destinationInterface")
                    source_address = self.config.get(section, "sourceAddress")  # This should match your config
                    destination_address = self.config.get(section, "destinationAddress")
                    services = self.config.get(section, "services")
                    nat = self.config.get(section, "nat")
                    comment = self.config.get(section, "comment")
                    group = self.config.get(section, "groups")  # Get the single group

                    # Prepare the policy data with all necessary fields
                    policy_data = {
                        "policyid": 0,
                        "status": "enable",
                        "name": policy_name,
                        "uuid": "00000000-0000-0000-0000-000000000000",  # Placeholder for UUID
                        "srcintf": [{"name": source_int}],
                        "dstintf": [{"name": destination_int}],
                        "action": "accept",
                        "srcaddr": [{"name": source_address}],
                        "dstaddr": [{"name": destination_address}],  # Should match your working API
                        "service": [{"name": services}],  # Ensure this matches what you need
                        "schedule": {"q_origin_key": "always"},  # Match the schedule format
                        "nat": nat,
                        "comments": comment,
                        "groups": [{"name": group}],  # This is your group
                    }

                    # Define the endpoint
                    endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/policy?vdom=root'
                    
                    # Make the POST request
                    response = self.session.post(endpoint, data=json.dumps(policy_data), verify=False)

                    # Handle response
                    if response.status_code == 200:
                        response_data = response.json()
                        mkey = response_data.get("mkey", "Unknown")
                        print(f"Policy ID: {mkey} created successfully.")
                    else:
                        print(f"Failed to create VPN policy {policy_name}.")
                        print("Status code:", response.status_code)
                        print("Response:", response.text)

                except configparser.NoOptionError as e:
                    print(f"Configuration error in section '{section}': {e}")
                except Exception as e:
                    print(f"An error occurred while creating policy: {e}")
        
                  
    def delete_vpn_policy(self):
        for section in self.config.sections():
            if section.startswith('Fortivpnpolicy'):
                get_policy_id = self.get_policy_by_name(self.config.get(section, "policyName"))
                endpoint = f'https://{self.mgmt_ip}:{self.port}/api/v2/cmdb/firewall/policy/{get_policy_id}?vdom=root'
                response = self.session.delete(endpoint, verify=False)
                if response.status_code == 200:
                    print(f"Policy {self.config.get(section, "policyName")} is delted successfully.")
                else:
                    print("Failed to delete Policy.")
                    print("Status code:", response.status_code)
                    print("Response:", response.text)