import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from contextlib import contextmanager

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def get_db_path():
    return os.environ.get('DB_PATH', 'uniform_inventory.db')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize the database with proper error handling"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create uniforms table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS uniforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                size TEXT NOT NULL,
                color TEXT NOT NULL,
                current_stock INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 0
            )
            ''')
            
            # Create staff table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL
            )
            ''')
            
            # Create stock_movements table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uniform_id INTEGER,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (uniform_id) REFERENCES uniforms (id)
            )
            ''')
            
            # Create staff_assignments table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER,
                uniform_id INTEGER,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                returned_date TIMESTAMP,
                status TEXT DEFAULT 'assigned',
                FOREIGN KEY (staff_id) REFERENCES staff (id),
                FOREIGN KEY (uniform_id) REFERENCES uniforms (id)
            )
            ''')
            
            # Create indexes for frequently queried columns
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_uniforms_type ON uniforms(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_staff_department ON staff(department)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(date)')
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db() 