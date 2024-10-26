import requests
import configparser
import pprint
import time
import ssl
import os
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

requests.packages.urllib3.disable_warnings()

class VMware:
    # Setting varibles to None to preflight test
    __host = None
    __vm = None
    def __init__(self) -> None:
        # Configparser
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'config.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
            os.path.join(config_folder, 'vmwareconfig.cfg')
        ]      
        self.config.read(config_files)
        # Session 
        self.session = requests.Session()
        # Check for CA certificate on VmWare vcenter
        self.session.verify = self.config.getboolean('VmWare', 'ca')
        
        # Auth vmware and set headers
        self.session.auth = (self.config.get('VmWare', 'username'), self.config.get('VmWare', 'password'))
        self.session.headers['Content-Type'] = 'application/json'
        self.session.headers['Accept'] = 'application/json'
        res = self.session.post('https://'+self.config.get('VmWare', 'vcenter')+'/api/session')
        self.session.headers['vmware-api-session-id'] = res.json()
        
        # For testing status code  
        print(f"Status Code VmWare: {res.status_code}")
        if res.status_code != 201:
            raise Exception(f"Could not login to vmware: {res.text}")
        
        # Establish pyVmomi connection
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
    

    def get_all_objs(self, vimtype):
        # Used for creating object in a list by RetrieveContent() and append
        objs = []
        content = self.si.RetrieveContent()
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for c in container.view:
            objs.append(c)
        container.Destroy()
        return objs


    def get_all_dvs_info(self):
        all_dvs = self.get_all_objs([vim.DistributedVirtualSwitch])
        if not all_dvs:
            raise Exception("No Distributed Virtual Switches found")
        else:
            print("Distributed Virtual Switches found:")
            print(all_dvs)
            for dvs in all_dvs:
                print(f"Name: {dvs.name}")
                print(f"UUID: {dvs.uuid}")
                #print(f"Portgroups: {dvs.portgroup}")
                for i in dvs.portgroup:
                    print(f"Portgroup: {i.name}")
                print(f"Number of Ports: {dvs.summary.numPorts}")
                print(f"Number of Hosts: {dvs.summary.numHosts}")
                print(f"Description: {dvs.summary.description}")
                print(f"Config Name: {dvs.config.name}")
                print(f"Config Max Ports: {dvs.config.maxPorts}")
                print(f"Config Description: {dvs.config.description}")
                print("-" * 40)
    
    
    def create_dvs(self):
        for section in self.config.sections():
            if section.startswith('DVSwitch'):
                content = self.si.RetrieveContent()

                # Prepare the DVS config spec
                dvs_spec = vim.DistributedVirtualSwitch.ConfigSpec()
                dvs_spec.name = self.config.get(section, "name")
                dvs_spec.numStandalonePorts = self.config.getint(section, "num_port")
                dvs_spec.configVersion = self.config.get(section, "version")

                # Prepare the DVS create spec
                create_spec = vim.DistributedVirtualSwitch.CreateSpec()
                create_spec.configSpec = dvs_spec

                # Find the datacenter and network folder
                host_folder = content.rootFolder
                dc = [entity for entity in host_folder.childEntity if isinstance(entity, vim.Datacenter)][0]
                network_folder = dc.networkFolder

                # Add hosts to the DVS
                host_names = self.config.get(section, "hosts").split(',')  # List of hostnames or IPs
                host_members = []
                print(host_names)

                for host_name in host_names:
                    host = self.find_host_by_name(content, host_name.strip())
                    if host:
                        host_member_spec = vim.dvs.HostMember.ConfigSpec()
                        host_member_spec.operation = vim.ConfigSpecOperation.add
                        host_member_spec.host = host
                        host_members.append(host_member_spec)
                    else:
                        print(f"Host {host_name} not found.")
                
                if host_members:
                    dvs_spec.host = host_members  # Attach hosts to the DVS

                # Create the DVS
                task = network_folder.CreateDVS_Task(create_spec)
                self.wait_for_task(task)

                if task.info.state == 'success':
                    print(f"Successfully created DVS: {self.config.get(section, 'name')}")
                else:
                    print(f"Failed to create DVS: {self.config.get(section, 'name')}")
                    print(f"Error: {task.info.error.msg}")
                    
    
    def find_host_by_name(self, content, host_name):
        """Helper function to find a host by it's name or IP."""
        for datacenter in content.rootFolder.childEntity:
            if isinstance(datacenter, vim.Datacenter):
                for cluster in datacenter.hostFolder.childEntity:
                    if isinstance(cluster, vim.ClusterComputeResource):
                        for host in cluster.host:
                            if host.name == host_name:
                                return host
        return None
            
        
    def create_dv_portgroup(self):
        for section in self.config.sections():
            if section.startswith('DVPortgroup'):
                # You need the name of the DVSwitch that the portgroup is part of 
                dvs = self.get_obj([vim.DistributedVirtualSwitch], self.config.get(section, "dvswitchName"))
                if not dvs:
                    raise Exception(f"Distributed Virtual Switch {self.config.get(section, "dvswitchName")} not found")

                spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
                spec.name = self.config.get(section, "portgroupName")
                spec.type = vim.dvs.DistributedVirtualPortgroup.PortgroupType.earlyBinding
                # TODO
                # Make it so configparser adds the port value e.g self.config.getint(section, "ports")
                spec.numPorts = 8

                vlan_spec = vim.dvs.VmwareDistributedVirtualSwitch.VlanIdSpec()
                vlan_spec.vlanId = self.config.getint(section, "vlanID")
                vlan_spec.inherited = False
                spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
                spec.defaultPortConfig.vlan = vlan_spec

                task = dvs.AddDVPortgroup_Task([spec])
                self.wait_for_task(task)

                if task.info.state == "success":
                    print(f"Distributed Port Group {self.config.get(section, "portgroupName")} created successfully")
                else:
                    print(f"Failed to create Distributed Port Group {self.config.get(section, "portgroupName")}")
                    print(f"Error: {task.info.error.msg}")


    def wait_for_task(self, task):
        while task.info.state not in ['success', 'error']:
            continue
        return task.info.state  
    
    
    def delete_dvs(self):
        # Importen, it's not nessasary to delete portgroup first if you delete the DVS
        for section in self.config.sections():
            if section.startswith('DVSwitch'):
                content = self.si.RetrieveContent()
                
                # Find the DVS by name
                dvs = None
                for datacenter in content.rootFolder.childEntity:
                    if isinstance(datacenter, vim.Datacenter):
                        network_folder = datacenter.networkFolder
                        for network in network_folder.childEntity:
                            if isinstance(network, vim.DistributedVirtualSwitch) and network.name == self.config.get(section, "name"):
                                dvs = network
                                break
                        if dvs:
                            break
                
                if not dvs:
                    print(f"Distributed Virtual Switch '{self.config.get(section, "name")}' not found.")
                    return
                
                # Delete the DVS
                try:
                    task = dvs.Destroy_Task()
                    self.wait_for_task(task)

                    if task.info.state == 'success':
                        print(f"Successfully deleted DVS: {self.config.get(section, "name")}")
                    else:
                        print(f"Failed to delete DVS: {self.config.get(section, "name")}")
                        print(f"Error: {task.info.error.msg}")
                except Exception as e:
                    print(f"An error occurred while deleting the DVS: {str(e)}")  
                     
                    
    def delete_portgroup(self):
        # Importen, it's not nessasary to delete portgroup first if you delete the DVS
        time.sleep(10)
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
    
    
    def get_vm_name(self,vm_moid):
        # Get VM Name from moid 
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{vm_moid}"
        request = self.session.get(url)
        moid = request.json()
        # See complete information about VM in a array
        pprint.pp(moid)
        print(f"VM Name: {moid['name']}\n")
        return moid['name']
    
    
    def get_host(self):
        # Get esxi host
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/host"
        requests = self.session.get(url)
        self.__host = requests.json()
        pprint.pp(self.__host)
        for i in self.__host:
            print(i['name'])
            print(i['host'])
        return self.__host
            
    
    def get_vm_from_host(self):
        # if statement is a preflight check, because I can't get host id before get_host function
        print(self.__host)
        if self.__host == None:
            self.__host = self.get_host()
        for i in self.__host:
            print(f"\n{i}")
            url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm?hosts={i['host']}"
            requests = self.session.get(url)
            req_vm = requests.json()
            pprint.pp(req_vm)
            #print(f"MOID: {req_vm[0]['vm']}")
            # iterates through each dictionary
            for entry in req_vm:
                print(entry['vm'])
    
    
    def get_power_status_vm_guest_os(self, vm=None):
        # This is for the guest operating system (OS) NOT the VM
        # I have to make sure the function works with or whitout a value being called
        if vm is not None:
            vm_to_use = vm
            self.__vm = self.find_vm_moid(vm_to_use)
        else:
            vm_to_use = self.__vm
        if vm_to_use is None:
            raise ValueError("VM must be provided if self.__vm is not set")
        
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{self.__vm['vm']}/guest/power"
        requests = self.session.get(url)
        self.__ospower = requests.json()
        # pprint.pp(self.__vmpower)
        print(f"Power State: {self.__ospower['state']}")
        return self.__ospower
    
    
    def get_power_status_vm(self, vm=None):
        # This is for the virtual machine (VM) 
        # I have to make sure the function works with or whitout a value being called
        if vm is not None:
            vm_to_use = vm
            self.__vm = self.find_vm_moid(vm_to_use)
        else:
            vm_to_use = self.__vm
        if vm_to_use is None:
            raise ValueError("VM must be provided if self.__vm is not set")
        
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{self.__vm['vm']}/power"
        requests = self.session.get(url)
        self.__vmpower = requests.json()
        # pprint.pp(self.__vmpower)
        print(f"Power State: {self.__vmpower['state']}")
        return self.__vmpower
    
    
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

    
    def get_resource_pool(self):
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/resource-pool"
        requests = self.session.get(url)
        self.__rescpool = requests.json()
        print(self.__rescpool)
        

    def get_folder(self):
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/folder"
        requests = self.session.get(url)
        self.__folder = requests.json()
        print(self.__folder)
        
    
    def get_datastore(self):
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/datastore"
        requests = self.session.get(url)
        self.__datastore = requests.json()
        print(self.__datastore)
        
        
    def get_network_id(self):
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/network"
        requests = self.session.get(url)
        self.__networkid = requests.json()
        pprint.pp(self.__networkid)
        #print(self.__networkid)
        
    
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
                
    
    def create_vm_from_template(self, vm_name, template_name, datacenter_name, cluster_name, datastore_name, network_name, num_cpus, memory_mb, resource_pool_name=None):
        content = self.si.RetrieveContent()

        # Locate the datacenter
        datacenter = None
        for dc in content.rootFolder.childEntity:
            print(f"Found datacenter: {dc.name}")  # Debugging
            if isinstance(dc, vim.Datacenter) and dc.name == datacenter_name:
                datacenter = dc
                break
        if not datacenter:
            print(f"Datacenter '{datacenter_name}' not found.")
            return

        print(f"Using datacenter: {datacenter_name}")  # Debugging

        # Locate the cluster
        cluster = None
        for cl in datacenter.hostFolder.childEntity:
            print(f"Found cluster: {cl.name}")  # Debugging
            if isinstance(cl, vim.ClusterComputeResource) and cl.name == cluster_name:
                cluster = cl
                break
        if not cluster:
            print(f"Cluster '{cluster_name}' not found.")
            return

        print(f"Using cluster: {cluster_name}")  # Debugging

        # Locate the resource pool (optional)
        resource_pool = cluster.resourcePool
        if resource_pool_name:
            resource_pool = next((rp for rp in cluster.resourcePool.resourcePool if rp.name == resource_pool_name), cluster.resourcePool)

        # Locate the datastore
        datastore = None
        for ds in datacenter.datastoreFolder.childEntity:
            print(f"Found datastore: {ds.name}")  # Debugging
            if isinstance(ds, vim.Datastore) and ds.name == datastore_name:
                datastore = ds
                break
        if not datastore:
            print(f"Datastore '{datastore_name}' not found.")
            return

        print(f"Using datastore: {datastore_name}")  # Debugging

        # Locate the network
        network = None
        for nw in datacenter.networkFolder.childEntity:
            print(f"Found network: {nw.name}")  # Debugging
            if isinstance(nw, vim.Network) and nw.name == network_name:
                network = nw
                break
        if not network:
            print(f"Network '{network_name}' not found.")
            return

        print(f"Using network: {network_name}")  # Debugging

        # Locate the template
        template = None
        for vm in datacenter.vmFolder.childEntity:
            print(f"Found VM: {vm.name}, Is template: {vm.config.template}")  # Debugging
            if isinstance(vm, vim.VirtualMachine) and vm.name == template_name and vm.config.template:
                template = vm
                break
        if not template:
            print(f"Template '{template_name}' not found.")
            return

        print(f"Using template: {template_name}")  # Debugging

        # Create a clone spec
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool

        # Configure CPU and Memory
        configspec = vim.vm.ConfigSpec()
        configspec.numCPUs = num_cpus
        configspec.memoryMB = memory_mb

        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        clonespec.config = configspec
        clonespec.powerOn = True
        clonespec.template = False

        # Clone the VM
        task = template.CloneVM_Task(folder=datacenter.vmFolder, name=vm_name, spec=clonespec)
        self.wait_for_task(task)

        if task.info.state == 'success':
            print(f"Successfully created VM: {vm_name}")
        else:
            print(f"Failed to create VM: {vm_name}")
            print(f"Error: {task.info.error.msg}")
        
        
    def convert_vm_to_template(self, vm_name, datacenter_name):
        content = self.si.RetrieveContent()

        # Locate the datacenter
        datacenter = None
        for dc in content.rootFolder.childEntity:
            if isinstance(dc, vim.Datacenter) and dc.name == datacenter_name:
                datacenter = dc
                break
        if not datacenter:
            print(f"Datacenter '{datacenter_name}' not found.")
            return

        # Locate the VM
        vm = None
        for vm_item in datacenter.vmFolder.childEntity:
            if isinstance(vm_item, vim.VirtualMachine) and vm_item.name == vm_name:
                vm = vm_item
                break
        if not vm:
            print(f"VM '{vm_name}' not found.")
            return

        # Power off the VM if it is powered on
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            print(f"Powering off VM '{vm_name}'...")
            task = vm.PowerOffVM_Task()
            self.wait_for_task(task)
            if task.info.state != 'success':
                print(f"Failed to power off VM '{vm_name}'. Error: {task.info.error.msg}")
                return

        # Convert VM to template
        try:
            print("Attempting to convert VM to template...")
            task = vm.MarkAsTemplate()

            # Directly check if the VM is now a template
            if vm.config.template:
                print(f"Successfully converted VM '{vm_name}' to template.")
            else:
                print(f"Failed to convert VM '{vm_name}' to template. VM is not in template state.")
            
        except Exception as e:
            print(f"An error occurred while converting the VM to a template: {str(e)}")
        
        
    def add_nic_to_vm(self, vm_name, network_name, nic_type="vmxnet3"):
        # Find the VM by name
        vm = self.get_obj([vim.VirtualMachine], vm_name)
        if not vm:
            raise Exception(f"VM '{vm_name}' not found.")
        
        # Find the network by name
        network = self.get_obj([vim.Network], network_name)
        if not network:
            raise Exception(f"Network '{network_name}' not found.")
        
        # Get the VM's device configuration
        spec = vim.vm.ConfigSpec()
        
        # Create a new network adapter
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        
        # Choose the NIC type (e.g., vmxnet3, e1000, etc.)
        if nic_type == "vmxnet3":
            nic_device = vim.vm.device.VirtualVmxnet3()
        elif nic_type == "e1000":
            nic_device = vim.vm.device.VirtualE1000()
        else:
            raise ValueError(f"Unsupported NIC type: {nic_type}")
        
        nic_device.deviceInfo = vim.Description()
        nic_device.deviceInfo.label = f"Network adapter for {vm_name}"
        nic_device.deviceInfo.summary = network_name
        
        # Set the network backing
        if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
            dvs_port_connection = vim.dvs.PortConnection()
            dvs_port_connection.portgroupKey = network.key
            dvs_port_connection.switchUuid = network.config.distributedVirtualSwitch.uuid
            nic_device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nic_device.backing.port = dvs_port_connection
        else:
            nic_device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            nic_device.backing.deviceName = network_name
            nic_device.backing.network = network
        
        # Set the NIC connection options
        nic_device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_device.connectable.startConnected = True
        nic_device.connectable.allowGuestControl = True
        nic_device.connectable.connected = True
        
        nic_spec.device = nic_device
        spec.deviceChange = [nic_spec]
        
        # Reconfigure the VM to add the NIC
        task = vm.ReconfigVM_Task(spec=spec)
        self.wait_for_task(task)
        
        if task.info.state == 'success':
            print(f"NIC successfully added to VM: {vm_name}")
        else:
            raise Exception(f"Failed to add NIC to VM: {task.info.error.msg}")
            
            
    def remove_nic_from_vm(self, vm_name, nic_label="Network adapter 1"):
        # Find the VM by name
        vm = self.get_obj([vim.VirtualMachine], vm_name)
        if not vm:
            raise Exception(f"VM '{vm_name}' not found.")
        
        # Find the NIC to remove based on the label
        nic_device = None
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard) and device.deviceInfo.label == nic_label:
                nic_device = device
                break
        
        if not nic_device:
            raise Exception(f"NIC '{nic_label}' not found in VM '{vm_name}'.")
        
        # Create a spec to remove the NIC
        spec = vim.vm.ConfigSpec()
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        nic_spec.device = nic_device
        spec.deviceChange = [nic_spec]
        
        # Reconfigure the VM to remove the NIC
        task = vm.ReconfigVM_Task(spec=spec)
        self.wait_for_task(task)
        
        if task.info.state == 'success':
            print(f"NIC '{nic_label}' successfully removed from VM: {vm_name}")
        else:
            raise Exception(f"Failed to remove NIC '{nic_label}' from VM: {task.info.error.msg}")
        
    def list_vm_nics(self, vm_name):
        # Find the VM by name
        vm = self.get_obj([vim.VirtualMachine], vm_name)
        if not vm:
            raise Exception(f"VM '{vm_name}' not found.")
        
        # Loop through the devices and print network adapters
        print(f"NICs for VM '{vm_name}':")
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                print(f"Label: {device.deviceInfo.label}, MAC: {device.macAddress}, Connected: {device.connectable.connected}")
                
                
    def connect_nic_to_vm(self, vm_name, nic_label):
        # Find the VM by name
        vm = self.get_obj([vim.VirtualMachine], vm_name)
        if not vm:
            raise Exception(f"VM '{vm_name}' not found.")

        # Find the NIC by label
        nic = next((device for device in vm.config.hardware.device 
                    if isinstance(device, vim.vm.device.VirtualEthernetCard) and device.deviceInfo.label == nic_label), None)

        if not nic:
            raise Exception(f"NIC '{nic_label}' not found in VM '{vm_name}'.")

        # Create a virtual device config spec to change the connection status
        nic_spec = vim.vm.device.VirtualDeviceConfigSpec()
        nic_spec.device = nic
        nic_spec.operation = vim.vm.device.VirtualDeviceConfigSpecOperation.edit

        # Set the NIC to connected
        nic_spec.device.connectable = vim.vm.device.VirtualDeviceConnectInfo()
        nic_spec.device.connectable.connected = True

        # Create a task to connect the NIC
        task = vm.ReconfigVM_Task(spec=vim.vm.ConfigSpec(deviceChange=[nic_spec]))
        return task
    
    
    def connect_nic_to_vm(self, vm_name, network_name):
        # First, find the VM's MOID
        vm_moid = self.find_vm_moid(vm_name)

        # Find the network ID of the network you want to attach
        url_network = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/network"
        network_resp = self.session.get(url_network)
        networks = network_resp.json()

        network_id = None
        for net in networks:
            if net['name'] == network_name:
                network_id = net['network']
                break
        
        if network_id is None:
            raise Exception(f"Network '{network_name}' not found.")

        # Now, create the specification for the network adapter
        nic_spec = {
            "spec": {
                "type": "VMXNET3",  # You can change this to your desired adapter type
                "network": network_id,
                "start_connected": True,
                "wake_on_lan_enabled": False
            }
        }

        # Attach the network adapter to the VM
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{vm_moid['vm']}/hardware/ethernet"
        attach_nic_resp = self.session.post(url, json=nic_spec)

        if attach_nic_resp.status_code == 200:
            print(f"NIC connected to {vm_name} on network {network_name} successfully.")
        else:
            print(f"Failed to connect NIC to {vm_name}. Status code: {attach_nic_resp.status_code}")
            print(f"Error: {attach_nic_resp.text}")
            
            
    def get_vm_nics(self, vm):
        # List all nics from a VM in a dict
        # GET https://{server}/rest/vcenter/vm/{vm}/hardware/ethernet
        url = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{vm}/hardware/ethernet"
        request = self.session.get(url)
        request_json = request.json()
        print(request_json)
        print(request_json[0])
        nics = {}
        for nic in request.json():
            url_nic = f"https://{self.config.get('VmWare', 'vcenter')}/api/vcenter/vm/{vm}/hardware/ethernet/{nic['nic']}"
            request_nic = self.session.get(url_nic)
            #!?!
            nics[nic.get('nic')] = request_nic.json()
        #print(f"print nics: {nics}\n")
        for nic in nics:
            if nics[nic]['start_connected'] == True:
                print(f"Ayo: {nics[nic]['start_connected']}")
                print(nics[nic])
        return nics
    

    def disconnect_all_nics(self, vm):
        # Raises an exception is a nic is connected
        # TODO change to API 
        nics = self.get_vm_nics(vm)
        for nic in nics:
            if nics[nic]['start_connected'] == True:
                url_nic = f'https://{self.config.get('VmWare', 'vcenter')}/rest/vcenter/vm/{vm}/hardware/ethernet/{nic}'
                disconnect_data = {
                    "spec": {
                        "state": "CONNECTED"
                    }
                }
                request=self.session.patch(url_nic, json=disconnect_data)
                if request.status_code != 200:
                    raise Exception("Exception: {}".format(request.text))
                
    def port_find(dvs, key):
        """
        Find port by port key
        """
        obj = None
        ports = dvs.FetchDVPorts()
        for port in ports:
            if port.key == key:
                obj = port
        return obj
    
    

    def change_vm_portgroup(self, vm_name, adapter_index, new_portgroup_name):
        # Get the VM object by name
        vm = self.get_obj([vim.VirtualMachine], vm_name)

        if not vm:
            raise Exception(f"VM '{vm_name}' not found.")

        # List all devices for debugging
        self.list_vm_devices(vm)

        # Check if the specified adapter index is valid
        if adapter_index >= len(vm.config.hardware.device):
            raise Exception(f"Adapter index {adapter_index} is out of range. VM has {len(vm.config.hardware.device)} devices.")

        # Get the network adapter
        nic = vm.config.hardware.device[adapter_index]

        if not isinstance(nic, vim.vm.device.VirtualEthernetCard):
            raise Exception(f"Device at index {adapter_index} is not a network adapter.")

        # Get the new port group object
        new_portgroup = self.get_obj([vim.DistributedVirtualPortgroup], new_portgroup_name)

        if not new_portgroup:
            raise Exception(f"Port group '{new_portgroup_name}' not found.")

        # Create a VirtualDeviceConfigSpec to update the adapter
        nic_spec = vim.VirtualDeviceConfigSpec()
        nic_spec.operation = vim.VirtualDeviceConfigSpecOperation.edit
        nic_spec.device = nic

        # Update the backing with the new port group
        backing = nic.backing
        print(f"Backing type: {type(backing)}")  # Debugging line

        # Check if the backing is for a Distributed Virtual Switch
        if isinstance(backing, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
            # Create the port connection
            port_connection = vim.DistributedVirtualSwitchPortConnection(
                portgroupKey=new_portgroup.key,
                switchUuid=new_portgroup.config.distributedVirtualSwitch.uuid
            )
            
            # Assign the port connection to the backing
            backing.port = port_connection  # Fixed this line
            nic.backing = backing
        else:
            raise Exception(f"Unsupported backing type: {type(backing)}. Please check the network adapter's configuration.")

        # Create a VirtualMachineConfigSpec to apply the change
        vm_spec = vim.VirtualMachineConfigSpec()
        vm_spec.deviceChange = [nic_spec]

        # Reconfigure the VM
        task = vm.ReconfigVM_Task(vm_spec)

        # Wait for the task to finish
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