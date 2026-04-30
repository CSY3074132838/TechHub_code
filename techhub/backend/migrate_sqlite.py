import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'techhub.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Helper function to check if column exists
def column_exists(table, col):
    cursor.execute(f'PRAGMA table_info({table})')
    return col in [c[1] for c in cursor.fetchall()]

# 1. Add missing columns to roles table
if not column_exists('roles', 'data_scope'):
    cursor.execute("ALTER TABLE roles ADD COLUMN data_scope VARCHAR(20) DEFAULT 'self'")
    print("Added roles.data_scope")

if not column_exists('roles', 'data_scope_custom'):
    cursor.execute("ALTER TABLE roles ADD COLUMN data_scope_custom JSON DEFAULT '[]'")
    print("Added roles.data_scope_custom")

# 2. Add missing columns to users table
if not column_exists('users', 'permission_version'):
    cursor.execute("ALTER TABLE users ADD COLUMN permission_version INTEGER DEFAULT 1")
    print("Added users.permission_version")

# 3. Add missing columns to projects table
if not column_exists('projects', 'client_id'):
    cursor.execute("ALTER TABLE projects ADD COLUMN client_id INTEGER")
    print("Added projects.client_id")

# 4. Create clients table if not exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
if not cursor.fetchone():
    cursor.execute('''
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            industry VARCHAR(50),
            contact_name VARCHAR(50),
            contact_phone VARCHAR(20),
            contact_email VARCHAR(120),
            address TEXT,
            status VARCHAR(20) DEFAULT 'potential',
            level VARCHAR(20) DEFAULT 'b',
            remark TEXT,
            manager_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("Created clients table")

# 5. Create contracts table if not exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contracts'")
if not cursor.fetchone():
    cursor.execute('''
        CREATE TABLE contracts (
            id INTEGER PRIMARY KEY,
            contract_no VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            client_id INTEGER NOT NULL,
            project_id INTEGER,
            amount NUMERIC(12, 2),
            sign_date DATE,
            start_date DATE,
            end_date DATE,
            status VARCHAR(20) DEFAULT 'draft',
            payment_terms TEXT,
            content TEXT,
            created_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("Created contracts table")

# 6. Create tickets table if not exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tickets'")
if not cursor.fetchone():
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            ticket_no VARCHAR(50) UNIQUE NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            client_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'open',
            priority VARCHAR(20) DEFAULT 'medium',
            assignee_id INTEGER,
            reporter_id INTEGER NOT NULL,
            resolved_at DATETIME,
            resolution TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("Created tickets table")

# 7. Create audit_logs table if not exists (from iteration 2)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
if not cursor.fetchone():
    cursor.execute('''
        CREATE TABLE audit_logs (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username VARCHAR(80) NOT NULL,
            action VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50),
            resource_id INTEGER,
            detail JSON DEFAULT '{}',
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            status VARCHAR(20) DEFAULT 'success',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("Created audit_logs table")

conn.commit()
conn.close()
print("Migration completed successfully!")
