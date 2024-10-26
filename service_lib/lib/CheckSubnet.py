import ipaddress
#import sqlite3

class SubnetChecker:
    def __init__(self, db_conn):
        # Initialize with a connection to the existing database
        self.conn = db_conn

    # Function to get the customerId from the config file
    def get_customerId_from_config(self, config):
        customer_info = config['Customerinfo']
        customerId = int(customer_info['customerId'])
        return customerId

    # Function to check if customerId already exists in the database
    def customer_id_exists(self, customerId):
        result = self.conn.execute('SELECT customerId FROM Customer WHERE customerId = ?;', (customerId,)).fetchone()
        return result is not None

    # Function to get the network from the config file
    def get_network_from_config(self, config):
        customer_info = config['Customerinfo']
        network = customer_info['network']  # e.g., '192.168.2.0'
        return network

    # Function to get all existing subnets from the database
    def get_existing_subnets(self):
        with self.conn:
            # Query all customer subnets (network) from the database
            subnets = self.conn.execute('SELECT network FROM Customer').fetchall()
            return [row[0] for row in subnets]

    # Function to check if a new subnet overlaps with any existing ones
    def check_for_overlapping_subnet(self, new_network):
        # Convert the new network string to an ip_network object with /24 CIDR
        new_subnet = ipaddress.ip_network(f"{new_network}/24", strict=False)

        # Fetch existing subnets
        existing_subnets = self.get_existing_subnets()

        # Loop through all existing subnets and check for overlap
        for subnet_str in existing_subnets:
            existing_subnet = ipaddress.ip_network(f"{subnet_str}/24", strict=False)
            if new_subnet.overlaps(existing_subnet):
                return True  # Overlap found

        return False  # No overlap

    # Function to validate the customerId and subnet
    def validate_customer_and_subnet(self, config):
        new_network = self.get_network_from_config(config)
        new_customerId = self.get_customerId_from_config(config)

        # Check if customerId already exists
        if self.customer_id_exists(new_customerId):
            print(f"Error: The customerId {new_customerId} already exists in the database.")
            return False

        # Check if the new subnet overlaps with any existing subnets
        if self.check_for_overlapping_subnet(new_network):
            print(f"Error: The subnet {new_network}/24 overlaps with an existing subnet.")
            return False

        print(f"The subnet {new_network}/24 and customerId {new_customerId} are available.")
        return True