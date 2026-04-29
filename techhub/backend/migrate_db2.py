import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN permission_version INT DEFAULT 1"))
        db.session.commit()
        print("[OK] Added users.permission_version")
    except Exception as e:
        if "already exists" in str(e).lower() or "Duplicate" in str(e):
            print("[OK] users.permission_version already exists")
        else:
            print(f"[ERR] {e}")
    print("Migration done!")
