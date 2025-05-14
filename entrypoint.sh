#!/bin/bash
set -e

echo "Entrypoint script starting..."

# Function to initialize the databases
initialize_databases() {
  echo "Initializing databases..."
  python - <<EOF
import psycopg2
import time

# Connection parameters
host = "postgres"
port = "5432"
user = "postgres"
password = "password"
databases = ["birthday_bot_dev", "birthday_bot_test", "birthday_bot_prod"]

print(f"Connecting to PostgreSQL server: {host}:{port}")

# Function to create a database if it doesn't exist
def create_database_if_not_exists(db_name):
    try:
        # Connect to the default postgres database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"
        )
        conn.autocommit = True
        
        # Check if database exists
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cursor.fetchone():
                print(f"Creating database: {db_name}")
                cursor.execute(f"CREATE DATABASE {db_name}")
                print(f"Database {db_name} created successfully")
            else:
                print(f"Database {db_name} already exists")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating database {db_name}: {e}")
        return False

# Try to connect to the PostgreSQL server with retries
max_retries = 10
retry_delay = 5

for attempt in range(1, max_retries + 1):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"
        )
        conn.close()
        print("Successfully connected to PostgreSQL server")
        
        # Create all required databases
        for db in databases:
            create_database_if_not_exists(db)
        
        break
    except Exception as e:
        print(f"Connection attempt {attempt}/{max_retries} failed: {e}")
        if attempt < max_retries:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("Failed to connect to PostgreSQL after maximum retries")
            raise
EOF
}

# Initialize databases
initialize_databases

# Start the application
echo "Starting Birthday Bot..."
exec python main.py 