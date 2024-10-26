from jinja2 import  Environment, FileSystemLoader
from datetime import datetime
import configparser
import os

class Dns:
    def __init__(self) -> None:
        print(f"Current working directory: {os.getcwd()}")
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'hostconfig.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
        ]      
        self.config.read(config_files)
        self.folder = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/file_dire"
        self.sec_folder = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/file_dire_sec"
        
        # Setting up the Jinja2 environment to use the correct 'templates' directory
        template_dir = os.path.join(os.path.dirname(__file__), '../' 'templates')
        print(template_dir)
        self.env = Environment(loader=FileSystemLoader(template_dir))
    
    def create_named(self):
        # ------------------ Fuction is not in use ---------------------------------_
        data = {
            "internal_subnets": [
                "10.0.20.0/24",
                "10.0.99.0/24",
                "10.0.199.0/24",
                "172.16.0.0/16"
            ],
            "forwarders": [
                "8.8.8.8",
                "1.1.1.1"
            ],
            "include_files": [
                "/etc/bind/ged.gg.conf",
                "/etc/bind/redrum.gg.conf"
            ]
        }

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('named_template.jinja')

        output = template.render(data)
        #print(output)
        
        
    def create_zones(self):
        for_var = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
        
        # Reverse IP from hostconfig.cfg
        rev_ip = self.config.get('Customerinfo', 'network')
        parts = rev_ip.split('.')
        reversed_parts = parts[-2::-1]
        reversed_ip = '.'.join(reversed_parts)

        data = {
            "for_zone": for_var,
            "for_file": f"/etc/bind/{for_var}.for.db",
            "rev_zone": reversed_ip,
            "rev_file": f"/etc/bind/{for_var}.rev.db",
        } 
        
        # Use the environment created in the __init__ method (self.env)
        template = self.env.get_template('zones_template.jinja')

        output = template.render(data)

        file_name = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.conf"
        os.makedirs(self.folder, exist_ok=True)
        file_path = os.path.join(self.folder, file_name)
        
        with open(file=file_path, mode="w") as zone_file:
            zone_file.write(output)
        
        
    def create_sec_zones(self):
        for_var = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
        
        # Reverse IP from hostconfig.cfg
        rev_ip = self.config.get('Customerinfo', 'network')
        parts = rev_ip.split('.')
        reversed_parts = parts[-2::-1]
        reversed_ip = '.'.join(reversed_parts)

        data = {
            "for_zone":
                for_var,
            "for_file":
                f"{for_var}.for.db",
            "rev_zone": 
                reversed_ip,
            "rev_file": 
                f"{for_var}.rev.db",
        } 
        
        template = self.env.get_template('sec_zones_template.jinja')

        output = template.render(data)

        file_name = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.conf"

        os.makedirs(self.sec_folder, exist_ok=True)
        file_path = os.path.join(self.sec_folder, file_name)
        with open(file=file_path, mode="w") as zone_file:
            zone_file.write(output)
        
        
    def create_reverse(self):
        rev_var = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
        # Reverse IP from hostconfig.cfg
        rev_ip = self.config.get('Customerinfo', 'network')
        parts = rev_ip.split('.')
        reversed_parts = parts[-2::-1]
        reversed_ip = '.'.join(reversed_parts)
        # Serial stuff
        today_time = datetime.now()
        serial_number = today_time.strftime("%Y%m%d%H")
        
        data = {
            "arpa":
                f"{reversed_ip}.in-addr.arpa",
            "soa":
                f"dns01.{rev_var}. {rev_var}.",
            "serial": 
                serial_number,
            "origin":
                f"{rev_var}"
        }    
        
        template = self.env.get_template('reverse_template.jinja')

        output = template.render(data)
        
        file_name = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.rev.db"

        os.makedirs(self.folder, exist_ok=True)
        file_path = os.path.join(self.folder, file_name)
        with open(file=file_path, mode="w") as zone_file:
            zone_file.write(output)
        #print(output)
        
        
    def create_forward(self):
        for_var = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
        
        today_time = datetime.now()
        serial_number = today_time.strftime("%Y%m%d%H")
        
        data = {
            "origin":
                for_var,
            "soa":
                f"dns01.{for_var}. {for_var}.",
            "serial": 
                serial_number,
        }   
        
        template = self.env.get_template('forward_template.jinja')

        output = template.render(data) 

        file_name = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.for.db"
        os.makedirs(self.folder, exist_ok=True)
        file_path = os.path.join(self.folder, file_name)
        with open(file=file_path, mode="w") as zone_file:
            zone_file.write(output)
        #print(output)
        
        
    def delete_zones(self):
        file_name = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.conf"
        file_path = os.path.join(self.folder, file_name)
        file_name_sec = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.conf"
        file_path_sec = os.path.join(self.sec_folder, file_name_sec)

        # Check if the file exists
        if os.path.exists(file_path):
            os.remove(file_path)  # Delete the file
            print(f"Zone File Deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")
            
        if os.path.exists(file_path_sec):
            os.remove(file_path_sec)  # Delete the file
            print(f"Zone File Deleted: {file_path_sec}")
        else:
            print(f"File not found: {file_path_sec}")
    
    
    def delete_forward(self):
        file_name = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.for.db"
        file_path = os.path.join(self.folder, file_name)

        # Check if the file exists
        if os.path.exists(file_path):
            os.remove(file_path)  # Delete the file
            print(f"Zone File Deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")
    
    
    def delete_reverse(self):
        file_name = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.rev.db"
        file_path = os.path.join(self.folder, file_name)

        # Check if the file exists
        if os.path.exists(file_path):
            os.remove(file_path)  # Delete the file
            print(f"Zone File Deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")