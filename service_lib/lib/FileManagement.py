import configparser
import os
import paramiko
import time
from scp import SCPClient

class Pushfile:
    def __init__(self) -> None:
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'hostconfig.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
        ]      
        self.config.read(config_files)
        self.folder = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/file_dire"
        self.sec_folder = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/file_dire_sec"
        
    
    def ssh_connect(self, server_key):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Get server hostname using the server key
        hostname = self.config.get('Scriptconfig', server_key)
        
        ssh.connect(hostname=hostname, 
                    port=self.config.get('Scriptconfig', 'port'), 
                    username=self.config.get('Scriptconfig', 'username'), 
                    password=self.config.get('Scriptconfig', 'password'))
        
        return ssh
    
    
    def restart_bind9_service(self, host):
        try:
            ssh = None
            ssh = self.ssh_connect(host)
            
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
                print("BIND9 service is running.\n")
            else:
                print("Failed to restart BIND9 service within the timeout period.")
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
         
            
    def ldap_apply_ldif(self, host):
        try:
            ssh = None
            ssh = self.ssh_connect(host)
            
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
                print("BIND9 service is running.\n")
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
            ssh = self.ssh_connect('dnsServer01')
            sudo_password = self.config.get('Scriptconfig', 'password')
            command = f"echo {sudo_password} | sudo -S systemctl is-active {service_name}"
            stdin, stdout, stderr = ssh.exec_command(command)
            status = stdout.read().decode().strip()
            return status == "active"
        except Exception as e:
            print(f"Failed to check status of {service_name}: {str(e)}")
            return False
        
        
    def rndc_retransfer(self):
        try:
            ssh = None
            ssh = self.ssh_connect('dnsServer02')
            
            custom_zone = f"{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
            sudo_password = self.config.get('Scriptconfig', 'password')
            command = f"echo {sudo_password} | sudo -S rndc retransfer {custom_zone}"
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
                print(f"Error rndc retransfer: {stderr_output}")
            else:
                print(f"rndc retransfer {custom_zone} done")
                
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()


    def create_file_list(self, path):
        dns_conf_dir = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/{path}"
        #dns_conf_dir = os.path.join(os.path.dirname(__file__), '..', path)
        all_files = os.listdir(dns_conf_dir)
        # print(all_files)
        file_list = []
        for files in all_files:
            full_dir = os.path.join(dns_conf_dir, files)
            file_list.append(full_dir)
        # print(file_list)
        
        return file_list
    
    
    def create_file_list_ldap(self, path):
        #ldap_conf_dir = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/{path}"
        ldap_conf_dir = os.path.join(os.path.dirname(__file__), '..', path)
        all_files = os.listdir(ldap_conf_dir)
        # print(all_files)
        file_list = []
        for files in all_files:
            full_dir = os.path.join(ldap_conf_dir, files)
            file_list.append(full_dir)
        # print(file_list)
        
        return file_list

    
    def upload_file_scp(self):
        # Get file list from repo
        file_list = self.create_file_list('file_dire')
        ssh = None
        

        try:
            ssh = self.ssh_connect('dnsServer01')
            
            temp_dir = "/tmp"
            for file_path in file_list:
                with SCPClient(ssh.get_transport()) as scp:
                    scp.put(file_path, temp_dir)
                    # print(f"File '{file_path}' uploaded to '{temp_dir}'")

                # Move file from temp location to the etc/bind directory using sudo
                file_name = file_path.split('/')[-1]
                remote_file = f"{temp_dir}/{file_name}"
                remote_dir = self.config.get('Scriptconfig', 'remoteDir')

                sudo_password = self.config.get('Scriptconfig', 'password')

                command = f"echo {sudo_password} | sudo -S mv {remote_file} {remote_dir} && echo {sudo_password} | sudo -S chown bind:bind {remote_dir}/{file_name}"
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
                    print(f"Error moving file: {stderr_output}")
                else:
                    print(f"File '{file_name}' moved to '{remote_dir}' and ownership changed to 'bind:bind'.")

        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
            self.create_path_file()
            self.add_entry('dnsServer01')
            
            
    def upload_file_sec_scp(self):
        # Get file list from repo
        file_list = self.create_file_list('file_dire_sec')
        ssh = None

        try:
            ssh = self.ssh_connect('dnsServer02')
            
            temp_dir = "/tmp"
            for file_path in file_list:
                with SCPClient(ssh.get_transport()) as scp:
                    scp.put(file_path, temp_dir)
                    # print(f"File '{file_path}' uploaded to '{temp_dir}'")

                # Move file from temp location to the etc/bind directory using sudo
                file_name = file_path.split('/')[-1]
                remote_file = f"{temp_dir}/{file_name}"
                remote_dir = self.config.get('Scriptconfig', 'remoteDir')

                sudo_password = self.config.get('Scriptconfig', 'password')

                command = f"echo {sudo_password} | sudo -S mv {remote_file} {remote_dir} && echo {sudo_password} | sudo -S chown bind:bind {remote_dir}/{file_name}"
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
                    print(f"Error moving file: {stderr_output}")
                else:
                    print(f"File '{file_name}' moved to '{remote_dir}' and ownership changed to 'bind:bind'.")

        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
            self.create_path_file_sec()
            self.add_entry('dnsServer02')  
            
    
    def upload_ldap_files(self):
        file_list = self.create_file_list('LDAP_conf_files')
        ssh = None
        
        try:
            ssh = self.ssh_connect('ldapServer01')
            
            temp_dir = "/tmp"
            for file_path in file_list:
                with SCPClient(ssh.get_transport()) as scp:
                    scp.put(file_path, temp_dir)
                    # print(f"File '{file_path}' uploaded to '{temp_dir}'")

                # Move file from temp location to the etc/bind directory using sudo
                file_name = file_path.split('/')[-1]
                remote_file = f"{temp_dir}/{file_name}"
                # TODO Skal ændres til ldap serverens directory for conf files
                remote_dir = self.config.get('Scriptconfig', 'remoteDir')

                sudo_password = self.config.get('Scriptconfig', 'password')

                command = f"echo {sudo_password} | sudo -S mv {remote_file} {remote_dir} && echo {sudo_password} | sudo -S chown bind:bind {remote_dir}/{file_name}"
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
                    print(f"Error moving file: {stderr_output}")
                else:
                    print(f"File '{file_name}' moved to '{remote_dir}' and ownership changed to 'bind:bind'.")

        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()       
            
    
    def create_path_file(self):
        dns_conf_dir = self.folder
        all_files = os.listdir(dns_conf_dir)
        
        customer_path = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/customer_path"
        
        #current_dir = os.path.dirname(os.path.abspath(__file__))
        #customer_path = os.path.join(current_dir, '..', 'customer_path')
        if not os.path.exists(customer_path):
            os.makedirs(customer_path)
            print(f"Folder '{customer_path}' created.")
        
        file_path = os.path.join(customer_path, f'{self.config.get('Customerinfo', 'subDomainName')}.txt')       
        for files in all_files:
            with open(file_path, 'a') as file:
                file.write(f"{self.config.get('Scriptconfig', 'remoteDir')}{files}\n")
        with open(file_path, 'a') as file:
            file.write(f"/etc/bind/{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.for.db.jnl\n")
            file.write(f"/etc/bind/{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}.rev.db.jnl\n")    
  
  
    def create_path_file_sec(self):
        dns_conf_dir = self.sec_folder
        all_files = os.listdir(dns_conf_dir)
        
        customer_path = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/customer_path_sec"
        
        #current_dir = os.path.dirname(os.path.abspath(__file__))
        #customer_path = os.path.join(current_dir, '..', 'customer_path_sec')
        if not os.path.exists(customer_path):
            os.makedirs(customer_path)
            print(f"Folder '{customer_path}' created.")
        
        file_path = os.path.join(customer_path, f'{self.config.get('Customerinfo', 'subDomainName')}.txt')       
        for files in all_files:
            with open(file_path, 'a') as file:
                file.write(f"{self.config.get('Scriptconfig', 'remoteDir')}{files}\n")
             
    
    def add_entry(self, host):
        # Add entry to named.conf 
        # IMPORTEN named.conf is static in "named_dot_conf"! 
        subdomain = self.config.get('Customerinfo', 'subDomainName')
        remote_dir = self.config.get('Scriptconfig', 'remoteDir')
        domain_name = self.config.get('Customerinfo', 'domainName')
        ssh = None
        
        try:
            ssh = self.ssh_connect(host)        
            sudo_password = self.config.get('Scriptconfig', 'password')
            named_dot_conf = f"{remote_dir}named.conf"
            command = f'echo {sudo_password} | sudo -S bash -c "echo \'include \\"{remote_dir}{subdomain}.{domain_name}.conf\\";\' >> {named_dot_conf}"'
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
                print(f"\nFailed to append string to {named_dot_conf}: {stderr_output}")
            else:
                print(f"\nSuccessfully added string to {named_dot_conf} from {host}")       
            
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()
    
    
    def delete_entry(self, host):
        # delete entry in named.conf
        subdomain = self.config.get('Customerinfo', 'subDomainName')
        remote_dir = self.config.get('Scriptconfig', 'remoteDir')
        domain_name = self.config.get('Customerinfo', 'domainName')
        entry_to_remove = f'include "{remote_dir}{subdomain}.{domain_name}.conf";'
        
        try:
            ssh = None
            ssh = self.ssh_connect(host)
            
            sudo_password = self.config.get('Scriptconfig', 'password')
            
            named_dot_conf = f"{remote_dir}named.conf"
            command = f"echo {sudo_password} | sudo -S sed -i '/{entry_to_remove.replace('/', '\\/').replace('"', '\\"')}/d' {named_dot_conf}"
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
                print(f"\nFailed to delete string from {named_dot_conf}: {stderr_output}")
            else:
                print(f"\nSuccessfully delete string from {named_dot_conf} from {host}")
            
            
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            ssh.close()        
            
            
    def delete_files(self):
        # homemade logic to catche missing files or "createDns" script is not run
        customer_path = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/customer_path"
        #current_dir = os.path.dirname(os.path.abspath(__file__))
        #customer_path = os.path.join(current_dir, '..', 'customer_path')
        
        if not os.path.exists(customer_path):
            print(f"Error: {customer_path} does not exist.")
            return
        local_directory = os.path.join(customer_path, f'{self.config.get('Customerinfo', 'subDomainName')}.txt')
        
        try:
            file_list = []
            with open(local_directory, 'r') as f:
                for line in f.readlines():
                    line = line.strip()
                    file_list.append(line)
        except FileNotFoundError:
                print(f"Error: The file '{local_directory}' does not exist. Nothing to delete!")
                return
             
        try:
            ssh = None
            ssh = self.ssh_connect('dnsServer01')
            #print(file_list)
            for remote_file in file_list:
                sudo_password = self.config.get('Scriptconfig', 'password')
                # Check if the file exists on the remote server
                
                stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_file} && echo 'exists' || echo 'not found'")
                result = stdout.read().decode().strip()
                #print(result)

                if result == 'exists':
                    # If the file exists, delete it
                    stdin, stdout, stderr = ssh.exec_command(f"echo {sudo_password} | sudo -S rm {remote_file}")
                    stdin.write(sudo_password + '\n')
                    stdin.flush()
                    error_message = stderr.read().decode().strip()

                    stdout_output = stdout.read().decode()
                    stderr_output = stderr.read().decode()
                    
                    

                    # Only treat stderr as an error if it contains something other than the password prompt
                    if "password for" in stderr_output.lower():
                        # Ignore sudo password prompts as they are not critical errors
                        stderr_output = ""

                    if stderr_output:
                        print(f"Error Deleting file: {stderr_output}")
                    else:
                        print(f"File '{remote_file}' Deleted successfully from {self.config.get('Scriptconfig', 'dnsServer01')}")
                else:
                    print(f"File on {self.config.get('Scriptconfig', 'dnsServer01')} server {result}")           
           
        except Exception as e:
            print(f"Error: {e}")

        finally:
            ssh.close()
            self.delete_entry('dnsServer01')
            self.restart_bind9_service('dnsServer01')
            
            
    def delete_files_sec(self):
        # homemade logic to catche missing files or "createDns" script is not run
        customer_path = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/customer_path_sec"
        #current_dir = os.path.dirname(os.path.abspath(__file__))
        #customer_path = os.path.join(current_dir, '..', 'customer_path_sec')
        
        if not os.path.exists(customer_path):
            print(f"Error: {customer_path} does not exist.")
            return
        local_directory = os.path.join(customer_path, f'{self.config.get('Customerinfo', 'subDomainName')}.txt')
        
        try:
            file_list = []
            with open(local_directory, 'r') as f:
                for line in f.readlines():
                    line = line.strip()
                    file_list.append(line)
        except FileNotFoundError:
                print(f"Error: The file '{local_directory}' does not exist. Nothing to delete!")
                return
             
        try:
            ssh = None
            ssh = self.ssh_connect('dnsServer02')
            #print(file_list)
            for remote_file in file_list:
                sudo_password = self.config.get('Scriptconfig', 'password')
                # Check if the file exists on the remote server
                
                stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_file} && echo 'exists' || echo 'not found'")
                result = stdout.read().decode().strip()
                #print(result)

                if result == 'exists':
                    # If the file exists, delete it
                    stdin, stdout, stderr = ssh.exec_command(f"echo {sudo_password} | sudo -S rm {remote_file}")
                    stdin.write(sudo_password + '\n')
                    stdin.flush()
                    error_message = stderr.read().decode().strip()

                    stdout_output = stdout.read().decode()
                    stderr_output = stderr.read().decode()
                    
                    

                    # Only treat stderr as an error if it contains something other than the password prompt
                    if "password for" in stderr_output.lower():
                        # Ignore sudo password prompts as they are not critical errors
                        stderr_output = ""

                    if stderr_output:
                        print(f"Error Deleting file: {stderr_output}")
                    else:
                        print(f"File '{remote_file}' Deleted successfully from {self.config.get('Scriptconfig', 'dnsServer02')}.")
                else:
                    print(f"File on {self.config.get('Scriptconfig', 'dnsServer02')} server {result}")           
           
        except Exception as e:
            print(f"Error: {e}")

        finally:
            ssh.close()
            self.delete_entry('dnsServer02')
            self.restart_bind9_service('dnsServer02')
       
        
    def delete_path_file(self):
        #current_dir = os.path.dirname(os.path.abspath(__file__))
        customer_path = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/customer_path"
        #ustomer_path = os.path.join(current_dir, '..', 'customer_path')
        local_directory = os.path.join(customer_path, f'{self.config.get('Customerinfo', 'subDomainName')}.txt')
        customer_path02 = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/customer_path_sec"
        local_directory02 = os.path.join(customer_path02, f'{self.config.get('Customerinfo', 'subDomainName')}.txt')
        try:
            os.remove(local_directory)
            os.remove(local_directory02)
            print(f"File '{local_directory}' is deleted /data")
        except Exception as e:
            print(f'Error {e} deleting files /data')
    
    