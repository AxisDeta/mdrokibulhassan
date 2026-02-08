"""
Backfill PDF URLs for existing publications by scraping Google Scholar
"""
import requests
from bs4 import BeautifulSoup
import time
from app import create_app
from models import db, Publication

def extract_pdf_url_from_scholar(title):
    """
    Search Google Scholar for a publication and extract its PDF URL
    """
    try:
        # Search Google Scholar for the publication
        search_url = f"https://scholar.google.com/scholar?q={requests.utils.quote(title)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the first result
        first_result = soup.find('div', class_='gs_r gs_or gs_scl')
        if not first_result:
            print(f"  No results found on Scholar")
            return None
        
        # Try to find the cluster ID from the citation link
        cite_link = first_result.find('a', string='Cite')
        if cite_link and 'href' in cite_link.attrs:
            cite_href = cite_link['href']
            # Extract cluster ID from cite link
            # Format: /scholar?q=info:CLUSTER_ID:scholar.google.com/&output=cite
            if 'info:' in cite_href:
                cluster_id = cite_href.split('info:')[1].split(':')[0]
                pdf_url = f"https://scholar.google.com/scholar?oi=bibs&cluster={cluster_id}&btnI=1&hl=en"
                return pdf_url
        
        # Alternative: look for cluster in the main link
        main_link = first_result.find('h3', class_='gs_rt')
        if main_link:
            link_tag = main_link.find('a')
            if link_tag and 'data-clk' in link_tag.attrs:
                # Sometimes cluster ID is in data-clk attribute
                pass
        
        print(f"  Could not extract cluster ID")
        return None
        
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None

app = create_app()

with app.app_context():
    # Get all publications without pdf_url
    publications = Publication.query.filter(
        (Publication.pdf_url == None) | (Publication.pdf_url == '')
    ).all()
    
    print(f"Found {len(publications)} publications without PDF URLs\n")
    
    updated_count = 0
    
    for i, pub in enumerate(publications, 1):
        print(f"[{i}/{len(publications)}] Processing: {pub.title[:70]}...")
        
        pdf_url = extract_pdf_url_from_scholar(pub.title)
        
        if pdf_url:
            pub.pdf_url = pdf_url
            db.session.commit()
            updated_count += 1
            print(f"  + PDF URL: {pdf_url}")
        else:
            print(f"  - No PDF URL found")
        
        # Be respectful to Google Scholar - add delay
        if i < len(publications):
            time.sleep(3)  # 3 second delay between requests
        
        print()
    
    print(f"\n\nBackfill complete!")
    print(f"Updated {updated_count} out of {len(publications)} publications with PDF URLs")
