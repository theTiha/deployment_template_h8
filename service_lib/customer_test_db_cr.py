import lib.CheckSubnet as CheckSubnet
import lib.CustomerDB as CustomerDB
import sys

if __name__ == "__main__":
    # Create an instance of the Database class
    customer_db = CustomerDB.CustomerDatabase()
    subnet_checker = CheckSubnet.SubnetChecker(customer_db.conn)
    
    if subnet_checker.validate_customer_and_subnet(customer_db.config):
        # If the subnet is valid, then add the customer
        customer_db.add_customer_from_config()
        customer_db.dump_database()
        customer_db.close()
        sys.exit(0)  # Exit success
    else:
        print("Customer is already built - breaking out.")
        sys.exit(1)  # Exit with status 1 to indicate failure