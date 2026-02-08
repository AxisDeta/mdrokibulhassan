"""
Initialize database with correct profile and research areas for MD ROKIBUL HASAN
"""
from app import create_app
from models import db, User, ProfileInfo, ResearchArea, Publication
from werkzeug.security import generate_password_hash
import os

app = create_app()

with app.app_context():
    # Drop all tables and recreate
    print("Dropping existing tables...")
    db.drop_all()
    
    print("Creating tables...")
    db.create_all()
    
    # Create admin user
    print("\nCreating admin user...")
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    admin = User(username=admin_username)
    admin.set_password(admin_password)
    db.session.add(admin)
    
    # Create profile for MD ROKIBUL HASAN
    print("Creating profile...")
    profile = ProfileInfo(
        full_name="MD ROKIBUL HASAN",
        title="Researcher",
        affiliation="",
        email="contact@example.com",
        bio="Researcher specializing in Supply Chain Management, Machine Learning, Big Data Analytics, and Business Analytics.",
        google_scholar_url="https://scholar.google.com/citations?user=jic1XEcAAAAJ&hl=en",
        total_citations=0,
        h_index=0,
        i10_index=0
    )
    db.session.add(profile)
    
    # Create research areas based on Google Scholar interests
    print("Creating research areas...")
    research_areas_data = [
        {
            'name': 'Supply Chain Management',
            'description': 'Research in supply chain optimization, logistics, and operations management',
            'icon': 'fa-truck'
        },
        {
            'name': 'Machine Learning',
            'description': 'Application of machine learning algorithms and AI techniques',
            'icon': 'fa-brain'
        },
        {
            'name': 'Big Data Analytics',
            'description': 'Big data processing, analysis, and insights generation',
            'icon': 'fa-database'
        },
        {
            'name': 'Business Analytics',
            'description': 'Data-driven business decision making and performance optimization',
            'icon': 'fa-chart-line'
        },
        {
            'name': 'Project Management',
            'description': 'Project planning, execution, and management methodologies',
            'icon': 'fa-tasks'
        }
    ]
    
    for area_data in research_areas_data:
        area = ResearchArea(**area_data)
        db.session.add(area)
        print(f"  - {area_data['name']}")
    
    db.session.commit()
    
    print("\n" + "="*60)
    print("Database initialized successfully!")
    print("="*60)
    print(f"\nAdmin Login Credentials:")
    print(f"  Username: {admin_username}")
    print(f"  Password: {admin_password}")
    print(f"\nProfile: {profile.full_name}")
    print(f"Research Areas: {len(research_areas_data)}")
    print("\nNext step: Run scrape_scholar.py to import publications")
