from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    # Clear existing users
    User.query.delete()
    db.session.commit()

    users = [
        ('admin', 'admin123', 'admin', 'Administrator'),
        ('supervisor', 'test123', 'supervisor', 'Supervisor One'),
        ('worker', 'test123', 'worker', 'Worker One'),
        ('qc', 'test123', 'qc', 'QC Inspector One'),
    ]

    for username, password, role, full_name in users:
        u = User(username=username, role=role, full_name=full_name)
        u.set_password(password)
        db.session.add(u)

    db.session.commit()
    print("✅ Users and stages seeded!")
    print("admin/admin123 | worker/test123")