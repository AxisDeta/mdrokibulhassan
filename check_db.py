from app import create_app
from models import Publication, ProfileInfo

app = create_app()

with app.app_context():
    total_pubs = Publication.query.count()
    profile = ProfileInfo.query.first()
    
    print(f"Total publications in database: {total_pubs}")
    print(f"Profile image: {profile.profile_image if profile else 'None'}")
    
    print("\nRecent publications:")
    pubs = Publication.query.order_by(Publication.year.desc()).limit(5).all()
    for pub in pubs:
        print(f"  - {pub.title[:60]}... ({pub.year}) - {pub.citations} citations")
