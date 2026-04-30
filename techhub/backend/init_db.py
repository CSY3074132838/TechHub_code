from app import create_app, db
from app.models import Role

app = create_app()
with app.app_context():
    db.create_all()
    Role.init_roles()
    print('Database initialized successfully')
