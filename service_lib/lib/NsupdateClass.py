from jinja2 import  Environment, FileSystemLoader
import paramiko
import subprocess
import configparser
import os
import time

class Nsupdate:
    def __init__(self) -> None:
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'hostconfig.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
        ]      
        self.config.read(config_files)
        self.rndc_key = os.path.join(os.path.dirname(__file__), '../', 'rndc_key/rndcKey.conf')
        
        template_dir = os.path.join(os.path.dirname(__file__), '../' 'templates')
        print(template_dir)
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    
    def ssh_connect(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.config.get('Scriptconfig', 'dnsServer01'), 
                        port=self.config.get('Scriptconfig', 'port'), 
                        username=self.config.get('Scriptconfig', 'username'), 
                        password=self.config.get('Scriptconfig', 'password')
                        )
        return ssh
    

    def restart_bind9_service(self):
        try:
            ssh = self.ssh_connect()
            
            sudo_password = self.config.get('Scriptconfig', 'password')
            command = f"echo {sudo_password} | sudo -S systemctl restart bind9"
            stdin, stdout, stderr = ssh.exec_command(command)

            stdin.write(sudo_password + '\n')
            stdin.flush()

            stdout_output = stdout.read().decode()
            stderr_output = stderr.read().decode()

            # Only treat stderr as an error if it contains something other than the password prompt
            if "password for" in stderr_output.lower():
                # Ignore sudo password prompts as they are not critical errors
                stderr_output = ""

            if stderr_output:
                print(f"Error restarting bind9: {stderr_output}")
            else:
                print(f"Systemctl restart bind9")
                
            # Wait and check if the service is back up
            if self.wait_for_service_up("bind9", timeout=60):
                print("BIND9 service is running.")
            else:
                print("Failed to restart BIND9 service within the timeout period.")
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
            
        
    def wait_for_service_up(self, service_name, timeout=60):
        """Wait for the service to be up by checking its status periodically."""
        start_time = time.time()
        #time.sleep(5)
        while time.time() - start_time < timeout:
            if self.check_service_status(service_name):
                return True
            print(f"Waiting for {service_name} to start...")
            time.sleep(5)  # Wait 5 seconds before checking again
        return False
    
    
    def check_service_status(self, service_name):
        """Check if the specified service is active."""
        try:
            ssh = self.ssh_connect()
            sudo_password = self.config.get('Scriptconfig', 'password')
            command = f"echo {sudo_password} | sudo -S systemctl is-active {service_name}"
            stdin, stdout, stderr = ssh.exec_command(command)
            status = stdout.read().decode().strip()
            return status == "active"
        except Exception as e:
            print(f"Failed to check status of {service_name}: {str(e)}")
            return False
        
        
    def reverse_ip(self, ip_add):
        #rev_ip = self.config.get('Customerinfo', 'network')
        parts = ip_add.split('.')
        reversed_parts = parts[-2::-1]
        reversed_ip = '.'.join(reversed_parts)
        
        return reversed_ip


    def add_ptr_records(self):
        for section in self.config.sections():
            if section.startswith('Host'):
                host_ip = self.config.get(section, 'ipAdress')
                host_name = self.config.get(section, 'hostName')
                
                zone_rev = self.reverse_ip(ip_add=self.config.get('Customerinfo', 'network'))
                full_domain = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
        
                parts = host_ip.split('.')
                reversed_parts = parts[::-1]
                reversed_ip = '.'.join(reversed_parts)
                
                data = {
                    'zone': f"{zone_rev}.in-addr.arpa",
                    'function': 'update add',
                    'reversed_ip': f"{reversed_ip}.in-addr.arpa.",
                    'ptr': f"{host_name}.{full_domain}."
                }
                template = self.env.get_template('ptr_template.jinja')

                output = template.render(data)
                
                print(output)
        
                process = subprocess.Popen(
                    ['nsupdate', '-k', f'{self.rndc_key}'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(output)

                if process.returncode == 0:
                    print("nsupdate succeeded.")
                    print(stdout)
                else:
                    print("nsupdate failed.")
                    print(stderr)
                    
    
    def add_A_records(self):
        for section in self.config.sections():
            if section.startswith('Host'):
                host_ip = self.config.get(section, 'ipAdress')
                host_name = self.config.get(section, 'hostName')
                
                #zone = self.reverse_ip(ip_add=self.config.get('Customerinfo', 'domainName'))
                full_domain = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
        
                # parts = host_ip.split('.')
                # reversed_parts = parts[::-1]
                # reversed_ip = '.'.join(reversed_parts)
                
                data = {
                    'zone': f"{full_domain}",
                    'function': 'update add',
                    'A_record': f"{host_name}.{full_domain}.",
                    'ptr': f"{host_ip}",
                }
                template = self.env.get_template('A_records_template.jinja')

                output = template.render(data)
                
                print(output)
        
                process = subprocess.Popen(
                    ['nsupdate', '-k', f'{self.rndc_key}'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(output)

                if process.returncode == 0:
                    print("nsupdate succeeded.")
                    print(stdout)
                else:
                    print("nsupdate failed.")
                    print(stderr)
        


    def delete_ptr_records(self):
        for section in self.config.sections():
            if section.startswith('Host'):
                host_ip = self.config.get(section, 'ipAdress')
                host_name = self.config.get(section, 'hostName')
                
                zone_rev = self.reverse_ip(ip_add=self.config.get('Customerinfo', 'network'))
                full_domain = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
        
                parts = host_ip.split('.')
                reversed_parts = parts[::-1]
                reversed_ip = '.'.join(reversed_parts)
                
                data = {
                    'zone': f"{zone_rev}.in-addr.arpa",
                    'function': 'delete',
                    'reversed_ip': f"{reversed_ip}.in-addr.arpa.",
                    'ptr': f"{host_name}.{full_domain}."
                }
                
                template = self.env.get_template('ptr_template.jinja')

                output = template.render(data)

                print(output)
        
        
                process = subprocess.Popen(
                    ['nsupdate', '-k', f'{self.rndc_key}'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(output)

                if process.returncode == 0:
                    print("nsupdate succeeded.")
                    print(stdout)
                else:
                    print("nsupdate failed.")
                    print(stderr)
                    
                    
    def delete_A_record(self):
        for section in self.config.sections():
            if section.startswith('Host'):
                host_ip = self.config.get(section, 'ipAdress')
                host_name = self.config.get(section, 'hostName')
                
                #zone = self.reverse_ip(ip_add=self.config.get('Customerinfo', 'domainName'))
                full_domain = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
        
                # parts = host_ip.split('.')
                # reversed_parts = parts[::-1]
                # reversed_ip = '.'.join(reversed_parts)
                
                data = {
                    'zone': f"{full_domain}",
                    'function': 'delete',
                    'A_record': f"{host_name}.{full_domain}.",
                    'ptr': f"{host_ip}",
                }
                template = self.env.get_template('A_records_template.jinja')

                output = template.render(data)
                
                print(output)
        
                process = subprocess.Popen(
                    ['nsupdate', '-k', f'{self.rndc_key}'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(output)

                if process.returncode == 0:
                    print("nsupdate succeeded.")
                    print(stdout)
                else:
                    print("nsupdate failed.")
                    print(stderr)