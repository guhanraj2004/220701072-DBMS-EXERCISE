import psycopg2

# Connect to PostgreSQL database
# Replace 'your_connection_string' with the connection string provided by ElephantSQL
conn_string = 'postgres://ermmmhea:o3nwulL9fesvtV9VHHcPAiXIlC6irytd@snuffleupagus.db.elephantsql.com/ermmmhea'
conn = psycopg2.connect(conn_string)

# Create a cursor object to execute SQL queries
cur = conn.cursor()

# SQL statement to create the 'stock' table
create_table_query = '''
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    ip_address VARCHAR(50),
    action TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

# Execute the SQL statement to create the table
cur.execute(create_table_query)

# Commit the transaction
conn.commit()

# Close cursor and connection
cur.close()
conn.close()
