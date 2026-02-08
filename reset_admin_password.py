"""
Update admin password to match .env file
"""
from app import create_app
from models import db, User
import os

app = create_app()

with app.app_context():
    admin = User.query.first()
    
    if admin:
        # Get password from environment
        new_password = os.environ.get('ADMIN_PASSWORD', 'admin456')
        admin.set_password(new_password)
        db.session.commit()
        
        print(f"Admin password updated successfully!")
        print(f"  Username: {admin.username}")
        print(f"  Password: {new_password}")
    else:
        print("No admin user found in database")
