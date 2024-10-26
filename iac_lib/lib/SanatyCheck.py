import configparser
import os
import ipaddress
import sqlite3
from lib import cisco

class CheckConfig:
    def __init__(self, db_path: str) -> None:
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        print(config_folder)
        config_files = [
            os.path.join(config_folder, 'config.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
            os.path.join(config_folder, 'forticonfig.cfg'),
            os.path.join(config_folder, 'ciscoconfig.cfg'),
            os.path.join(config_folder, 'vmwareconfig.cfg'),
        ]
        self.config.read(config_files)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cisco = cisco.CiscoSwitch(self.config.get('Cisco', 'switchIP'), 
                                       self.config.get('Cisco', 'username'), 
                                       self.config.get('Cisco', 'password'))


    def vmware_check(self):
        required_params = ['vcenter', 'username', 'password', 'ca']
        for param in required_params:
            if self.config.get('VmWare', param) == '':
                raise Exception(f"[X] VmWare {param} not defined in the config file")
        print(f"[\u2713] VmWare Check is OK!")


    def network_check(self):
        required_params = ['defaultGW', 'subnet', 'vlanId']
        for param in required_params:
            if self.config.get('Network', param) == '':
                raise Exception(f"[X] Network {param} not defined in the config file")
        print("[\u2713] Network Check is OK!")


    def create_vm_check(self):
        required_params = ['hostName', 'hostIP', 'vCPU', 'vmem', 'nics', 'powerStatus']
        for param in required_params:
            if self.config.get('CreateVm', param) == '':
                raise Exception(f"[X] CreateVm {param} not defined in the config file")
        print("[\u2713] CreateVm Check is OK!")


    def cisco_check(self):
        required_params = ['username', 'password', 'switchIP', 'port']
        for param in required_params:
            if self.config.get('Cisco', param) == '':
                raise Exception(f"[X] Cisco {param} not defined in the config file")
        print("[\u2713] Cisco Check is OK!")


    def fortigate_check(self):
        required_params = ['username', 'password', 'mgmtIP', 'port']
        for param in required_params:
            if self.config.get('Fortigate', param) == '':
                raise Exception(f"[X] Fortigate {param} not defined in the config file")
        print("[\u2713] Fortigate Check is OK!")


    def subnet_check(self):
        # Check subnet from config file vs database.db
        # This is the subnet from the config file
        subnet_config = self.config.get('Network', 'subnet')
        ipadr1 = ipaddress.ip_network(subnet_config)

        # Look though the DB
        # TODO Make sure the code breake if there is a overlap!!
        self.cursor.execute('SELECT subnet FROM network_info')
        rows = self.cursor.fetchall()
        for row in rows:
            subnet_str = row[0]
            try:
                ipadr2 = ipaddress.ip_network(subnet_str)
                if ipadr1.overlaps(ipadr2):
                    # Breake code here ----
                    print(f"Overlap found: {subnet_str} and {ipadr1}")
                else:
                    print(f"No overlap: {subnet_str}")
            except ValueError as e:
                print(f"Invalid subnet {subnet_str}: {e}")

        print("[\u2713] Subnet overlap Check is OK!")


    def vlanid_check(self):
        self.cisco.connect()
        self.cisco.check_for_vlan_id(self.config.get('Network', 'vlanId'))
        self.cisco.disconnect()
