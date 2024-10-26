import os
from netmiko import ConnectHandler
import configparser


class CiscoSwitch:
    def __init__(self):
        __vlanname = None
        # Configparser
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'config.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
            os.path.join(config_folder, 'ciscoconfig.cfg')
        ]      
        self.config.read(config_files)
        # Auth cisco
        self.device = {
            'device_type': 'cisco_ios',
            'host': self.config.get('Cisco', 'switchIP'),
            'username': self.config.get('Cisco', 'username'),
            'password': self.config.get('Cisco', 'password'),
        }
        self.connect()


    def connect(self):
        try:
            self.connection = ConnectHandler(**self.device)
            print(f"\nSuccessfully connected to {self.device['host']} (Cisco)")
        except Exception as e:
            print(f"Failed to connect to {self.device['host']}: {e}")


    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
            print(f"Disconnected from {self.device['host']} (Cisco)\n")


    def check_for_vlan_id(self, vlan_id):
        if not self.connection:
            print("Not connected to any device.")
            return

        try:
            output = self.connection.send_command('show vlan brief')
            #print(output)
            if f" {vlan_id} " in output or f"\n{vlan_id} " in output:
                print(f"[\u2713] VLAN {vlan_id} is present on the switch.")
            else:
                print(f"[X] VLAN {vlan_id} is NOT present on the switch.")
        except Exception as e:
            print(f"Failed to execute command on {self.device['host']}: {e}")


    def add_vlan_id(self):
        if not self.connection:
            print("Not connected to any device.")
            return
        
        for section in self.config.sections():
            if section.startswith('vlanInfo'): 
                self.__vlanname = f"{self.config.get(section, 'domain')}_{self.config.get(section, 'vlanID')}"

                # Check if string is more then 16 char do to cisco limit on name in vlan
                
                if len(self.__vlanname) > 16:
                    print("more then 16 char")
                    self.__vlanname = self.__vlanname[:16] + f"_{self.config.get(section, 'vlanID')}" 
                    #print(len(self.__vlanname))
                    
                vlan_id_conf = self.config.get(section, "vlanID").split(',') 
                vlan_id_list = []
                #print(vlan_id_conf)
                
                for vlan_ids in vlan_id_conf:
                    vlan_id_list.append(vlan_ids)
                #print(vlan_id_list)
                
                try:
                    for vlan_id in vlan_id_list:
                        self.connection.enable()
                        self.connection.config_mode()
                        commands = [
                            f'vlan {vlan_id}',
                            f'name {self.__vlanname}'
                        ]
                        output = self.connection.send_config_set(commands)
                        self.connection.save_config()
                        print(f"[\u2713] VLAN {self.config.get(section, 'vlanID')} with name '{self.__vlanname}' added successfully.")
                        #print(output)
                    
                except Exception as e:
                    print(f"[X] Failed to add VLAN {self.config.get(section, 'vlanID')} on {self.device['host']}: {e}")


    def delete_vlan_id(self):
        if not self.connection:
            print("Not connected to any device.")
            return
        
        for section in self.config.sections():
            if section.startswith('vlanInfo'):
                vlan_id_conf = self.config.get(section, "vlanID").split(',') 
                vlan_id_list = []
                #print(vlan_id_conf)
                
                for vlan_ids in vlan_id_conf:
                    vlan_id_list.append(vlan_ids)
                #print(vlan_id_list)

                try:
                    for vlan_id in vlan_id_list:
                        self.connection.enable()
                        self.connection.config_mode()
                        commands = [
                            f'no vlan {vlan_id}'
                        ]
                        output = self.connection.send_config_set(commands)
                        self.connection.save_config()
                        print(f"[\u2713] VLAN {vlan_id} removed successfully.")
                        #print(output)
                except Exception as e:
                    print(f"[X] Failed to remove VLAN {vlan_id} on {self.device['host']}: {e}")
      
            
    def some_new(self):
        pass
