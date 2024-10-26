import lib.CreateDNS as CreateDNS
import lib.NsupdateClass as NsupdateClass
import lib.FileManagement as FileManagement
import lib.CustomerDB as CustomerDB
import lib.CreateLDAP as CreateLDAP


if __name__ == "__main__":
    # Create an instance of the Database class
    customer_db = CustomerDB.CustomerDatabase()

    # ______________ Create an instance of the DNS class_________________________
    delete_records = NsupdateClass.Nsupdate()
    delete_files_on_dns = FileManagement.Pushfile()
    destrue_zone_files = CreateDNS.Dns()
    ldap_create_files = CreateLDAP.Ldap()

    # # Delete PTR and A records using NSupdate (NsupdateClass.py)
    delete_records.delete_ptr_records()
    delete_records.delete_A_record()

    # # Delete files located on server using (FileManagement.py)
    delete_files_on_dns.delete_files()
    delete_files_on_dns.delete_files_sec()
    delete_files_on_dns.delete_files()
    delete_files_on_dns.delete_files_sec()
    delete_files_on_dns.delete_path_file()

    # # Delete files located in this repo using (CreateDNS.py)
    destrue_zone_files.delete_zones()
    destrue_zone_files.delete_reverse()
    destrue_zone_files.delete_forward()
    
    # # Cleanup LDAP 
    ldap_create_files.delete_customer_users()
    ldap_create_files.delete_customer_ldap()
    
    # Cleanup the Database
    customer_db.delete_customer()
    customer_db.dump_database()
    customer_db.close()
