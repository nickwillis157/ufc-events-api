"""
UFC.com official website scraper
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from models.ufc_models import UFCEvent, Fight, Fighter, EventStatus, TitleFightType
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class UFCOfficialScraper:
    """Scraper for UFC.com official website"""
    
    BASE_URL = "https://www.ufc.com"
    EVENTS_URL = f"{BASE_URL}/events"
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.ufc.com/events'
        })
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_json(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Fetch JSON data with retry logic"""
        await self.rate_limiter.wait()
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch JSON from {url}: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a web page with retry logic"""
        await self.rate_limiter.wait()
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise
    
    async def discover_events(self, mode: str = "full", since: Optional[str] = None) -> List[Dict]:
        """Discover UFC events from UFC.com"""
        events = []
        
        try:
            # Since the API endpoint is not working, let's scrape the events page directly
            soup = await self._fetch_page(self.EVENTS_URL)
            events = await self._parse_events_page(soup, mode, since)
        except Exception as e:
            logger.error(f"Error discovering events from UFC.com: {e}")
        
        logger.info(f"Discovered {len(events)} events from UFC.com")
        return events
    
    async def _parse_events_page(self, soup, mode: str, since: Optional[str] = None) -> List[Dict]:
        """Parse events from the main events page"""
        events = []
        
        try:
            # Look for event cards or links
            event_selectors = [
                '.c-card-event',
                '.event-card',
                '.c-listing-fight',
                'article.c-card',
                '.view-events .views-row'
            ]
            
            event_elements = []
            for selector in event_selectors:
                elements = soup.select(selector)
                if elements:
                    event_elements = elements
                    logger.info(f"Found {len(elements)} events using selector: {selector}")
                    break
            
            if not event_elements:
                # Try to find any links that might be events
                links = soup.find_all('a', href=True)
                event_links = [link for link in links if '/event/' in link.get('href', '')]
                logger.info(f"Found {len(event_links)} event links as fallback")
                
                for link in event_links[:10]:  # Limit to 10
                    href = link.get('href')
                    if href.startswith('/'):
                        href = self.BASE_URL + href
                    
                    event_id = href.split('/')[-1]
                    event_name = link.get_text(strip=True) or f"UFC Event {event_id}"
                    
                    events.append({
                        'id': event_id,
                        'name': event_name,
                        'date': datetime.now().strftime('%Y-%m-%d'),  # Placeholder
                        'url': href,
                        'source': 'ufc_official'
                    })
            else:
                # Parse event elements
                for element in event_elements[:10]:  # Limit to 10
                    event_data = self._parse_event_element(element)
                    if event_data:
                        events.append(event_data)
        
        except Exception as e:
            logger.error(f"Error parsing events page: {e}")
        
        return events
    
    def _parse_event_element(self, element) -> Optional[Dict]:
        """Parse an individual event element"""
        try:
            # Try to extract event information
            event_link = element.find('a', href=True)
            if not event_link:
                return None
            
            href = event_link.get('href')
            if href.startswith('/'):
                href = self.BASE_URL + href
            
            event_id = href.split('/')[-1]
            event_name = event_link.get_text(strip=True)
            
            # Try to find date
            date_elem = element.find(string=lambda text: text and any(month in text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']))
            event_date = datetime.now().strftime('%Y-%m-%d')  # Default
            
            if date_elem:
                # Try to parse the date
                try:
                    # This is a simplified date parsing - would need more robust parsing
                    date_text = date_elem.strip()
                    # Add more sophisticated date parsing here
                except:
                    pass
            
            return {
                'id': event_id,
                'name': event_name,
                'date': event_date,
                'url': href,
                'source': 'ufc_official'
            }
        
        except Exception as e:
            logger.error(f"Error parsing event element: {e}")
            return None
    
    async def _discover_upcoming_events(self, since: Optional[str] = None) -> List[Dict]:
        """Discover upcoming events"""
        events = []
        
        try:
            # Fetch upcoming events
            params = {
                'limit': 50,
                'offset': 0,
                'status': 'upcoming'
            }
            
            data = await self._fetch_json(self.EVENTS_API, params)
            
            for event_data in data.get('results', []):
                event_info = self._parse_api_event(event_data)
                if event_info:
                    # Filter by date if specified
                    if since:
                        event_date = datetime.strptime(event_info['date'], '%Y-%m-%d')
                        since_date = datetime.strptime(since, '%Y-%m-%d')
                        if event_date < since_date:
                            continue
                    
                    events.append(event_info)
            
        except Exception as e:
            logger.error(f"Error discovering upcoming events: {e}")
        
        return events
    
    async def _discover_past_events(self, since: Optional[str] = None) -> List[Dict]:
        """Discover past events"""
        events = []
        
        try:
            # Fetch past events
            params = {
                'limit': 50,
                'offset': 0,
                'status': 'past'
            }
            
            # Paginate through past events
            while True:
                data = await self._fetch_json(self.EVENTS_API, params)
                results = data.get('results', [])
                
                if not results:
                    break
                
                page_events = []
                for event_data in results:
                    event_info = self._parse_api_event(event_data)
                    if event_info:
                        # Filter by date if specified
                        if since:
                            event_date = datetime.strptime(event_info['date'], '%Y-%m-%d')
                            since_date = datetime.strptime(since, '%Y-%m-%d')
                            if event_date < since_date:
                                continue
                        
                        page_events.append(event_info)
                
                events.extend(page_events)
                
                # Check if we should continue
                if len(results) < params['limit']:
                    break
                
                params['offset'] += params['limit']
                
                # Safety break
                if params['offset'] > 1000:
                    break
        
        except Exception as e:
            logger.error(f"Error discovering past events: {e}")
        
        return events
    
    def _parse_api_event(self, event_data: Dict) -> Optional[Dict]:
        """Parse event data from API response"""
        try:
            event_id = event_data.get('id')
            if not event_id:
                return None
            
            name = event_data.get('name', '')
            
            # Parse date
            date_str = event_data.get('date')
            if date_str:
                try:
                    event_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                except ValueError:
                    event_date = datetime.now().strftime('%Y-%m-%d')
            else:
                event_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract location
            location = event_data.get('location', {})
            venue = None
            city = None
            
            if isinstance(location, dict):
                venue = location.get('venue')
                city = location.get('city')
            
            # Create event URL
            event_url = f"{self.BASE_URL}/event/{event_id}"
            
            return {
                'id': str(event_id),
                'name': name,
                'date': event_date,
                'venue': venue,
                'location': city,
                'url': event_url,
                'source': 'ufc_official'
            }
            
        except Exception as e:
            logger.error(f"Error parsing API event: {e}")
            return None
    
    async def scrape_event(self, event_id: str) -> Optional[UFCEvent]:
        """Scrape detailed event information"""
        event_url = f"{self.BASE_URL}/event/{event_id}"
        
        try:
            soup = await self._fetch_page(event_url)
            return await self._parse_event_details(soup, event_id, event_url)
        except Exception as e:
            logger.error(f"Failed to scrape event {event_id}: {e}")
            return None
    
    async def _parse_event_details(self, soup: BeautifulSoup, event_id: str, event_url: str) -> Optional[UFCEvent]:
        """Parse event details from the event page"""
        try:
            # Extract event information
            event_name = self._extract_event_name(soup)
            event_date = self._extract_event_date(soup)
            venue = self._extract_venue(soup)
            location = self._extract_location(soup)
            status = self._extract_status(soup)
            
            # Extract fights
            fights = await self._extract_fights(soup)
            
            event = UFCEvent(
                event_id=event_id,
                event_name=event_name,
                event_date=event_date,
                venue=venue,
                location=location,
                status=status,
                fights=fights,
                source_urls={'ufc_official': event_url}
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing event details: {e}")
            return None
    
    def _extract_event_name(self, soup: BeautifulSoup) -> str:
        """Extract event name"""
        # Try multiple selectors
        selectors = [
            'h1.hero-profile__name',
            'h1.c-hero__headline',
            '.event-header__title',
            'h1'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.text.strip()
        
        return "Unknown Event"
    
    def _extract_event_date(self, soup: BeautifulSoup) -> str:
        """Extract event date"""
        # Look for date in various formats
        date_selectors = [
            '.hero-profile__info .c-listing-fight__date',
            '.c-hero__info .c-listing-fight__date',
            '.event-header__date',
            '[data-date]'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date_text = elem.text.strip()
                try:
                    # Try various date formats
                    for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(date_text, fmt).strftime('%Y-%m-%d')
                        except ValueError:
                            continue
                except:
                    continue
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_venue(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract venue information"""
        venue_selectors = [
            '.hero-profile__info .c-listing-fight__venue',
            '.c-hero__info .c-listing-fight__venue',
            '.event-header__venue'
        ]
        
        for selector in venue_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.text.strip()
        
        return None
    
    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location information"""
        location_selectors = [
            '.hero-profile__info .c-listing-fight__location',
            '.c-hero__info .c-listing-fight__location',
            '.event-header__location'
        ]
        
        for selector in location_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.text.strip()
        
        return None
    
    def _extract_status(self, soup: BeautifulSoup) -> EventStatus:
        """Extract event status"""
        # Check for indicators of event status
        if soup.find(string=lambda text: text and 'upcoming' in text.lower()):
            return EventStatus.SCHEDULED
        elif soup.find(string=lambda text: text and 'results' in text.lower()):
            return EventStatus.COMPLETED
        else:
            # Default to scheduled for UFC.com
            return EventStatus.SCHEDULED
    
    async def _extract_fights(self, soup: BeautifulSoup) -> List[Fight]:
        """Extract fight information with segment detection"""
        fights = []
        
        # Look for structured fight card sections
        segments = self._extract_fight_segments(soup)
        
        if segments:
            bout_order = 1
            for segment_name, segment_fights in segments.items():
                for fight_elem in segment_fights:
                    fight = await self._parse_fight_element(fight_elem, bout_order)
                    if fight:
                        # Add segment information to fight
                        fight.segment = segment_name
                        fights.append(fight)
                        bout_order += 1
        else:
            # Fallback to generic fight extraction
            fight_selectors = [
                '.l-listing__item',
                '.c-listing-fight',
                '.fight-card__fight'
            ]
            
            fight_elements = []
            for selector in fight_selectors:
                elements = soup.select(selector)
                if elements:
                    fight_elements = elements
                    break
            
            bout_order = 1
            for fight_elem in fight_elements:
                fight = await self._parse_fight_element(fight_elem, bout_order)
                if fight:
                    fights.append(fight)
                    bout_order += 1
        
        # Reverse order so main event is first
        fights.reverse()
        for i, fight in enumerate(fights):
            fight.bout_order = i + 1
        
        return fights
    
    def _extract_fight_segments(self, soup: BeautifulSoup) -> Dict[str, List]:
        """Extract fights organized by broadcast segments"""
        segments = {}
        
        # Look for main card section
        main_card_section = soup.find(id='main-card') or soup.find(class_='main-card')
        if main_card_section:
            main_card_fights = main_card_section.find_all(class_='c-listing-fight') or main_card_section.find_all('.l-listing__item')
            if main_card_fights:
                segments['main-card'] = main_card_fights
        
        # Look for prelims section
        prelims_section = soup.find(id='prelims') or soup.find(class_='prelims')
        if prelims_section:
            prelims_fights = prelims_section.find_all(class_='c-listing-fight') or prelims_section.find_all('.l-listing__item')
            if prelims_fights:
                segments['prelims'] = prelims_fights
        
        # Look for early prelims section
        early_prelims_section = soup.find(id='early-prelims') or soup.find(class_='early-prelims')
        if early_prelims_section:
            early_prelims_fights = early_prelims_section.find_all(class_='c-listing-fight') or early_prelims_section.find_all('.l-listing__item')
            if early_prelims_fights:
                segments['early-prelims'] = early_prelims_fights
        
        # Alternative: look for section headers
        if not segments:
            sections_with_headers = {}
            
            # Find all potential section headers
            headers = soup.find_all(['h2', 'h3', 'h4'], string=lambda text: text and any(keyword in text.lower() for keyword in ['main card', 'prelim']))
            
            for header in headers:
                section_name = header.text.lower().strip()
                if 'main card' in section_name:
                    key = 'main-card'
                elif 'early prelim' in section_name:
                    key = 'early-prelims'
                elif 'prelim' in section_name:
                    key = 'prelims'
                else:
                    continue
                
                # Find fights after this header
                current = header.next_sibling
                section_fights = []
                while current:
                    if hasattr(current, 'find_all'):
                        fights_in_current = current.find_all(class_='c-listing-fight') or current.find_all('.l-listing__item')
                        section_fights.extend(fights_in_current)
                    
                    # Stop if we hit another header
                    if hasattr(current, 'name') and current.name in ['h2', 'h3', 'h4']:
                        break
                    
                    current = current.next_sibling
                
                if section_fights:
                    sections_with_headers[key] = section_fights
            
            segments = sections_with_headers
        
        return segments
    
    async def _parse_fight_element(self, elem, bout_order: int) -> Optional[Fight]:
        """Parse individual fight element"""
        try:
            # Extract fighter names
            fighter_names = []
            
            # Try different selectors for fighter names
            name_selectors = [
                '.c-listing-fight__corner-name',
                '.c-listing-fight__fighter-name',
                '.fight-card__fighter-name'
            ]
            
            for selector in name_selectors:
                names = elem.select(selector)
                if names:
                    fighter_names = [name.text.strip() for name in names]
                    break
            
            if len(fighter_names) < 2:
                return None
            
            # Extract weight class
            weight_class = "Unknown"
            weight_selectors = [
                '.c-listing-fight__class-text',
                '.fight-card__weight-class'
            ]
            
            for selector in weight_selectors:
                weight_elem = elem.select_one(selector)
                if weight_elem:
                    weight_class = weight_elem.text.strip()
                    break
            
            # Check for title fight
            title_fight = TitleFightType.NONE
            if 'title' in weight_class.lower() or 'championship' in weight_class.lower():
                title_fight = TitleFightType.UNDISPUTED
            
            # Create fighter objects
            fighter1 = Fighter(name=fighter_names[0])
            fighter2 = Fighter(name=fighter_names[1])
            
            fight = Fight(
                bout_order=bout_order,
                fighter1=fighter1,
                fighter2=fighter2,
                weight_class=weight_class,
                title_fight=title_fight
            )
            
            return fight
            
        except Exception as e:
            logger.error(f"Error parsing fight element: {e}")
            return None