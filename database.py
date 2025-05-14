import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database')

load_dotenv()

# Get environment - default to dev for initial connection
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
logger.info(f"Current environment: {ENVIRONMENT}")

# Override to dev if database doesn't exist yet
DB_NAME = f"birthday_bot_{ENVIRONMENT.lower()}"

# Database config
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": "postgres",  # Hardcoded for reliability
    "password": "password",  # Hardcoded for reliability
    "database": "birthday_bot_dev"  # Always use dev database first
}

# Log connection parameters (without password)
logger.info(f"Connecting to database at {DB_CONFIG['host']}:{DB_CONFIG['port']} as {DB_CONFIG['user']}")
logger.info(f"Using database: {DB_CONFIG['database']}")

# Create connection pool with retry
def create_connection_pool(max_retries=5, retry_delay=5):
    """Create database connection pool with retries"""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Connection attempt {attempt}/{max_retries}")
            pool_obj = pool.SimpleConnectionPool(
                1, 10,
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                database=DB_CONFIG["database"]
            )
            logger.info("Database connection pool created successfully")
            return pool_obj
        except Exception as e:
            logger.error(f"Connection attempt {attempt} failed: {e}")
            
            # Try basic connection to see if server is reachable
            try:
                logger.info("Trying basic connection to PostgreSQL server...")
                conn = psycopg2.connect(
                    host=DB_CONFIG["host"],
                    user=DB_CONFIG["user"],
                    password=DB_CONFIG["password"],
                )
                logger.info("Basic connection successful")
                
                # Check if database exists
                conn.autocommit = True
                with conn.cursor() as cur:
                    # Create the dev database if it doesn't exist
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", ("birthday_bot_dev",))
                    if cur.fetchone() is None:
                        logger.info("Creating birthday_bot_dev database")
                        cur.execute("CREATE DATABASE birthday_bot_dev")
                    
                    # Also create test and prod databases if they don't exist
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", ("birthday_bot_test",))
                    if cur.fetchone() is None:
                        logger.info("Creating birthday_bot_test database")
                        cur.execute("CREATE DATABASE birthday_bot_test")
                        
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", ("birthday_bot_prod",))
                    if cur.fetchone() is None:
                        logger.info("Creating birthday_bot_prod database")
                        cur.execute("CREATE DATABASE birthday_bot_prod")
                
                conn.close()
                logger.info(f"Retrying connection to database {DB_CONFIG['database']} in {retry_delay} seconds")
            except Exception as e2:
                logger.error(f"Basic connection failed: {e2}")
            
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Maximum retry attempts reached")
                return None

# Initialize connection pool with retries
connection_pool = create_connection_pool()

def get_connection():
    """Get a connection from the pool"""
    if connection_pool:
        try:
            return connection_pool.getconn()
        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            return None
    else:
        logger.error("Connection pool is not initialized")
        return None

def release_connection(conn):
    """Return a connection to the pool"""
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")

def initialize_database():
    """Initialize database schema for a guild"""
    conn = get_connection()
    if not conn:
        logger.error("Cannot initialize database - no connection available")
        return
    
    try:
        with conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    birthday VARCHAR(4) NOT NULL,
                    birth_year INTEGER,
                    announce_in_servers INTEGER DEFAULT 1,
                    receive_dms INTEGER DEFAULT 1,
                    share_age INTEGER DEFAULT 0,
                    UNIQUE (user_id, guild_id)
                )
            """)
            
            # Create settings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    guild_id BIGINT NOT NULL,
                    setting VARCHAR(50) NOT NULL,
                    value TEXT,
                    PRIMARY KEY (guild_id, setting)
                )
            """)
            
            conn.commit()
            logger.info("Database tables initialized successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Database initialization error: {e}")
    finally:
        release_connection(conn)

def close_all_connections():
    """Close all database connections"""
    if connection_pool:
        try:
            connection_pool.closeall()
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
    else:
        logger.warning("No connection pool to close") 