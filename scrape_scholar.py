"""
Google Scholar Profile Scraper
Extracts publication data from Google Scholar profile and populates the database
"""

import requests
from bs4 import BeautifulSoup
import time
from app import create_app
from models import db, Publication, ResearchArea, ProfileInfo
import os

def download_profile_image(url, save_path):
    """Download profile image from Google Scholar"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"[SUCCESS] Profile image downloaded: {save_path}")
            return os.path.basename(save_path)
        else:
            print(f"[ERROR] Failed to download image: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Error downloading image: {e}")
        return None

def extract_pdf_url(pub_link, headers):
    """Extract PDF URL from publication page using cluster ID"""
    if not pub_link:
        return None
    
    try:
        response = requests.get(pub_link, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for the cluster ID in the page
        # It's usually in links like: /scholar?cites=CLUSTER_ID
        cites_link = soup.find('a', string=lambda text: text and 'Cited by' in text)
        if cites_link and 'href' in cites_link.attrs:
            href = cites_link['href']
            if 'cites=' in href:
                cluster_id = href.split('cites=')[1].split('&')[0]
                pdf_url = f"https://scholar.google.com/scholar?oi=bibs&cluster={cluster_id}&btnI=1&hl=en"
                return pdf_url
        
        return None
    except Exception as e:
        print(f"    [WARNING] Could not extract PDF URL: {e}")
        return None

def scrape_google_scholar(scholar_url):
    """Scrape publications from Google Scholar profile"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    publications = []
    
    try:
        print(f"Fetching Google Scholar profile: {scholar_url}")
        response = requests.get(scholar_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch profile: {response.status_code}")
            return publications
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all publication rows
        pub_rows = soup.find_all('tr', class_='gsc_a_tr')
        
        print(f"Found {len(pub_rows)} publications")
        
        for idx, row in enumerate(pub_rows, 1):
            try:
                # Extract title and link
                title_elem = row.find('a', class_='gsc_a_at')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                pub_link = 'https://scholar.google.com' + title_elem['href'] if title_elem.get('href') else None
                
                # Extract authors and venue
                authors_venue = row.find('div', class_='gs_gray')
                authors = authors_venue.text.strip() if authors_venue else ''
                
                # Get venue (second gs_gray div)
                venue_elem = authors_venue.find_next_sibling('div', class_='gs_gray') if authors_venue else None
                venue = venue_elem.text.strip() if venue_elem else ''
                
                # Extract year
                year_elem = row.find('span', class_='gsc_a_h')
                year = int(year_elem.text.strip()) if year_elem and year_elem.text.strip().isdigit() else None
                
                # Extract citations
                citations_elem = row.find('a', class_='gsc_a_ac')
                citations = int(citations_elem.text.strip()) if citations_elem and citations_elem.text.strip().isdigit() else 0
                
                # Extract PDF URL
                pdf_url = extract_pdf_url(pub_link, headers)
                
                if title and year:
                    pub_data = {
                        'title': title,
                        'authors': authors,
                        'venue': venue,
                        'year': year,
                        'citations': citations,
                        'google_scholar_url': pub_link,
                        'pdf_url': pdf_url
                    }
                    publications.append(pub_data)
                    pdf_status = "✓ PDF" if pdf_url else "✗ No PDF"
                    print(f"  [{idx}] {title} ({year}) - {citations} citations {pdf_status}")
                
                # Be nice to Google's servers
                time.sleep(1)  # Increased delay for PDF extraction
                
            except Exception as e:
                print(f"[WARNING] Error parsing publication {idx}: {e}")
                continue
        
        return publications
        
    except Exception as e:
        print(f"[ERROR] Error scraping Google Scholar: {e}")
        return publications

def populate_database(publications_data):
    """Add publications to database"""
    app = create_app()
    
    with app.app_context():
        # Get all research areas for categorization
        research_areas = ResearchArea.query.all()
        
        added_count = 0
        skipped_count = 0
        
        for pub_data in publications_data:
            # Check if publication already exists
            existing = Publication.query.filter_by(title=pub_data['title']).first()
            
            if existing:
                print(f"[SKIP] Publication already exists: {pub_data['title'][:50]}...")
                skipped_count += 1
                continue
            
            # Create new publication
            publication = Publication(
                title=pub_data['title'],
                authors=pub_data['authors'],
                venue=pub_data['venue'],
                year=pub_data['year'],
                citations=pub_data['citations'],
                google_scholar_url=pub_data.get('google_scholar_url'),
                pdf_url=pub_data.get('pdf_url')
            )
            
            # Auto-assign research areas based on keywords
            title_lower = pub_data['title'].lower()
            venue_lower = pub_data['venue'].lower()
            
            for area in research_areas:
                area_name_lower = area.name.lower()
                
                # Simple keyword matching
                if any(keyword in title_lower or keyword in venue_lower for keyword in [
                    'machine learning', 'ml', 'deep learning', 'neural'
                ]) and 'machine learning' in area_name_lower:
                    publication.research_areas.append(area)
                
                elif any(keyword in title_lower or keyword in venue_lower for keyword in [
                    'data', 'analytics', 'analysis', 'statistical'
                ]) and 'data science' in area_name_lower:
                    publication.research_areas.append(area)
                
                elif any(keyword in title_lower or keyword in venue_lower for keyword in [
                    'business', 'management', 'decision', 'enterprise'
                ]) and 'business analytics' in area_name_lower:
                    publication.research_areas.append(area)
                
                elif any(keyword in title_lower or keyword in venue_lower for keyword in [
                    'information', 'technology', 'system', 'software'
                ]) and 'information technology' in area_name_lower:
                    publication.research_areas.append(area)
            
            db.session.add(publication)
            added_count += 1
            print(f"[ADD] {pub_data['title'][:60]}... ({pub_data['year']})")
        
        db.session.commit()
        print(f"\n[SUCCESS] Added {added_count} publications, skipped {skipped_count}")
        return added_count, skipped_count

def update_profile_picture(image_filename):
    """Update profile picture in database"""
    app = create_app()
    
    with app.app_context():
        profile = ProfileInfo.query.first()
        if profile:
            profile.profile_image = image_filename
            db.session.commit()
            print(f"[SUCCESS] Profile picture updated in database")
        else:
            print("[WARNING] No profile found in database")

if __name__ == '__main__':
    print("=" * 60)
    print("Google Scholar Profile Scraper")
    print("=" * 60)
    
    # Download profile picture
    print("\n[1] Downloading profile picture...")
    profile_pic_url = "https://scholar.googleusercontent.com/citations?view_op=medium_photo&user=j3B8Dz8AAAAJ&citpid=5"
    profile_pic_path = "static/uploads/images/profile.jpg"
    image_filename = download_profile_image(profile_pic_url, profile_pic_path)
    
    if image_filename:
        update_profile_picture(image_filename)
    
    # Scrape publications
    print("\n[2] Scraping Google Scholar publications...")
    scholar_url = "https://scholar.google.com/citations?user=jic1XEcAAAAJ&hl=en"
    publications = scrape_google_scholar(scholar_url)
    
    if publications:
        print(f"\n[3] Adding {len(publications)} publications to database...")
        added, skipped = populate_database(publications)
        
        print("\n" + "=" * 60)
        print(f"SUMMARY:")
        print(f"  Total found: {len(publications)}")
        print(f"  Added: {added}")
        print(f"  Skipped: {skipped}")
        print("=" * 60)
    else:
        print("\n[ERROR] No publications found. Please check the Google Scholar URL.")
    
    print("\nDone! You can now view your publications at http://localhost:5000")
