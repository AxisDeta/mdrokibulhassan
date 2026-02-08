"""
Quick script to scrape Google Scholar profile and identify research areas
"""
import requests
from bs4 import BeautifulSoup

scholar_url = "https://scholar.google.com/citations?user=jic1XEcAAAAJ&hl=en"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(scholar_url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Get profile name
name_elem = soup.find('div', id='gsc_prf_in')
name = name_elem.text.strip() if name_elem else "Unknown"

# Get research interests
interests_div = soup.find('div', id='gsc_prf_int')
interests = []
if interests_div:
    interest_links = interests_div.find_all('a', class_='gsc_prf_inta')
    interests = [link.text.strip() for link in interest_links]

# Get publication count
pub_count_elem = soup.find('td', class_='gsc_rsb_std')
pub_count = pub_count_elem.text.strip() if pub_count_elem else "0"

print(f"Name: {name}")
print(f"Total Publications: {pub_count}")
print(f"\nResearch Interests/Areas:")
for interest in interests:
    print(f"  - {interest}")

# Get a few publication titles to understand the research focus
print(f"\nSample Publications:")
pub_rows = soup.find_all('tr', class_='gsc_a_tr')[:5]
for row in pub_rows:
    title_elem = row.find('a', class_='gsc_a_at')
    if title_elem:
        print(f"  - {title_elem.text.strip()}")
