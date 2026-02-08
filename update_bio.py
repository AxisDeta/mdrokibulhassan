"""
Update profile biography to remove 'Researcher' term
"""
from app import create_app
from models import db, ProfileInfo

app = create_app()

with app.app_context():
    profile = ProfileInfo.query.first()
    
    if profile:
        # Update bio to remove 'Researcher' and use appropriate professional title
        new_bio = """<p>Professional specializing in Supply Chain Management, Machine Learning, Big Data Analytics, and Business Analytics with extensive experience in applying advanced analytical techniques to solve complex business challenges.</p>

<p>With a strong foundation in both theoretical knowledge and practical implementation, the focus is on leveraging data-driven insights to optimize supply chain operations, develop predictive models, and drive strategic business decisions.</p>"""
        
        profile.bio = new_bio
        db.session.commit()
        
        print("Profile biography updated successfully!")
        print(f"New bio: {new_bio[:100]}...")
    else:
        print("No profile found in database")
