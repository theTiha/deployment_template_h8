import sqlite3
import os

# Path for the database
db_path = '/Users/timhansen/my_repos/create_customer_H8/database/database.db'

def create_database(db_path):
    # Check if the database exists
    if not os.path.exists(db_path):
        # Connection to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the table with the specified columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_info (
                id INTEGER PRIMARY KEY,
                domain_name TEXT NOT NULL,
                subnet TEXT NOT NULL
            )
        ''')
        
        # Insert dummy entry into the table
        cursor.execute('''
            INSERT INTO network_info (domain_name, subnet)
            VALUES ('ggob.gg', '192.168.0.0/24')
        ''')
        cursor.execute('''
            INSERT INTO network_info (domain_name, subnet)
            VALUES ('redrum.gg', '192.168.1.0/24')
        ''')
        
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print(f'Database created and entry added at {db_path}')
    else:
        print(f'Database already exists at {db_path}')

def dump_database(db_path):
    # Check if the database exists
    if os.path.exists(db_path):
        # Create a connection to the SQLite database
        conn = sqlite3.connect(db_path)
        
        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()
        
        # Retrieve all data from the network_info table
        cursor.execute('SELECT * FROM network_info')
        rows = cursor.fetchall()
        
        # Print the data
        for row in rows:
            print(f'ID: {row[0]}, Domain Name: {row[1]}, Subnet: {row[2]}')
        
        # Close the connection
        conn.close()
    else:
        print(f'Database does not exist at {db_path}')

# Create the database and insert the initial entry
create_database(db_path)
# Dump the database contents
dump_database(db_path)