import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'techhub.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if client_id already exists in projects
cursor.execute('PRAGMA table_info(projects)')
cols = [c[1] for c in cursor.fetchall()]
print('Current projects columns:', cols)

if 'client_id' not in cols:
    cursor.execute('ALTER TABLE projects ADD COLUMN client_id INTEGER')
    conn.commit()
    print('Added client_id column to projects')
else:
    print('client_id already exists in projects')

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print('All tables:', tables)

# Ensure new tables exist
for table in ['clients', 'contracts', 'tickets']:
    if table in tables:
        print(f'Table {table} exists')
    else:
        print(f'Table {table} MISSING!')

conn.close()
print('Database fix completed.')
