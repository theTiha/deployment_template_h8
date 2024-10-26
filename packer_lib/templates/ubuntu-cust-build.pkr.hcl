// Packer configuration for cloning a VM and setting a static IP
packer {
  required_version = ">= 1.10.0"
  required_plugins {
    vsphere = {
      source  = "github.com/hashicorp/vsphere"
      version = ">= 1.3.0"
    }
  }
}

locals {
  #vm_name           = "${var.new_hostname}"
  build_by          = "Built by: HashiCorp Packer ${packer.version}"
  build_date        = formatdate("YYYY-MM-DD hh:mm ZZZ", timestamp())
  build_description = "VM Name: ${var.new_hostname}\nBuilt on: ${local.build_date}\n${local.build_by}"
  invoke_sudo       = "echo '${var.ssh_password}' |"
}

source "vsphere-clone" "vm_clone" {
  vcenter_server      = var.vcenter
  username            = var.username
  password            = var.password
  insecure_connection = true

  datacenter          = var.datacenter_name
  cluster             = var.cluster_name
  template            = var.template_name
  vm_name             = var.new_hostname
  datastore           = var.datastore_name
  folder              = var.vm_folder
  network             = var.network_name
  convert_to_template = false
  linked_clone        = false

  communicator     = "ssh"
  ssh_username     = var.ssh_username
  ssh_password     = var.ssh_password
  ssh_wait_timeout = "3m"

  notes = local.build_description
}

build {
  sources = ["source.vsphere-clone.vm_clone"]

  provisioner "shell" {
    inline = [
      "echo 'Configuring networking...'",
       "${local.invoke_sudo} sudo -S hostnamectl set-hostname ${var.new_hostname}",
       "echo 'Updating IP and gateway in /etc/netplan/50-cloud-init.yaml...'",
      # Replace the IP address
      "${local.invoke_sudo} sudo -S sed -i 's|${var.template_ip}/${var.netmask}|${var.new_ip}/${var.netmask}|g' /etc/netplan/50-cloud-init.yaml",
      # Replace the gateway
      "${local.invoke_sudo} sudo -S sed -i 's|via: ${var.template_gw}|via: ${var.new_gateway}|g' /etc/netplan/50-cloud-init.yaml",      "echo 'applying networking...'",
      # insert login permission for customer
      "${local.invoke_sudo} sudo -S sed -i 's|customer|${var.unique_id}_admins|g' /etc/security/access.conf",      "echo 'fixing access'",
      # Create the sudoers.d file with the required line
      "${local.invoke_sudo} sudo -S bash -c 'echo \"%${var.unique_id}_admins ALL=(ALL:ALL) ALL\" > /etc/sudoers.d/${var.unique_id}_admins'",
      "echo 'Sudoers file created...'",
      # Set permissions on the sudoers.d file
      "${local.invoke_sudo} sudo -S chmod 440 /etc/sudoers.d/${var.unique_id}_admins",
      "echo 'Permissions set to 440 on /etc/sudoers.d/${var.unique_id}_admins...'",
    ]
  }


  # post-processor "manifest" {
  #   output     = "${path.cwd}/manifests/${var.new_hostname}.json"
  #   strip_path = true
  #   custom_data = {
  #     build_date = local.build_date
  #     build_by   = local.build_by
  #   }
  # }
}



# host_variables

variable "new_hostname" {
  type = string
}

variable "vm_folder" {
  type = string
}

variable "network_name" {
  type = string
}

variable "new_ip" {
  type = string
}

variable "new_gateway" {
  type = string
}

variable "dns1" {
  type = string
}

variable "dns2" {
  type = string
}

variable "unique_id" {
  type = string
}


# constant_variables

variable "vcenter" {
  type = string
}

variable "username" {
  type = string
}

variable "password" {
  type = string
}

variable "template_name" {
  type = string
}

variable "datacenter_name" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "datastore_name" {
  type = string
}

variable "ssh_username" {
  type = string
}

variable "ssh_password" {
  type = string
}

variable "netmask" {
  type = string
}

variable "template_ip" {
  type = string
}

variable "template_gw" {
  type = string
}