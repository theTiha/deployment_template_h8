import os
import sqlite3
import configparser

class CustomerDatabase:
    def __init__(self):
        # Initialize configparser to read multiple config files
        self.config = configparser.ConfigParser()
        config_folder = os.path.join(os.path.dirname(__file__), '../..', 'config_files')
        config_files = [
            os.path.join(config_folder, 'hostconfig.cfg'),
            os.path.join(config_folder, 'credentials.cfg'),
        ]
        self.config.read(config_files)

        # Initialize the database connection and create tables
        self.conn = self.initialize_database()
        self.create_tables()

    def initialize_database(self):
        # Use the absolute path '/data/customer_database' for the database directory
        db_dir = self.config.get('Scriptconfig', 'sqlitePath')
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        # Create or connect to the SQLite database in /data/customer_database
        db_path = os.path.join(db_dir, 'customers.db')
        conn = sqlite3.connect(db_path)
        return conn

    # Create tables if they don't exist
    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS Customer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customerId INTEGER UNIQUE,
                    customerName TEXT,
                    domainName TEXT,
                    subDomainName TEXT,
                    enviroment TEXT,
                    network TEXT
                );
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS Host (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customerId INTEGER,
                    hostName TEXT,
                    ipAdress TEXT,
                    vlanID INTEGER,
                    FOREIGN KEY (customerId) REFERENCES Customer (id),
                    UNIQUE(customerId, hostName)
                );
            ''')

    # Check if the customer exists in the DB using customerId
    def customer_exists(self, customerId):
        result = self.conn.execute('SELECT id FROM Customer WHERE customerId = ?;', (customerId,)).fetchone()
        return result is not None

    # Function to check if a host already exists in the DB
    def host_exists(self, customer_db_id, hostName):
        result = self.conn.execute('SELECT id FROM Host WHERE customerId = ? AND hostName = ?;', 
                                   (customer_db_id, hostName)).fetchone()
        return result is not None

    # Function to parse the config file and insert customer and host data
    def add_customer_from_config(self):
        # Extract customer info from hostconfig.cfg
        customer_info = self.config['Customerinfo']
        customerName = customer_info['customerName']
        customerId = int(customer_info['customerId'])
        domainName = customer_info['domainName']
        subDomainName = customer_info['subDomainName']
        enviroment = customer_info['enviroment']
        network = customer_info['network']

        # Check if customer already exists
        if not self.customer_exists(customerId):
            # Insert customer into the database
            with self.conn:
                self.conn.execute('''
                    INSERT INTO Customer (customerId, customerName, domainName, subDomainName, enviroment, network)
                    VALUES (?, ?, ?, ?, ?, ?);
                ''', (customerId, customerName, domainName, subDomainName, enviroment, network))
                print(f"Customer '{customerName}' added to the database.")
        else:
            print(f"Customer '{customerName}' already exists in the database.")

        # Get the customer ID for foreign key reference
        customer_db_id = self.conn.execute('SELECT id FROM Customer WHERE customerId = ?;', (customerId,)).fetchone()[0]

        # Insert host info from hostconfig.cfg file
        for section in self.config.sections():
            if section.startswith('Host'):
                host_info = self.config[section]
                hostName = host_info['hostName']
                ipAdress = host_info['ipAdress']
                vlanID = int(host_info['vlanID'])

                # Check if host already exists
                if not self.host_exists(customer_db_id, hostName):
                    self.conn.execute('''
                        INSERT INTO Host (customerId, hostName, ipAdress, vlanID)
                        VALUES (?, ?, ?, ?);
                    ''', (customer_db_id, hostName, ipAdress, vlanID))
                    print(f"Host '{hostName}' added to the database.")
                else:
                    print(f"Host '{hostName}' already exists in the database.")
       
                    
    def list_hosts_for_customer(self, customerId):
        # Get the customer db_id from the Customer table
        result = self.conn.execute('SELECT id FROM Customer WHERE customerId = ?;', (customerId,)).fetchone()

        if result:
            customer_db_id = result[0]

            # Fetch and display the hosts associated with the customer
            print(f"\nHosts for Customer ID {customerId}:")
            hosts = self.conn.execute('SELECT * FROM Host WHERE customerId = ?;', (customer_db_id,)).fetchall()
            
            if hosts:
                for host in hosts:
                    print(host)
            else:
                print(f"No hosts found for customer ID {customerId}.")
        else:
            print(f"Customer with customerId {customerId} does not exist.")
    

    # Function to delete customer and their hosts
    def delete_customer(self):
        customer_id = self.config.get('Customerinfo', 'customerId')
        # Get the customer db_id from the Customer table
        result = self.conn.execute('SELECT id FROM Customer WHERE customerId = ?', (customer_id,)).fetchone()
        
        if result:
            customer_db_id = result[0]

            # Delete hosts first
            with self.conn:
                self.conn.execute('DELETE FROM Host WHERE customerId = ?', (customer_db_id,))
                # Delete customer
                self.conn.execute('DELETE FROM Customer WHERE id = ?', (customer_db_id,))
                print(f"Customer with customerId {customer_id} and associated hosts have been deleted.")
        else:
            print(f"Customer with customerId {customer_id} does not exist.")

    # Dump the database 
    def dump_database(self):
        with self.conn:
            # Dump customers
            print("\nDump Customers:")
            for row in self.conn.execute('SELECT * FROM Customer;'):
                print(row)

            # Dump hosts
            print("\nDump Hosts:")
            for row in self.conn.execute('SELECT * FROM Host;'):
                print(row)

    # Close the database connection
    def close(self):
        self.conn.close()