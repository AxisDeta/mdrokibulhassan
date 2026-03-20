"""Google Scholar sync utilities."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20
SYNC_CACHE_PATH = Path('data/scholar_sync_cache.json')
DEFAULT_SYNC_INTERVAL_SECONDS = 6 * 60 * 60
SCHOLAR_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/123.0.0.0 Safari/537.36'
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_int(value: str | None, default: int = 0) -> int:
    if not value:
        return default
    digits = re.sub(r'[^0-9]', '', value)
    return int(digits) if digits else default


def _clean_text(value: str | None) -> str:
    return ' '.join((value or '').split())


class ScholarSyncError(Exception):
    """Raised when Google Scholar sync cannot complete."""


def get_scholar_user_id(scholar_url: str | None) -> str | None:
    """Extract the Scholar profile user id from a profile URL."""
    if not scholar_url:
        return None

    parsed = urlparse(scholar_url)
    user_id = parse_qs(parsed.query).get('user', [None])[0]
    return user_id or None


def build_scholar_photo_url(user_id: str | None) -> str | None:
    """Return the direct Google Scholar profile photo URL for a user id."""
    if not user_id:
        return None
    return f'https://scholar.googleusercontent.com/citations?view_op=medium_photo&user={user_id}'


def get_scholar_sync_status() -> dict[str, Any]:
    """Read the persisted sync cache state."""
    if not SYNC_CACHE_PATH.exists():
        return {}

    try:
        return json.loads(SYNC_CACHE_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}


def update_scholar_sync_status(**values: Any) -> dict[str, Any]:
    """Persist sync cache state."""
    status = get_scholar_sync_status()
    status.update(values)
    status['updated_at'] = _utcnow().isoformat()

    SYNC_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYNC_CACHE_PATH.write_text(json.dumps(status, indent=2), encoding='utf-8')
    return status


def is_sync_stale(interval_seconds: int | None = None) -> bool:
    """Return True when the last successful sync is older than the cache TTL."""
    status = get_scholar_sync_status()
    last_success_at = status.get('last_success_at')
    if not last_success_at:
        return True

    try:
        last_success = datetime.fromisoformat(last_success_at)
    except ValueError:
        return True

    ttl = interval_seconds or int(
        os.environ.get('SCHOLAR_SYNC_INTERVAL_SECONDS', DEFAULT_SYNC_INTERVAL_SECONDS)
    )
    return _utcnow() - last_success >= timedelta(seconds=ttl)


def make_scholar_session() -> requests.Session:
    """Create a requests session configured for Scholar scraping."""
    session = requests.Session()
    session.headers.update(
        {
            'User-Agent': SCHOLAR_USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9',
        }
    )
    return session


def fetch_scholar_page(session: requests.Session, scholar_url: str, start: int = 0, page_size: int = 100) -> BeautifulSoup:
    """Fetch and parse a Scholar profile page."""
    response = session.get(
        scholar_url,
        params={'cstart': start, 'pagesize': page_size},
        timeout=DEFAULT_TIMEOUT,
    )

    if response.status_code != 200:
        raise ScholarSyncError(f'Google Scholar returned HTTP {response.status_code}.')

    soup = BeautifulSoup(response.text, 'html.parser')
    page_text = soup.get_text(' ', strip=True).lower()
    if 'not a robot' in page_text or 'enable javascript' in page_text:
        raise ScholarSyncError('Google Scholar blocked the request with an anti-bot challenge.')

    return soup


def parse_profile_metrics(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract profile metadata and metrics from a Scholar profile page."""
    metrics = {
        'name': _clean_text(soup.select_one('#gsc_prf_in').get_text()) if soup.select_one('#gsc_prf_in') else '',
        'affiliation': _clean_text(soup.select_one('.gsc_prf_il').get_text()) if soup.select_one('.gsc_prf_il') else '',
        'citations': 0,
        'h_index': 0,
        'i10_index': 0,
        'image_url': None,
    }

    metric_rows = soup.select('#gsc_rsb_st tbody tr')
    if len(metric_rows) >= 3:
        metrics['citations'] = _safe_int(metric_rows[0].select_one('.gsc_rsb_std').get_text() if metric_rows[0].select_one('.gsc_rsb_std') else None)
        metrics['h_index'] = _safe_int(metric_rows[1].select_one('.gsc_rsb_std').get_text() if metric_rows[1].select_one('.gsc_rsb_std') else None)
        metrics['i10_index'] = _safe_int(metric_rows[2].select_one('.gsc_rsb_std').get_text() if metric_rows[2].select_one('.gsc_rsb_std') else None)

    image_elem = soup.select_one('#gsc_prf_pup-img')
    if image_elem and image_elem.get('src'):
        metrics['image_url'] = image_elem['src']

    return metrics


def parse_publications_from_page(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Extract publication rows from a Scholar profile page."""
    publications: list[dict[str, Any]] = []

    for row in soup.select('tr.gsc_a_tr'):
        title_elem = row.select_one('a.gsc_a_at')
        if not title_elem:
            continue

        author_venue_elems = row.select('td.gsc_a_t .gs_gray')
        authors = _clean_text(author_venue_elems[0].get_text()) if len(author_venue_elems) > 0 else ''
        venue = _clean_text(author_venue_elems[1].get_text()) if len(author_venue_elems) > 1 else ''

        year_text = row.select_one('.gsc_a_y')
        citations_elem = row.select_one('.gsc_a_c a, .gsc_a_ac')
        href = title_elem.get('href', '')
        pub_url = f'https://scholar.google.com{href}' if href.startswith('/') else href or None

        publication = {
            'title': _clean_text(title_elem.get_text()),
            'authors': authors,
            'venue': venue,
            'year': _safe_int(year_text.get_text() if year_text else None, default=0) or None,
            'citations': _safe_int(citations_elem.get_text() if citations_elem else None, default=0),
            'google_scholar_url': pub_url,
        }

        if publication['title']:
            publications.append(publication)

    return publications


def scrape_google_scholar(scholar_url: str) -> list[dict[str, Any]] | dict[str, str]:
    """Backward-compatible publication scraper used by the admin import page."""
    try:
        session = make_scholar_session()
        all_publications: list[dict[str, Any]] = []
        start = 0

        while True:
            soup = fetch_scholar_page(session, scholar_url, start=start)
            page_publications = parse_publications_from_page(soup)
            if not page_publications:
                break

            all_publications.extend(page_publications)

            if len(page_publications) < 100:
                break
            start += 100

        return all_publications
    except (requests.RequestException, ScholarSyncError) as exc:
        return {'error': str(exc)}


def download_profile_image(session: requests.Session, image_url: str, save_path: str) -> str | None:
    """Download a Scholar profile image if Google allows access."""
    try:
        response = session.get(image_url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return None

    content_type = response.headers.get('Content-Type', '')
    if not content_type.startswith('image/'):
        return None

    save_target = Path(save_path)
    save_target.parent.mkdir(parents=True, exist_ok=True)
    save_target.write_bytes(response.content)
    return save_target.name


def categorize_publication(pub_data, research_areas):
    """Auto-assign research areas to a publication based on keywords."""
    matched_areas = []
    title_lower = pub_data['title'].lower()
    venue_lower = pub_data['venue'].lower()
    combined_text = title_lower + ' ' + venue_lower

    for area in research_areas:
        area_name_lower = area.name.lower()

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

    if not matched_areas:
        for area in research_areas:
            if 'business analytics' in area.name.lower():
                matched_areas.append(area)
                break

    return matched_areas


def sync_profile_and_publications(profile, db, Publication, ResearchArea, force: bool = False) -> dict[str, Any]:
    """Sync the configured Scholar profile into the local database."""
    scholar_url = (profile.google_scholar_url or '').strip()
    if not scholar_url:
        raise ScholarSyncError('No Google Scholar URL is configured on the profile.')

    if not force and not is_sync_stale():
        status = get_scholar_sync_status()
        return {
            'status': 'cached',
            'message': 'Cached Scholar data is still fresh.',
            'stats': status.get('stats', {}),
            'profile_image': profile.profile_image,
        }

    session = make_scholar_session()
    soup = fetch_scholar_page(session, scholar_url, start=0)
    metrics = parse_profile_metrics(soup)

    publications: list[dict[str, Any]] = []
    start = 0
    while True:
        page_soup = soup if start == 0 else fetch_scholar_page(session, scholar_url, start=start)
        page_publications = parse_publications_from_page(page_soup)
        if not page_publications:
            break

        publications.extend(page_publications)
        if len(page_publications) < 100:
            break
        start += 100

    if not publications:
        raise ScholarSyncError('No publications were found on the Google Scholar profile.')

    research_areas = ResearchArea.query.all()
    added_count = 0
    updated_count = 0
    skipped_count = 0

    existing_by_title = {
        publication.title.strip().lower(): publication
        for publication in Publication.query.all()
    }

    for pub_data in publications:
        title_key = pub_data['title'].strip().lower()
        existing = existing_by_title.get(title_key)

        if existing:
            changed = False
            for field in ('authors', 'venue', 'year', 'citations', 'google_scholar_url'):
                new_value = pub_data.get(field)
                if new_value is not None and getattr(existing, field) != new_value:
                    setattr(existing, field, new_value)
                    changed = True

            if changed:
                updated_count += 1
            else:
                skipped_count += 1
            continue

        publication = Publication(
            title=pub_data['title'],
            authors=pub_data['authors'],
            venue=pub_data['venue'],
            year=pub_data['year'] or 0,
            citations=pub_data['citations'],
            google_scholar_url=pub_data.get('google_scholar_url'),
        )
        publication.research_areas.extend(categorize_publication(pub_data, research_areas))
        db.session.add(publication)
        existing_by_title[title_key] = publication
        added_count += 1

    if metrics.get('name'):
        profile.full_name = metrics['name']
    if metrics.get('affiliation') and not profile.affiliation:
        profile.affiliation = metrics['affiliation']

    profile.total_citations = metrics['citations'] or sum(pub['citations'] for pub in publications)
    profile.h_index = metrics['h_index']
    profile.i10_index = metrics['i10_index']

    user_id = get_scholar_user_id(scholar_url)
    fallback_image_url = build_scholar_photo_url(user_id)
    image_url = metrics.get('image_url') or fallback_image_url
    downloaded_filename = None
    if image_url:
        downloaded_filename = download_profile_image(
            session,
            image_url,
            'static/uploads/images/google-scholar-profile.jpg',
        )

    profile.profile_image = downloaded_filename or image_url or profile.profile_image

    db.session.commit()

    stats = {
        'publications_found': len(publications),
        'publications_added': added_count,
        'publications_updated': updated_count,
        'publications_unchanged': skipped_count,
        'total_citations': profile.total_citations,
        'h_index': profile.h_index,
        'i10_index': profile.i10_index,
    }
    update_scholar_sync_status(
        last_attempt_at=_utcnow().isoformat(),
        last_success_at=_utcnow().isoformat(),
        last_status='success',
        last_error=None,
        stats=stats,
    )

    return {
        'status': 'success',
        'message': 'Google Scholar data synced successfully.',
        'stats': stats,
        'profile_image': profile.profile_image,
    }


def attempt_cached_profile_image_refresh(profile) -> None:
    """Ensure the profile points to the expected Scholar image URL even before the first full sync."""
    if profile.profile_image:
        return

    image_url = build_scholar_photo_url(get_scholar_user_id(profile.google_scholar_url))
    if image_url:
        profile.profile_image = image_url
