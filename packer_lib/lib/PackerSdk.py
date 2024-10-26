import requests
import configparser
import ipaddress
import subprocess
import time
import shutil
import ssl
import os
from jinja2 import  Environment, FileSystemLoader
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

requests.packages.urllib3.disable_warnings()

class Packersdk:
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
        self.template_dir = os.path.join(os.path.dirname(__file__), '../', 'templates')
        #self.created_path = os.path.join(os.path.dirname(__file__), '../', 'created')
        self.created_path = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/created"
        #self.data_path = os.path.join(os.path.dirname(__file__), '../', 'data') 
        self.data_path = f"{self.config.get('Scriptconfig', 'dnsFilePath')}{self.config.get('Customerinfo', 'customerName')}/data"
        self.env = Environment(loader=FileSystemLoader(self.template_dir))     
        self.session = requests.Session()
        self.session.verify = self.config.getboolean('VmWare', 'ca')
        self.session.auth = (self.config.get('VmWare', 'username'), self.config.get('VmWare', 'password'))
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['Accept'] = 'application/json'
        res = self.session.post('https://'+self.config.get('VmWare', 'vcenter')+'/api/session')
        self.session.headers['vmware-api-session-id'] = res.json() 
        print(f"Status Code VmWare: {res.status_code}")
        if res.status_code != 201:
            raise Exception(f"Could not login to vmware: {res.text}")
        self.connect_pyvmomi()


    def connect_pyvmomi(self):
        # Create SSL
        context = ssl._create_unverified_context()
        # Connect to the vCenter Server
        self.si = SmartConnect(
            host=self.config.get('VmWare', 'vcenter'),
            user=self.config.get('VmWare', 'username'),
            pwd=self.config.get('VmWare', 'password'),
            port=443,
            sslContext=context
            )
        
        
    def disconnect(self):
        Disconnect(self.si)
        print("Disconnected from vCenter")
        
        
    def power_off_vm(self, vm=None):
        if vm is not None:
            vm_to_use = vm
            self.__vm = self.find_vm_moid(vm_to_use)
        else:
            vm_to_use = self.__vm
        if vm_to_use is None:
            raise ValueError("VM must be provided if self.__vm is not set")
        
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{self.__vm['vm']}/power?action=stop"
        requests = self.session.post(url)
        # requests.raise_for_status()
        if requests.status_code == 400:
            print(f"virtual machine is already powered off. STATUS {requests.status_code}")
    
    
    def power_on_vm(self, vm=None):
        if vm is not None:
            vm_to_use = vm
            self.__vm = self.find_vm_moid(vm_to_use)
        else:
            vm_to_use = self.__vm
        if vm_to_use is None:
            raise ValueError("VM must be provided if self.__vm is not set")
        
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{self.__vm['vm']}/power?action=start"
        requests = self.session.post(url)
        if requests.status_code == 400:
            print(f"virtual machine is already powered off. STATUS {requests.status_code}")
    
    
    def find_vm_moid(self, vm_name):
        # Find VM moid "Virtual machine identifier"
        if vm_name is None:
            raise FileNotFoundError("find_vm_name: VM Not found")
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm?names={vm_name}"
        request = self.session.get(url)
        # print(request.status_code)
        req_json = request.json()
        if not req_json:
            raise FileNotFoundError(f"Could not find vm {vm_name} - request empty")
        self.__vm = req_json[0]
        print(f"MOID: {self.__vm['vm']}")
        return self.__vm
    
    
    def delete_vm(self, vm):
        # Needs MOID to delete VM and the VM must be powered off first
        if vm is not None:
            vm_to_use = vm
            self.__vm = self.find_vm_moid(vm_to_use)
        else:
            vm_to_use = self.__vm

        if vm_to_use is None:
            raise ValueError("VM must be provided if self.__vm is not set")
        
        if isinstance(self.__vm, dict):
            self.__vm = self.__vm.get('vm')  

        if not self.__vm:
            raise ValueError("MOID for the VM could not be found")

        print(f"Using MOID: {self.__vm}")
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{self.__vm}"
        response = self.session.delete(url)

        if response.status_code == 400:
            print(f"Error: Virtual machine is powered on. STATUS {response.status_code}")
        elif response.status_code == 404:
            print(f"Error: Virtual machine not found. STATUS {response.status_code}")
        elif response.status_code == 204:
            print(f"VM deleted successfully. STATUS {response.status_code}")
        else:
            try:
                print(response.json())
            except requests.exceptions.JSONDecodeError:
                print("No JSON response, likely because the operation succeeded with no content.")
            
            
    def change_vm_portgroup(self, vm_name, adapter_index, new_portgroup_name):
        # Get the VM object by name
        vm = self.get_obj([vim.VirtualMachine], vm_name)
        if not vm:
            raise Exception(f"VM '{vm_name}' not found.")
        self.list_vm_devices(vm)

        if adapter_index >= len(vm.config.hardware.device):
            raise Exception(f"Adapter index {adapter_index} is out of range. VM has {len(vm.config.hardware.device)} devices.")
        nic = vm.config.hardware.device[adapter_index]

        if not isinstance(nic, vim.vm.device.VirtualEthernetCard):
            raise Exception(f"Device at index {adapter_index} is not a network adapter.")
        new_portgroup = self.get_obj([vim.DistributedVirtualPortgroup], new_portgroup_name)

        if not new_portgroup:
            raise Exception(f"Port group '{new_portgroup_name}' not found.")
        nic_spec = vim.VirtualDeviceConfigSpec()
        nic_spec.operation = vim.VirtualDeviceConfigSpecOperation.edit
        nic_spec.device = nic

        backing = nic.backing
        print(f"Backing type: {type(backing)}") 

        if isinstance(backing, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
            port_connection = vim.DistributedVirtualSwitchPortConnection(
                portgroupKey=new_portgroup.key,
                switchUuid=new_portgroup.config.distributedVirtualSwitch.uuid
            )
            
            backing.port = port_connection 
            nic.backing = backing
        else:
            raise Exception(f"Unsupported backing type: {type(backing)}. Please check the network adapter's configuration.")

        vm_spec = vim.VirtualMachineConfigSpec()
        vm_spec.deviceChange = [nic_spec]
        task = vm.ReconfigVM_Task(vm_spec)
        self.wait_for_task(task)
        print(f"Successfully changed the port group of '{vm_name}' adapter {adapter_index} to '{new_portgroup_name}'.")
              
        
    def wait_for_task(self, task):
        while True:
            if task.info.state in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                break
            print("Waiting for task to complete...")
            time.sleep(2)

        if task.info.state == vim.TaskInfo.State.error:
            raise Exception(f"Task failed: {task.info.error.msg}")
        
    
    def list_vm_devices(self, vm):
        print(f"Devices for VM '{vm.name}':")
        for idx, device in enumerate(vm.config.hardware.device):
            print(f"Index: {idx}, Device: {type(device).__name__}, Name: {device.deviceInfo.label}")
      
            
    def get_obj(self, vimtype, name):
        content = self.si.RetrieveContent()
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        obj = None
        for c in container.view:
            if c.name == name:
                obj = c
                break
        container.Destroy()
        return obj
            
    
    def create_host_files(self):
        os.makedirs(self.created_path, exist_ok=True)
        for section in self.config.sections():
            if section.startswith("Host"):
                fqdn = f"{self.config.get(section, 'hostName')}.{self.config.get('Customerinfo', 'subDomainName')}.{self.config.get('Customerinfo', 'domainName')}"
                ip_address = f"{self.config.get(section, 'ipAdress')}"
                data = {
                    "hostname": f'"{fqdn}"',
                    "ip": f'"{ip_address}"',
                }

                env = Environment(loader=FileSystemLoader(self.template_dir))
                template = env.get_template('host_variables_template.jinja')

                output = template.render(data)

                with open(f"{self.created_path}/{fqdn}.pkrvars.hcl", 'w') as file:
                    file.write(output)


    def create_subnet_files(self):
        os.makedirs(self.created_path, exist_ok=True)
        for section in self.config.sections():
            if section.startswith("Customerinfo"):
                customer_unique_id=f"{self.config.get(section,'uniqueId')}"
                dp_vlan=f"{customer_unique_id}-{self.config.get('Host01','vlanId')}"
                network = ipaddress.ip_network(f"{self.config.get(section,'network')}/24", strict=False)
                gateway= list(network.hosts())[0]
                data = {
                                    "dp_vlan": f'"{dp_vlan}"',
                                    "vm_folder": '""',
                                    "unique_id":  f'"{customer_unique_id}"',
                                    "gateway": f'"{gateway}"',
                                }
                env = Environment(loader=FileSystemLoader(self.template_dir)) 
                template = env.get_template('subnet_variables_template.jinja')

                output = template.render(data)
                with open(f"{self.created_path}/subnet_config.pkrvars.hcl", 'w') as file:
                    file.write(output)
        
                    
    def create_vm_host(self):
        print(os.path.dirname(__file__))
        all_files = os.listdir(f'{self.created_path}')
        files_to_process = [file for file in all_files if file != 'subnet_config.pkrvars.hcl']
        print(files_to_process)
        overall_return_code = 0
        
        try:
            # Ensure Packer plugins are initialized
            print("Initializing Packer plugins...")
            init_command = ["packer", "init", os.path.join(os.path.dirname(__file__), '../templates/ubuntu-cust-build.pkr.hcl')]
            init_process = subprocess.Popen(init_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = init_process.communicate()
            print(stdout.decode())
            if init_process.returncode != 0:
                print("Packer init failed:")
                print(stderr.decode())
                return 1  # Exit early if init fails
            else:
                print("Packer plugins initialized successfully.")

        except Exception as e:
            print(f"An error occurred during Packer initialization: {e}")
            return 1

        for new_host in files_to_process:
            try:
                print(new_host)

                # Fix the relative path to point to the correct templates directory
                template_path = os.path.join(os.path.dirname(__file__), '../templates/ubuntu-cust-build.pkr.hcl')
                #template_path = f'{self.created_path} ../templates/ubuntu-cust-build.pkr.hcl'
                subnet_config_path = f'{self.created_path}/subnet_config.pkrvars.hcl'
                print(subnet_config_path)
                # subnet_config_path = os.path.join(os.path.dirname(__file__), '../created/subnet_config.pkrvars.hcl')
                constant_variables = os.path.join(os.path.dirname(__file__), '../templates/constant_variables_template.pkrvars.hcl')

                command = [
                    "packer", "build",
                    f"-var-file={self.created_path}/{new_host}",
                    f"-var-file={subnet_config_path}",
                    f"-var-file={constant_variables}",
                    template_path  # Use the fixed path
                ]
                print(f"Starting Packer build for {new_host}...")

                # Set working directory to ensure correct paths
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.dirname(__file__))
                stdout, stderr = process.communicate()
                print(stdout.decode())
                if process.returncode == 0:
                    print(f"Build completed successfully for {new_host}.")
                    clean_hostname = new_host.split(".pkrvars.hcl")
                    with open(subnet_config_path, 'r') as file:
                        for line in file:
                            if line.startswith('new_network'):
                                find_dp = line.split('=')[1].strip().strip('"')
                                print(find_dp)

                    self.change_vm_portgroup(vm_name=clean_hostname[0], adapter_index=13, new_portgroup_name=find_dp)
                    self.power_on_vm(vm=f"{clean_hostname[0]}")
                    os.makedirs(self.data_path, exist_ok=True)
                    file_path = os.path.join(self.data_path, "current_hosts")
                    with open(file=file_path, mode="a") as zone_file:
                        zone_file.write(f"{clean_hostname[0]}\n")
                        print(stdout.decode())

                else:
                    print(f"Build failed for {new_host}.")
                    print(stderr.decode())  # Print specific error message
                    overall_return_code = 1

            except Exception as e:
                print(f"An error occurred while running Packer: {e}")
                overall_return_code = 1
        return overall_return_code
    
    
    def destroy_vm_host(self):
        with open(f"{self.data_path}/current_hosts","r") as file:
            for hosts in file:
                host = hosts.strip()
                self.power_off_vm(host)
                self.delete_vm(host)
        if os.path.exists(self.data_path):
            # Remove the folder and all its contents
            shutil.rmtree(self.data_path)
            print(f"Folder '{self.data_path}' and its contents have been removed.")
        else:
            print(f"Folder '{self.data_path}' does not exist.")
        
        if os.path.exists(self.created_path):
            # Remove the folder and all its contents
            shutil.rmtree(self.created_path)
            print(f"Folder '{self.created_path}' and its contents have been removed.")
        else:
            print(f"Folder '{self.created_path}' does not exist.")


    def delete_portgroup(self):
        # Importen, it's not nessasary to delete portgroup first if you delete the DVS
        #time.sleep(10)
        for section in self.config.sections():
            if section.startswith('DVPortgroup'):
                content = self.si.RetrieveContent()
                        
                # Find the Portgroup by name
                portgroup = None
                for datacenter in content.rootFolder.childEntity:
                    if isinstance(datacenter, vim.Datacenter):
                        network_folder = datacenter.networkFolder
                        for network in network_folder.childEntity:
                            if isinstance(network, vim.dvs.DistributedVirtualPortgroup) and network.name == self.config.get(section, "portgroupName"):
                                portgroup = network
                                print("Portgroup found")
                                print(portgroup)
                                break
                        if portgroup:
                            break
                
                if not portgroup:
                    print(f"Distributed Virtual Switch '{self.config.get(section, "portgroupName")}' not found.")
                    return
                
                # Delete the portgroup
                try:
                    task = portgroup.Destroy_Task()
                    self.wait_for_task(task)

                    if task.info.state == 'success':
                        print(f"Successfully deleted DVS: {self.config.get(section, "portgroupName")}")
                    else:
                        print(f"Failed to delete DVS: {self.config.get(section, "portgroupName")}")
                        print(f"Error: {task.info.error.msg}")
                except Exception as e:
                    print(f"An error occurred while deleting the DVS: {str(e)}")