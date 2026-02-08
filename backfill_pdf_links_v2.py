"""
Backfill PDF URLs for existing publications using their existing Google Scholar URLs
"""
import requests
from bs4 import BeautifulSoup
import time
from app import create_app
from models import db, Publication

def extract_pdf_url_from_pub_page(pub_url):
    """
    Extract PDF URL from a Google Scholar publication page using cluster ID
    """
    if not pub_url:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(pub_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the "Cited by" link which contains the cluster ID
        cites_link = soup.find('a', string=lambda text: text and 'Cited by' in text)
        if cites_link and 'href' in cites_link.attrs:
            href = cites_link['href']
            if 'cites=' in href:
                cluster_id = href.split('cites=')[1].split('&')[0]
                pdf_url = f"https://scholar.google.com/scholar?oi=bibs&cluster={cluster_id}&btnI=1&hl=en"
                return pdf_url
        
        print(f"  Could not find cluster ID in page")
        return None
        
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None

app = create_app()

with app.app_context():
    # Get all publications with google_scholar_url but without pdf_url
    publications = Publication.query.filter(
        Publication.google_scholar_url != None,
        (Publication.pdf_url == None) | (Publication.pdf_url == '')
    ).all()
    
    print(f"Found {len(publications)} publications with Scholar URLs but no PDF URLs\n")
    
    updated_count = 0
    
    for i, pub in enumerate(publications, 1):
        print(f"[{i}/{len(publications)}] {pub.title[:70]}...")
        
        pdf_url = extract_pdf_url_from_pub_page(pub.google_scholar_url)
        
        if pdf_url:
            pub.pdf_url = pdf_url
            db.session.commit()
            updated_count += 1
            print(f"  + PDF URL added")
        else:
            print(f"  - Could not extract PDF URL")
        
        # Be respectful to Google Scholar
        if i < len(publications):
            time.sleep(2)
        
        print()
    
    print(f"\nBackfill complete!")
    print(f"Updated {updated_count} out of {len(publications)} publications with PDF URLs")
