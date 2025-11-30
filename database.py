import os
import mysql.connector
from mysql.connector import pooling, Error
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Database connection pool configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'stock_monitor'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': False,
    'pool_size': 5,
    'pool_name': 'stock_monitor_pool'
}

# Create connection pool with retry logic
connection_pool = None
max_retries = 3
retry_delay = 2

for attempt in range(max_retries):
    try:
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(**DB_CONFIG)
        print("MySQL connection pool created successfully")
        break
    except Error as e:
        print(f"Attempt {attempt + 1}/{max_retries}: Error creating connection pool: {e}")
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("Failed to create connection pool after all attempts")
            connection_pool = None

def get_db_connection():
    """Get database connection from pool with retry logic and fallback"""
    global connection_pool
    
    # Try connection pool first
    if connection_pool:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = connection_pool.get_connection()
                return conn
            except Error as e:
                print(f"Pool connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    print("All pool connection attempts failed, trying direct connection")
    
    # Fallback to direct connection
    try:
        print("Attempting direct database connection...")
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Direct connection successful")
        return conn
    except Error as e:
        print(f"Direct connection failed: {e}")
        raise Exception("Unable to establish database connection")

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute database query with proper error handling"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid
            conn.commit()
        
        return result
        
    except Error as e:
        if conn:
            conn.rollback()
        print(f"Database error: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_many(query, params_list):
    """Execute multiple INSERT/UPDATE operations"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.executemany(query, params_list)
        conn.commit()
        
        return cursor.rowcount
        
    except Error as e:
        if conn:
            conn.rollback()
        print(f"Database error in execute_many: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def init_database():
    """Initialize database with tables if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Read and execute schema
        schema_file = os.path.join(os.path.dirname(__file__), 'mysql_schema.sql')
        if os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Split and execute individual statements
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            conn.commit()
            print("Database schema initialized successfully")
        else:
            print("Schema file not found, creating tables manually...")
            # Fallback to manual table creation
            create_tables_fallback(cursor)
            conn.commit()
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"Database initialization error: {e}")
        raise e

def create_tables_fallback(cursor):
    """Fallback table creation if schema file is missing"""
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS stock_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            quantity INT NOT NULL DEFAULT 0,
            selling_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            description TEXT,
            image_path VARCHAR(255),
            total_initial_value DECIMAL(10,2) DEFAULT 0.00,
            current_stock_value DECIMAL(10,2) DEFAULT 0.00,
            initial_price DECIMAL(10,2) DEFAULT 0.00,
            added_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_added_by (added_by),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT,
            item_name VARCHAR(255),
            quantity_sold INT NOT NULL DEFAULT 0,
            selling_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            image_path VARCHAR(255),
            user_id INT,
            user_name VARCHAR(50),
            user_email VARCHAR(100),
            place VARCHAR(100),
            sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_item_id (item_id),
            INDEX idx_user_id (user_id),
            INDEX idx_sold_at (sold_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS investment_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_type ENUM('invest', 'withdraw') NOT NULL,
            amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            description TEXT,
            investor_name VARCHAR(100),
            investor_email VARCHAR(100),
            investor_phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_investor_name (investor_name),
            INDEX idx_transaction_type (transaction_type),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS wages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_name VARCHAR(100) NOT NULL,
            amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            wage_type VARCHAR(50),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_employee_name (employee_name),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)

def test_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] == 1
    except Error as e:
        print(f"Connection test failed: {e}")
        return False
