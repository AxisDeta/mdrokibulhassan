"""
Google Scholar scraper utilities
Reusable functions for scraping publications from Google Scholar
"""

import requests
from bs4 import BeautifulSoup
import time

def scrape_google_scholar(scholar_url):
    """
    Scrape publications from Google Scholar profile
    
    Args:
        scholar_url: Full Google Scholar profile URL
        
    Returns:
        List of publication dictionaries with keys: title, authors, venue, year, citations, google_scholar_url
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    publications = []
    
    try:
        response = requests.get(scholar_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {'error': f'Failed to fetch profile: HTTP {response.status_code}'}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all publication rows
        pub_rows = soup.find_all('tr', class_='gsc_a_tr')
        
        for row in pub_rows:
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
                
                if title and year:
                    pub_data = {
                        'title': title,
                        'authors': authors,
                        'venue': venue,
                        'year': year,
                        'citations': citations,
                        'google_scholar_url': pub_link
                    }
                    publications.append(pub_data)
                
                # Be nice to Google's servers
                time.sleep(0.3)
                
            except Exception as e:
                print(f"Warning: Error parsing publication: {e}")
                continue
        
        return publications
        
    except requests.RequestException as e:
        return {'error': f'Network error: {str(e)}'}
    except Exception as e:
        return {'error': f'Scraping error: {str(e)}'}

def categorize_publication(pub_data, research_areas):
    """
    Auto-assign research areas to a publication based on keywords
    
    Args:
        pub_data: Publication dictionary with 'title' and 'venue'
        research_areas: List of ResearchArea objects
        
    Returns:
        List of ResearchArea objects that match
    """
    matched_areas = []
    title_lower = pub_data['title'].lower()
    venue_lower = pub_data['venue'].lower()
    combined_text = title_lower + ' ' + venue_lower
    
    for area in research_areas:
        area_name_lower = area.name.lower()
        
        # Keyword matching for different research areas
        if 'supply chain' in area_name_lower:
            if any(keyword in combined_text for keyword in [
                'supply chain', 'logistics', 'inventory', 'procurement', 
                'supplier', 'distribution', 'warehouse', 'operations'
            ]):
                matched_areas.append(area)
        
        elif 'machine learning' in area_name_lower:
            if any(keyword in combined_text for keyword in [
                'machine learning', 'ml', 'deep learning', 'neural', 
                'ai', 'artificial intelligence', 'predictive', 'algorithm'
            ]):
                matched_areas.append(area)
        
        elif 'big data' in area_name_lower:
            if any(keyword in combined_text for keyword in [
                'big data', 'data analytics', 'data mining', 'hadoop',
                'spark', 'data processing', 'data science'
            ]):
                matched_areas.append(area)
        
        elif 'business analytics' in area_name_lower:
            if any(keyword in combined_text for keyword in [
                'business', 'analytics', 'decision', 'performance',
                'optimization', 'strategy', 'management', 'enterprise'
            ]):
                matched_areas.append(area)
        
        elif 'project management' in area_name_lower:
            if any(keyword in combined_text for keyword in [
                'project', 'management', 'planning', 'execution',
                'agile', 'scrum', 'methodology'
            ]):
                matched_areas.append(area)
    
    # If no match found, assign to most general area (Business Analytics)
    if not matched_areas:
        for area in research_areas:
            if 'business analytics' in area.name.lower():
                matched_areas.append(area)
                break
    
    return matched_areas
