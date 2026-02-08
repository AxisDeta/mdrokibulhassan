"""
Script to automatically update profile metrics from publications
"""
from app import create_app
from models import db, Publication, ProfileInfo

app = create_app()

with app.app_context():
    # Calculate total citations
    total_citations = db.session.query(db.func.sum(Publication.citations)).scalar() or 0
    
    # Get all publications ordered by citations
    pubs = Publication.query.order_by(Publication.citations.desc()).all()
    
    # Calculate h-index
    # h-index is the largest number h such that h publications have at least h citations each
    citations_list = [p.citations for p in pubs]
    h_index = 0
    for i, cites in enumerate(citations_list, 1):
        if cites >= i:
            h_index = i
        else:
            break
    
    # Calculate i10-index (number of publications with at least 10 citations)
    i10_index = sum(1 for c in citations_list if c >= 10)
    
    # Update profile
    profile = ProfileInfo.query.first()
    if profile:
        profile.total_citations = total_citations
        profile.h_index = h_index
        profile.i10_index = i10_index
        db.session.commit()
        
        print("Profile metrics updated successfully!")
        print(f"  Total Citations: {total_citations}")
        print(f"  h-index: {h_index}")
        print(f"  i10-index: {i10_index}")
    else:
        print("No profile found in database")
