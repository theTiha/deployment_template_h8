import lib.PackerSdk as PackerSdk  

if __name__ == "__main__":
    packer = PackerSdk.Packersdk()
    packer.destroy_vm_host()
    packer.delete_portgroup()