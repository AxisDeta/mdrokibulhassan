"""
Re-categorize all publications with improved keyword matching
"""
from app import create_app
from models import db, Publication, ResearchArea

app = create_app()

# Enhanced keyword mapping for each research area
AREA_KEYWORDS = {
    'Supply Chain Management': [
        'supply chain', 'logistics', 'inventory', 'procurement', 'distribution',
        'warehouse', 'supplier', 'demand forecasting', 'supply', 'chain'
    ],
    'Machine Learning': [
        'machine learning', 'deep learning', 'neural network', 'ai', 'artificial intelligence',
        'predictive', 'classification', 'regression', 'model', 'algorithm', 'ml', 'prediction',
        'forecasting model', 'ai-driven', 'ai-based', 'ai-powered'
    ],
    'Big Data Analytics': [
        'big data', 'data analytics', 'data science', 'analytics', 'data mining',
        'data-driven', 'data analysis', 'geospatial', 'intelligence'
    ],
    'Business Analytics': [
        'business analytics', 'business intelligence', 'performance', 'optimization',
        'strategy', 'decision', 'business', 'market', 'customer', 'sales',
        'revenue', 'profit', 'trading', 'financial', 'economic', 'retail', 'cybersecurity'
    ],
    'Project Management': [
        'project management', 'implementation', 'deployment', 'framework',
        'strategic', 'planning', 'management'
    ]
}

def categorize_publication(title, abstract=''):
    """Categorize publication based on title and abstract"""
    text = f"{title} {abstract}".lower()
    matched_areas = []
    
    for area_name, keywords in AREA_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                matched_areas.append(area_name)
                break
    
    return matched_areas

with app.app_context():
    # Get all research areas
    areas_dict = {area.name: area for area in ResearchArea.query.all()}
    
    # Get all publications
    publications = Publication.query.all()
    
    updated_count = 0
    
    for pub in publications:
        # Clear existing areas
        pub.research_areas = []
        
        # Categorize based on title and abstract
        matched_area_names = categorize_publication(pub.title, pub.abstract or '')
        
        # Add matched areas
        for area_name in matched_area_names:
            if area_name in areas_dict:
                pub.research_areas.append(areas_dict[area_name])
        
        if matched_area_names:
            updated_count += 1
            print(f"+ {pub.title[:70]}")
            print(f"  Areas: {matched_area_names}")
        else:
            print(f"- {pub.title[:70]}")
            print(f"  No areas matched")
    
    db.session.commit()
    
    print(f"\n\nRe-categorization complete!")
    print(f"Updated {updated_count} out of {len(publications)} publications")
    
    # Show summary
    print("\n\nSummary by research area:")
    for area_name, area in areas_dict.items():
        count = Publication.query.filter(Publication.research_areas.contains(area)).count()
        print(f"  {area_name}: {count} publications")
