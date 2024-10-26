import lib.CreateDNS as CreateDNS
import lib.NsupdateClass as NsupdateClass
import lib.FileManagement as FileManagement
import lib.CustomerDB as CustomerDB
import lib.CheckSubnet as CheckSubnet
import lib.CreateLDAP as CreateLDAP


if __name__ == "__main__":
    # Create an instance of the Database class
    customer_db = CustomerDB.CustomerDatabase()
    subnet_checker = CheckSubnet.SubnetChecker(customer_db.conn)
    
    if subnet_checker.validate_customer_and_subnet(customer_db.config):
        # If the subnet is valid, then add the customer
        customer_db.add_customer_from_config()
        customer_db.dump_database()
        customer_db.close()
        
        # ______________ Create an instance of the DNS class_________________________
        build_zone_files = CreateDNS.Dns()
        add_records = NsupdateClass.Nsupdate()
        push_files = FileManagement.Pushfile()
        ldap_create_files = CreateLDAP.Ldap()

        # # Create zone files in this repo using (CreateDNS.py)
        build_zone_files.create_zones()
        build_zone_files.create_sec_zones()
        build_zone_files.create_forward()
        build_zone_files.create_reverse()

        # Push zone files from repo to remote server (FileManagement.py)
        push_files.upload_file_scp()
        push_files.upload_file_sec_scp()
        add_records.restart_bind9_service()

        # # Create PTR and A records using NSupdate (NsupdateClass.py)
        add_records.add_ptr_records()
        add_records.add_A_records()
        add_records.restart_bind9_service()
        push_files.restart_bind9_service('dnsServer02')
        push_files.rndc_retransfer()
        
        ldap_create_files.create_customer_ou()
        ldap_create_files.create_customer_vpn()
        ldap_create_files.create_customer_users()
        
        
    else:
        print("Failed to add customer due to subnet conflict.")

