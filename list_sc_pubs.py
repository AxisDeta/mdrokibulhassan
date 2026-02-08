"""
List all supply chain related publications
"""
from app import create_app
from models import db, Publication, ResearchArea

app = create_app()

with app.app_context():
    sc_area = ResearchArea.query.filter_by(name='Supply Chain Management').first()
    
    if sc_area:
        pubs = Publication.query.filter(Publication.research_areas.contains(sc_area)).all()
        
        print(f"Supply Chain Publications: {len(pubs)}\n")
        print("=" * 80)
        
        for i, p in enumerate(pubs, 1):
            print(f"\n{i}. {p.title}")
            print(f"   Year: {p.year} | Citations: {p.citations}")
            print(f"   Authors: {p.authors[:100]}...")
            if p.abstract:
                print(f"   Abstract: {p.abstract[:200]}...")
            print("-" * 80)
    else:
        print("Supply Chain Management research area not found")
