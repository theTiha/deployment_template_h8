
import lib.CreateLDAP as CreateLDAP
import lib.FileManagement as FileManagement
if __name__ == "__main__":
    ldap_create_files = CreateLDAP.Ldap()
    # print("Test ok...")
    # sys.exit(0)  # Exit success
    
    
    #  LDAP configuration

    # ldap_create_files.create_customer_ou()
    # ldap_create_files.create_customer_vpn()
    # ldap_create_files.create_customer_users()


    ldap_create_files.delete_customer_users()
    ldap_create_files.delete_customer_ldap()