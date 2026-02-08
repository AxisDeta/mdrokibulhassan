"""
Check publication research area assignments
"""
from app import create_app
from models import Publication, ResearchArea

app = create_app()

with app.app_context():
    # Get Machine Learning area
    ml_area = ResearchArea.query.filter_by(name='Machine Learning').first()
    
    if ml_area:
        print(f"Machine Learning area ID: {ml_area.id}")
        
        # Count publications with this area
        ml_pubs = Publication.query.filter(Publication.research_areas.contains(ml_area)).all()
        print(f"Publications tagged with Machine Learning: {len(ml_pubs)}")
        
        print("\nMachine Learning publications:")
        for p in ml_pubs:
            print(f"  - {p.title[:80]}")
    else:
        print("Machine Learning area not found!")
    
    # Show all publications and their areas
    print("\n\nAll publications and their research areas:")
    all_pubs = Publication.query.all()
    for p in all_pubs:
        areas = [a.name for a in p.research_areas]
        print(f"\n{p.title[:80]}")
        print(f"  Areas: {areas if areas else 'NONE'}")
