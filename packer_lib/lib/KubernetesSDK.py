import configparser
from scp import SCPClient
import paramiko
import time
import os

class Kubernetes:
    __host = None
    __vm = None
    def __init__(self) -> None:
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'credentials.cfg'),
            os.path.join(config_folder, 'vmwareconfig.cfg'),
            os.path.join(config_folder, 'hostconfig.cfg'),
        ]
        self.config.read(config_files)
        self.customer_name = self.config.get('Customerinfo', 'uniqueId')
        
        
    def ssh_connect(self, hostname):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(hostname=hostname, 
                    port=self.config.get('Scriptconfig', 'port'), 
                    username=self.config.get('Scriptconfig', 'username'), 
                    password=self.config.get('Scriptconfig', 'password'))
        
        return ssh
    
    
    def get_join_command(self, host):
        try:
            ssh = None
            ssh = self.ssh_connect(host)
            
            stdin, stdout, stderr = ssh.exec_command("kubeadm token create --print-join-command")
            join_command = stdout.read().decode().strip()
            ssh.close()
            
            #print(join_command)
            return join_command
        
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()
            
            
    def kubeadm_init(self):
        time.sleep(10)
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if k8s_role:
                        cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(cp_hostname) 
                        ssh = None
                        ssh = self.ssh_connect(cp_hostname)
                        sudo_password = self.config.get('Scriptconfig', 'password')
                        command = f"echo {sudo_password} | sudo -S kubeadm init --control-plane-endpoint={cp_hostname}"
                        stdin, stdout, stderr = ssh.exec_command(command)

                        stdin.write(sudo_password + '\n')
                        stdin.flush()

                        stdout_output = stdout.read().decode()
                        stderr_output = stderr.read().decode()

                        if "password for" in stderr_output.lower():
                            # Ignore sudo password prompts as they are not critical errors
                            stderr_output = ""

                        if stderr_output:
                            print(f"Error kubeadm_init: {stderr_output}")
                        else:
                            print(f"{cp_hostname}: kubeadm_init Done")
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close() 
            
            
    def add_kube_config(self): 
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if k8s_role:
                        cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(cp_hostname) 
                        ssh = None
                        ssh = self.ssh_connect(cp_hostname)
                        sudo_password = self.config.get('Scriptconfig', 'password')
                        command = f"""
mkdir -p $HOME/.kube && 
echo {sudo_password} | sudo -S cp -i /etc/kubernetes/admin.conf $HOME/.kube/config && 
echo {sudo_password} | sudo -S chown $(id -u):$(id -g) $HOME/.kube/config
                        """
                        stdin, stdout, stderr = ssh.exec_command(command)

                        stdin.write(sudo_password + '\n')
                        stdin.flush()

                        stdout_output = stdout.read().decode()
                        stderr_output = stderr.read().decode()

                        if "password for" in stderr_output.lower():
                            # Ignore sudo password prompts as they are not critical errors
                            stderr_output = ""

                        if stderr_output:
                            print(f"Error adding kube config file to Home: {stderr_output}")
                        else:
                            print(f"Added admin.conf to test/.kube/config")
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()    
        
        
    def setup_cillium_cp(self): 
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if k8s_role:
                        cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(cp_hostname) 
                        ssh = None
                        ssh = self.ssh_connect(cp_hostname)
                        sudo_password = self.config.get('Scriptconfig', 'password')

                        command = f"""
                        CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt) && \
                        CLI_ARCH=amd64 && \
                        if [ "$(uname -m)" = "aarch64" ]; then CLI_ARCH=arm64; fi && \
                        curl -L --fail --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${{CILIUM_CLI_VERSION}}/cilium-linux-${{CLI_ARCH}}.tar.gz{{,.sha256sum}} && \
                        sha256sum --check cilium-linux-${{CLI_ARCH}}.tar.gz.sha256sum && \
                        echo {sudo_password} | sudo -S tar xzvfC cilium-linux-${{CLI_ARCH}}.tar.gz /usr/local/bin && \
                        rm cilium-linux-${{CLI_ARCH}}.tar.gz{{,.sha256sum}} && \
                        /usr/local/bin/cilium install --version 1.15.5
                        """

                        stdin, stdout, stderr = ssh.exec_command(command)

                        stdin.write(sudo_password + '\n')
                        stdin.flush()

                        stdout_output = stdout.read().decode()
                        stderr_output = stderr.read().decode()

                        if "password for" in stderr_output.lower():
                            stderr_output = ""

                        if stderr_output:
                            print(f"Error installing Cilium: {stderr_output}")
                        else:
                            print(f"Cilium installed successfully: {stdout_output}")
                            
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()        
        
    
    def identify_controller_role(self):
        for section in self.config.sections():
            if section.startswith('Host'):
                k8s_role = self.config.getboolean(section, 'k8sController')     
                if k8s_role:
                    cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                    print(cp_hostname)
                    
        return cp_hostname
                
    
    def identify_wnodes_role(self):
        wn_list = []
        for section in self.config.sections():
            if section.startswith('Host'):
                k8s_role = self.config.getboolean(section, 'k8sController')     
                if not k8s_role:
                    #cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                    wn_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                    wn_list.append(wn_hostname)
                    
        return wn_list
        
        
    def join_controller(self, join_command):
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if not k8s_role:
                        wn_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(wn_hostname) 
                        ssh = None
                        ssh = self.ssh_connect(wn_hostname)
                        sudo_password = self.config.get('Scriptconfig', 'password')
                        command = f"echo {sudo_password} | sudo -S {join_command}"
                        stdin, stdout, stderr = ssh.exec_command(command)

                        stdin.write(sudo_password + '\n')
                        stdin.flush()

                        stdout_output = stdout.read().decode()
                        stderr_output = stderr.read().decode()

                        if "password for" in stderr_output.lower():
                            # Ignore sudo password prompts as they are not critical errors
                            stderr_output = ""

                        if stderr_output:
                            print(f"Error kubeadm_init: {stderr_output}")
                        else:
                            print(f"{wn_hostname}: kubeadm_init Done")
        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()
            
    
    def wait_for_nodes_ready(self, node_hostnames, max_retries=10, delay=10):
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if k8s_role:
                        cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(f"SSH to {cp_hostname}") 
                        ssh = None
                        ssh = self.ssh_connect(cp_hostname)

                        for wn_hostname in node_hostnames:
                            node_ready = False
                            retries = 0
                            while retries < max_retries:
                                stdin, stdout, stderr = ssh.exec_command("kubectl get nodes")
                                output = stdout.read().decode()

                                # Check for the node in the kubectl output and ensure it's in the "Ready" status
                                for line in output.splitlines():
                                    if wn_hostname in line:
                                        # The second column is typically the status, so we split and check for "Ready"
                                        columns = line.split()
                                        if len(columns) > 1 and columns[1] == "Ready":
                                            node_ready = True
                                            print(f"{wn_hostname} is now Ready")
                                            break

                                if node_ready:
                                    break
                                else:
                                    retries += 1
                                    print(f"Waiting for {wn_hostname} to be Ready... ({retries}/{max_retries})")
                                    time.sleep(delay)  # Wait for the specified delay before checking again

                            if not node_ready:
                                print(f"Timed out waiting for {wn_hostname} to be Ready")

        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()
                
                
    def wait_for_metallb_ready(self, max_retries=10, delay=10):
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if k8s_role:
                        cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(f"SSH to {cp_hostname} (wait_for_metallb_deployment_ready)") 
                        ssh = None
                        ssh = self.ssh_connect(cp_hostname)

                        retries = 0
                        while retries < max_retries:
                            # Run the kubectl get deployment command and check if output is non-empty
                            stdin, stdout, stderr = ssh.exec_command(
                                "kubectl get deployment -n metallb-system | grep -P '(\\d+)/(\\1)'"
                            )
                            output = stdout.read().decode().strip()

                            if output:
                                print(f"MetalLB deployment is ready: {output}")
                                return True  # Deployment is ready
                            else:
                                retries += 1
                                print(f"Waiting for MetalLB deployment to be ready... ({retries}/{max_retries})")
                                time.sleep(delay)

                        # If we exhaust retries, MetalLB isn't ready
                        print("Timed out waiting for MetalLB deployment to be ready.")

        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()
                    
                
    def install_metallb(self):
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if k8s_role:
                        cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(f"SSH to {cp_hostname} (install_metallb)") 
                        ssh = None
                        ssh = self.ssh_connect(cp_hostname)

                        # Apply MetalLB manifest to the cluster
                        command = "kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.8/config/manifests/metallb-native.yaml"
                        stdin, stdout, stderr = ssh.exec_command(command)

                        stdout_output = stdout.read().decode()
                        stderr_output = stderr.read().decode()

                        if stderr_output:
                            print(f"Error installing MetalLB: {stderr_output}")
                        else:
                            print(f"MetalLB installed successfully: {stdout_output}")

        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()
                    
    
    def configure_metallb(self):
        #time.sleep(15)
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if k8s_role:
                        cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(f"SSH to {cp_hostname} (configure_metallb)") 
                        ssh = None
                        ssh = self.ssh_connect(cp_hostname)
                        # Define the IP range for the Layer 2 pool
                        ip_address = self.config.get('Customerinfo', 'network')
                        parts = ip_address.split(".")
                        new_ip = ".".join(parts[:-1]) + ".240/32" 
                        print(new_ip)
                        #ip_range = "10.5.0.240-10.5.0.250"         

                        # Create the MetalLB configuration (Layer 2 mode)
                        command = f"""
cat <<EOF | kubectl create -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  namespace: metallb-system
  name: {self.customer_name}-ip-pool
spec:
  addresses:
  - {new_ip}
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  namespace: metallb-system
  name: {self.customer_name}-l2-advertisement
EOF
                        """
                        print(command)

                        stdin, stdout, stderr = ssh.exec_command(command)
                        stdout_output = stdout.read().decode()
                        stderr_output = stderr.read().decode()

                        if stderr_output:
                            print(f"Error configuring MetalLB: {stderr_output}")
                        else:
                            print(f"MetalLB configured successfully: {stdout_output}")

        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()


    def scp_kubeconfig_to_deployment_server(self):
        try:
            for section in self.config.sections():
                if section.startswith('Host'):
                    k8s_role = self.config.getboolean(section, 'k8sController')     
                    if k8s_role:
                        cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                        print(f"SSH to {cp_hostname} (SCP kubeconfig with sudo)")

                        # SSH to the control plane node
                        ssh = self.ssh_connect(cp_hostname)

                        # Use sudo to read the file and copy it
                        command = "sudo cat /etc/kubernetes/admin.conf"
                        stdin, stdout, stderr = ssh.exec_command(command)
                        stdout_output = stdout.read()

                        # Check if there was an error with sudo
                        stderr_output = stderr.read().decode().strip()
                        if stderr_output:
                            print(f"Error reading admin.conf with sudo: {stderr_output}")
                            return

                        # Write the file content to the /data/config path on the deployment server
                        destination_path = "/data/config"
                        sftp = ssh.open_sftp()
                        with sftp.file(destination_path, 'w') as f:
                            f.write(stdout_output.decode())

                        print(f"Successfully copied admin.conf to {destination_path} on the deployment server.")

                        # Close the SFTP connection
                        sftp.close()

        except paramiko.SSHException as e:
            print(f"SSH connection failed: {e}")
        except FileNotFoundError as e:
            print(f"File not found: {e}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if ssh:
                ssh.close()
                
                
    def clone_repository(self, ssh, repo_url="https://github.com/theTiha/h8_k8s_deploy.git", clone_path="~/h8_k8s_deploy"):
        """Clones the specified repository to the remote host."""
        clone_command = f"git clone {repo_url} {clone_path}"
        stdin, stdout, stderr = ssh.exec_command(clone_command)
        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()
        if stderr_output:
            print(f"Cloning repository: {stderr_output}")
        else:
            print(f"Repository cloned successfully: {stdout_output}")


    def apply_kubectl_commands(self, ssh, clone_path="~/h8_k8s_deploy"):
        """Applies kubectl configurations from the cloned repository."""
        kubectl_commands = [
            f"kubectl apply -f {clone_path}/nfs-pv-pvc.yaml",
            f"kubectl apply -f {clone_path}/nginx-deployment.yaml",
            f"kubectl apply -f {clone_path}/nginx-service.yaml"
        ]
        for command in kubectl_commands:
            stdin, stdout, stderr = ssh.exec_command(command)
            stdout_output = stdout.read().decode()
            stderr_output = stderr.read().decode()
            if stderr_output:
                print(f"Error executing {command}: {stderr_output}")
            else:
                print(f"Executed {command} successfully: {stdout_output}")


    def mount_nfs_and_copy_file(self, ssh, clone_path="~/h8_k8s_deploy", nfs_server_ip="172.16.252.21", nfs_path="/mnt/Cust_pool/demo01", mount_point="/mnt"):
        """Mounts NFS and copies the index.html file to the mounted directory."""
        sudo_password = self.config.get('Scriptconfig', 'password')
        
        # Create the mount directory if it does not exist
        ssh.exec_command(f"echo {sudo_password} | sudo -S mkdir -p {mount_point}")
        
        # Mount NFS with a command that includes the password in a single input for simplicity
        mount_command = f"echo {sudo_password} | sudo -S mount -t nfs {nfs_server_ip}:{nfs_path} {mount_point}"
        stdin, stdout, stderr = ssh.exec_command(mount_command)
        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()
        
        stdin.write(sudo_password + '\n')
        stdin.flush()

        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()

        if "password for" in stderr_output.lower():
            # Ignore sudo password prompts as they are not critical errors
            stderr_output = ""

        if stderr_output:
            print(f"Error NFS: {stderr_output}")
        else:
            print(f"{nfs_server_ip}:{nfs_path} {mount_point}: NFS mount is Done")

        # Copy the index.html file to the mounted directory
        copy_command = f"echo {sudo_password} | sudo -S cp {clone_path}/index.html {mount_point}/"
        stdin, stdout, stderr = ssh.exec_command(copy_command)
        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()
        
        stdin.write(sudo_password + '\n')
        stdin.flush()

        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()

        if "password for" in stderr_output.lower():
            # Ignore sudo password prompts as they are not critical errors
            stderr_output = ""

        if stderr_output:
            print(f"Error copy index.html to mount path: {stderr_output}")
        else:
            print(f"{clone_path}/index.html {mount_point}/: NFS mount is Done")
            


    def clone_and_apply_kubectl_commands(self, retries=5):
        for section in self.config.sections():
            if section.startswith('Host'):
                k8s_role = self.config.getboolean(section, 'k8sController')     
                if k8s_role:
                    cp_hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                    print(f"SSH to {cp_hostname} (clone_and_apply_kubectl_commands)") 

                    # Retry mechanism for SSH connection
                    attempt = 0
                    while attempt < retries:
                        try:
                            ssh = self.ssh_connect(cp_hostname)

                            # Enable keep-alive
                            ssh.get_transport().set_keepalive(30)

                            # Clone repository
                            self.clone_repository(ssh)
                            time.sleep(1)  # Short delay between commands

                            # Mount NFS and copy index.html
                            self.mount_nfs_and_copy_file(ssh)
                            time.sleep(1)  # Short delay between commands

                            # Apply kubectl commands
                            self.apply_kubectl_commands(ssh)
                            break  # Break out of loop if successful

                        except paramiko.SSHException as e:
                            print(f"SSH connection attempt {attempt + 1} failed: {e}")
                            attempt += 1
                            time.sleep(2)  # Wait before retrying
                        except Exception as e:
                            print(f"Error during execution: {e}")
                            attempt += 1
                            time.sleep(2)  # Wait before retrying
                        finally:
                            if ssh:
                                ssh.close()

                    if attempt == retries:
                        print(f"Failed to complete SSH commands after {retries} attempts.")
                        
                        
    def clone_repository(self, hostname, repo_url="https://github.com/theTiha/h8_k8s_deploy.git", clone_path="~/h8_k8s_deploy"):
        """Clones the specified repository to the remote host."""
        try:
            ssh = self.ssh_connect(hostname)
            clone_command = f"git clone {repo_url} {clone_path}"
            stdin, stdout, stderr = ssh.exec_command(clone_command)
            stdout_output = stdout.read().decode()
            stderr_output = stderr.read().decode()
            if stderr_output:
                print(f"Cloning repository: {stderr_output}")
            else:
                print(f"Repository cloned successfully: {stdout_output}")
        finally:
            ssh.close()

    def apply_kubectl_commands(self, hostname, clone_path="~/h8_k8s_deploy"):
        """Applies kubectl configurations from the cloned repository."""
        kubectl_commands = [
            f"kubectl apply -f {clone_path}/nfs-pv-pvc.yaml",
            f"kubectl apply -f {clone_path}/nginx-deployment.yaml",
            f"kubectl apply -f {clone_path}/nginx-service.yaml"
        ]
        try:
            ssh = self.ssh_connect(hostname)
            for command in kubectl_commands:
                stdin, stdout, stderr = ssh.exec_command(command)
                stdout_output = stdout.read().decode()
                stderr_output = stderr.read().decode()
                if stderr_output:
                    print(f"Error executing {command}: {stderr_output}")
                else:
                    print(f"Executed {command} successfully: {stdout_output}")
        finally:
            ssh.close()

    def mount_nfs(self, hostname, nfs_server_ip="172.16.252.21", nfs_path="/mnt/Cust_pool/demo01", mount_point="/mnt"):
        """Mounts the NFS share on the remote host."""
        sudo_password = self.config.get('Scriptconfig', 'password')
        try:
            ssh = self.ssh_connect(hostname)
            ssh.exec_command(f"echo {sudo_password} | sudo -S mkdir -p {mount_point}")
            mount_command = f"echo {sudo_password} | sudo -S mount -t nfs {nfs_server_ip}:{nfs_path} {mount_point}"
            stdin, stdout, stderr = ssh.exec_command(mount_command)
            stdin.write(sudo_password + '\n')
            stdin.flush()
            stdout_output = stdout.read().decode()
            stderr_output = stderr.read().decode()
            if stderr_output:
                print(f"Mounting NFS: {stderr_output}")
            else:
                print(f"NFS mount completed: {stdout_output}")
        finally:
            ssh.close()

    def copy_index_html(self, hostname, clone_path="~/h8_k8s_deploy", mount_point="/mnt"):
        """Copies the index.html file to the mounted directory."""
        sudo_password = self.config.get('Scriptconfig', 'password')
        copy_command = f"echo {sudo_password} | sudo -S cp {clone_path}/index.html {mount_point}/"
        try:
            ssh = self.ssh_connect(hostname)
            stdin, stdout, stderr = ssh.exec_command(copy_command)
            stdin.write(sudo_password + '\n')
            stdin.flush()
            stdout_output = stdout.read().decode()
            stderr_output = stderr.read().decode()
            if stderr_output:
                print(f"Copying index.html to mount path: {stderr_output}")
            else:
                print(f"index.html copied successfully to {mount_point}")
        finally:
            ssh.close()


    def execute_tasks(self):
        """Executes all tasks in sequence for each configured host with k8sController role."""
        for section in self.config.sections():
            if section.startswith('Host'):
                k8s_role = self.config.getboolean(section, 'k8sController')
                if k8s_role:
                    hostname = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.cloudcubes.gg"
                    print(f"Connecting to {hostname} for task execution")
                    self.clone_repository(hostname)
                    time.sleep(1)
                    self.mount_nfs(hostname)
                    time.sleep(1)
                    self.copy_index_html(hostname)
                    time.sleep(1)
                    self.apply_kubectl_commands(hostname)
