"""
seed.py — Creates default admin user on first deploy.
Run once after database is set up.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    db.create_all()

    # Admin account
    if not User.query.filter_by(email='admin@devineadventures.co.ke').first():
        admin = User(
            email='admin@devineadventures.co.ke',
            username='devineadmin',
            first_name='Devine',
            last_name='Admin',
            role='admin',
            is_active=True
        )
        admin.set_password('DevineAdmin@2025')
        db.session.add(admin)
        db.session.commit()
        print('Admin created: admin@devineadventures.co.ke / DevineAdmin@2025')
    else:
        print('Admin already exists.')
