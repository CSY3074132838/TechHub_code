"""
Database migration script
Add DataScope fields and AuditLog table
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Fix roles.data_scope column type (ENUM -> VARCHAR)
    try:
        db.session.execute(text("ALTER TABLE roles DROP COLUMN data_scope"))
        print("[OK] Dropped old roles.data_scope")
    except Exception as e:
        print(f"[INFO] Drop data_scope: {e}")
    
    try:
        db.session.execute(text("ALTER TABLE roles ADD COLUMN data_scope VARCHAR(20) DEFAULT 'self'"))
        print("[OK] Added roles.data_scope as VARCHAR")
    except Exception as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print("[OK] roles.data_scope already exists")
        else:
            print(f"[ERR] roles.data_scope: {e}")
    
    # Add roles.data_scope_custom column (JSON without default)
    try:
        db.session.execute(text("ALTER TABLE roles ADD COLUMN data_scope_custom JSON"))
        print("[OK] Added roles.data_scope_custom")
    except Exception as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            print("[OK] roles.data_scope_custom already exists")
        else:
            print(f"[ERR] roles.data_scope_custom: {e}")
    
    # Create audit_logs table (JSON without default)
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(80) NOT NULL,
                action VARCHAR(50) NOT NULL,
                resource_type VARCHAR(50),
                resource_id INT,
                detail JSON,
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                status VARCHAR(20) DEFAULT 'success',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_action (action),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        print("[OK] Created audit_logs table")
    except Exception as e:
        if 'already exists' in str(e).lower():
            print("[OK] audit_logs already exists")
        else:
            print(f"[ERR] audit_logs: {e}")
    
    db.session.commit()
    print("\nDatabase migration completed!")
