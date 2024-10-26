from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException
import configparser
import os

class Ldap:
    def __init__(self) -> None:
        print(f"Current working directory: {os.getcwd()}")
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'hostconfig.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
            os.path.join(config_folder, 'ldapusers.cfg'),
        ]      
        self.config.read(config_files)
        self.ldapuser = self.config.get('Scriptconfig','ldapAdminDn')
        self.ldappass = self.config.get('Scriptconfig','ldapAdminPassword')
        self.ldapserver = self.config.get('Scriptconfig','ldapServer')
        self.uniqueid = self.config.get('Customerinfo','uniqueId')
        self.customername = self.config.get('Customerinfo','customerName')
        self.ldapgid = self.config.get('Customergroup','ldapGid')
        self.subdomain = self.config.get('Customerinfo','subDomainName')
        self.ou_customer_dn = f'ou={self.uniqueid},ou=customers,dc=cloudcubes,dc=gg'


    
    def ldap_connection(self):
        # Connect to the LDAP server
        server = Server(self.ldapserver, get_info=ALL)
        conn = Connection(server, self.ldapuser, self.ldappass, auto_bind=True)
        
        return conn



    def create_customer_ou(self):

        try:        
            cn_admins_dn = f'cn={self.uniqueid}_admins,{self.ou_customer_dn}'
            conn = self.ldap_connection()


            ou_customer_attributes = {
                'objectClass': ['top', 'organizationalUnit'],
                'description': self.customername,
                'ou': self.uniqueid
            }

            cn_admins_attributes = {
                'objectClass': ['top', 'posixGroup'],
                'cn': f'{self.uniqueid}_admins',
                'gidNumber': self.ldapgid
            }

            # Add OU for the customer
            conn.add(self.ou_customer_dn, attributes=ou_customer_attributes)
            if conn.result['description'] == 'success':
                print(f"OU {self.ou_customer_dn} created successfully.")
            else:
                print(f"Failed to create OU: {conn.result}")

            # Add Admins group
            conn.add(cn_admins_dn, attributes=cn_admins_attributes)
            if conn.result['description'] == 'success':
                print(f"Posix GROUP {cn_admins_dn} created successfully.")
            else:
                print(f"Failed to create posix GROUP: {conn.result}")

        except Exception as e:
            print(f"error: {e}")

        finally:
            conn.unbind()

    
    def create_customer_vpn(self):
        cn_vpn_dn = f'cn={self.uniqueid}_vpn,{self.ou_customer_dn}'
        
        list_member = []
        for section in self.config.sections():
            if section.startswith('User'):  
                login_uid = self.config.get(section, 'login') 
                list_member.append(f'uid={login_uid},ou={self.uniqueid},ou=customers,dc=cloudcubes,dc=gg')
        
        try:
            conn = self.ldap_connection()
          
            cn_vpn_attributes = {
                    'objectClass': ['groupOfNames'],
                    'cn': f'{self.uniqueid}_vpn',    
                    'member': list_member
                }

            conn.add(cn_vpn_dn, attributes=cn_vpn_attributes)
            if conn.result['description'] == 'success':
                print(f"GROUP {cn_vpn_dn} created successfully.")
            else:
                print(f"Failed to create GROUP: {conn.result}")

        except Exception as e:
            print(f"error: {e}")

        finally:
            conn.unbind()


    def create_customer_users(self):
        for section in self.config.sections():
            if section.startswith('User'):
                login_uid = self.config.get(section, 'login')     
                user_dn = f'uid={login_uid},{self.ou_customer_dn}'
                first_name = self.config.get(section, 'firstName') 
                sur_name = self.config.get(section, 'surName') 
                user_uid_nr = self.config.get(section, 'userUidNr') 
                user_pass = self.config.get(section, 'ldapPass') 
                

                user_attributes = {
                'objectClass': ['inetOrgPerson', 'posixAccount', 'shadowAccount'],
                'cn': f'{first_name} {sur_name}',
                'gidNumber': self.ldapgid,
                'homeDirectory': f'/home/{login_uid}',
                'sn': sur_name,
                'uid': login_uid,
                'uidNumber': user_uid_nr,
                'displayName': f'{first_name} {sur_name}',
                'givenName': first_name,
                'mail' : f'{login_uid}@{self.subdomain}.cloudcubes.gg',
                'userPassword' :user_pass,
                'loginShell' :'/bin/bash'
            }

                try:
                
                    conn = self.ldap_connection()

                    conn.add(user_dn, attributes=user_attributes)

                    if conn.result['description'] == 'success':
                        print(f"USER {user_dn} created successfully.")
                    else:
                        print(f"Failed to create USER: {conn.result}")

                except Exception as e:
                    print(f"error: {e}")

                finally:
                    conn.unbind()



    def delete_customer_ldap(self):

        try:        
            ou_customer_dn = f'ou={self.uniqueid},ou=customers,dc=cloudcubes,dc=gg'
            cn_admins_dn = f'cn={self.uniqueid}_admins,{ou_customer_dn}'
            cn_vpn_dn = f'cn={self.uniqueid}_vpn,{self.ou_customer_dn}'

            conn = self.ldap_connection()

            conn.delete(cn_vpn_dn)
            if conn.result['description'] == 'success':
                print(f"OU {cn_vpn_dn} deleted successfully.")
            else:
                print(f"Failed to delete OU: {conn.result}")

            conn.delete(cn_admins_dn)
            if conn.result['description'] == 'success':
                print(f"OU {cn_admins_dn} deleted successfully.")
            else:
                print(f"Failed to delete OU: {conn.result}")
            
            conn.delete(ou_customer_dn)
            if conn.result['description'] == 'success':
                print(f"OU {ou_customer_dn} deleted successfully.")
            else:
                print(f"Failed to delete OU: {conn.result}")



        except Exception as e:
            print(f"error: {e}")

        finally:
            conn.unbind()

    def delete_customer_users(self):

               

        try: 

            for section in self.config.sections():
                if section.startswith('User'):
                    login_uid = self.config.get(section, 'login')     
                    user_dn = f'uid={login_uid},{self.ou_customer_dn}'

                    

                    conn = self.ldap_connection()

                    conn.delete(user_dn)
                    if conn.result['description'] == 'success':
                        print(f"user {user_dn} deleted successfully.")
                    else:
                        print(f"Failed to delete user: {conn.result}")


        except Exception as e:
            print(f"error: {e}")

        finally:
            conn.unbind()