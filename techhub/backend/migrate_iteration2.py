"""
【第二次迭代】数据库迁移脚本
添加部门表、考勤表、假期余额表、工时记录表，并扩展用户表字段
作者: 于然
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'techhub.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()


def column_exists(table, col):
    cursor.execute(f'PRAGMA table_info({table})')
    return col in [c[1] for c in cursor.fetchall()]


def table_exists(table):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None


# ==================== 1. 扩展 users 表字段（第二次迭代）====================
user_new_columns = [
    ('employee_no', "VARCHAR(50)"),
    ('employee_status', "VARCHAR(20) DEFAULT 'probation'"),
    ('entry_date', "DATE"),
    ('probation_end_date', "DATE"),
    ('leave_date', "DATE"),
    ('id_card', "VARCHAR(18)"),
    ('gender', "VARCHAR(10)"),
    ('birthday', "DATE"),
    ('native_place', "VARCHAR(100)"),
    ('address', "TEXT"),
    ('education', "VARCHAR(50)"),
    ('school', "VARCHAR(100)"),
    ('major', "VARCHAR(100)"),
    ('emergency_contact', "VARCHAR(50)"),
    ('emergency_phone', "VARCHAR(20)"),
    ('manager_id', "INTEGER"),
    ('department_id', "INTEGER"),
    ('attachments', "JSON DEFAULT '[]'")
]

for col_name, col_type in user_new_columns:
    if not column_exists('users', col_name):
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"[OK] Added users.{col_name}")
        except Exception as e:
            print(f"[ERR] users.{col_name}: {e}")
    else:
        print(f"[SKIP] users.{col_name} already exists")


# ==================== 2. 创建 departments 表（第二次迭代）====================
if not table_exists('departments'):
    cursor.execute('''
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            code VARCHAR(50) UNIQUE NOT NULL,
            description VARCHAR(200),
            parent_id INTEGER,
            manager_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("[OK] Created departments table")
else:
    print("[SKIP] departments table already exists")


# ==================== 3. 创建 attendances 表（第二次迭代）====================
if not table_exists('attendances'):
    cursor.execute('''
        CREATE TABLE attendances (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            work_date DATE NOT NULL,
            check_in DATETIME,
            check_out DATETIME,
            work_hours NUMERIC(4, 2) DEFAULT 0,
            overtime_hours NUMERIC(4, 2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'normal',
            remark TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX idx_attendances_user_id ON attendances(user_id)')
    print("[OK] Created attendances table")
else:
    print("[SKIP] attendances table already exists")


# ==================== 4. 创建 leave_balances 表（第二次迭代）====================
if not table_exists('leave_balances'):
    cursor.execute('''
        CREATE TABLE leave_balances (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            leave_type VARCHAR(20) NOT NULL,
            total_days NUMERIC(5, 1) DEFAULT 0,
            used_days NUMERIC(5, 1) DEFAULT 0,
            year INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX idx_leave_balances_user_id ON leave_balances(user_id)')
    print("[OK] Created leave_balances table")
else:
    print("[SKIP] leave_balances table already exists")


# ==================== 5. 创建 work_time_records 表（第二次迭代）====================
if not table_exists('work_time_records'):
    cursor.execute('''
        CREATE TABLE work_time_records (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            project_id INTEGER,
            task_id INTEGER,
            work_date DATE NOT NULL,
            hours NUMERIC(4, 2) DEFAULT 0,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX idx_work_time_user_id ON work_time_records(user_id)')
    print("[OK] Created work_time_records table")
else:
    print("[SKIP] work_time_records table already exists")


conn.commit()
conn.close()
print("\n【第二次迭代】数据库迁移完成！")
