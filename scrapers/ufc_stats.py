"""
UFCStats.com scraper - Official UFC statistics website
"""

import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from models.ufc_models import UFCEvent, Fight, Fighter, EventStatus, TitleFightType
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class UFCStatsScaper:
    """Scraper for UFCStats.com"""
    
    BASE_URL = "http://ufcstats.com"
    EVENTS_URL = f"{BASE_URL}/statistics/events/completed"
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
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
        """Discover UFC events from UFCStats.com"""
        events = []
        
        if mode in ["full", "historical"]:
            events.extend(await self._discover_completed_events(since))
        
        # UFCStats doesn't have future events, so we skip those
        logger.info(f"Discovered {len(events)} events from UFCStats")
        return events
    
    async def _discover_completed_events(self, since: Optional[str] = None) -> List[Dict]:
        """Discover completed events from UFCStats"""
        events = []
        
        try:
            # Start with the main events page
            soup = await self._fetch_page(self.EVENTS_URL)
            
            # Look for different possible selectors for event rows
            event_rows = []
            
            # Try multiple selectors
            selectors = [
                'tr.b-statistics__table-row',
                'tbody tr',
                'table tr',
                '.b-statistics__table tr'
            ]
            
            for selector in selectors:
                rows = soup.select(selector)
                if rows and len(rows) > 1:  # Skip header row
                    event_rows = rows[1:]  # Skip header
                    logger.info(f"Found {len(event_rows)} event rows using selector: {selector}")
                    break
            
            if not event_rows:
                logger.warning("No event rows found. Checking page structure...")
                # Debug: show some page content
                text_content = soup.get_text()[:500]
                logger.info(f"Page content preview: {text_content}")
                return events
            
            for row in event_rows[:20]:  # Limit to first 20 events for testing
                event_data = self._parse_event_row(row)
                if event_data:
                    # Filter by date if specified
                    if since:
                        try:
                            event_date = datetime.strptime(event_data['date'], '%Y-%m-%d')
                            since_date = datetime.strptime(since, '%Y-%m-%d')
                            if event_date < since_date:
                                continue
                        except ValueError:
                            logger.warning(f"Could not parse date: {event_data.get('date')}")
                            continue
                    
                    events.append(event_data)
                    logger.info(f"Found event: {event_data['name']} on {event_data['date']}")
        
        except Exception as e:
            logger.error(f"Error discovering events: {e}")
        
        return events
    
    def _parse_event_row(self, row) -> Optional[Dict]:
        """Parse an event row from the events table"""
        try:
            # Skip header rows
            if 'b-statistics__table-header' in row.get('class', []):
                return None
            
            cols = row.find_all(['td', 'th'])
            if len(cols) < 2:
                return None
            
            # Find event link - could be in first or second column
            event_link = None
            event_name = ""
            
            for col in cols[:3]:  # Check first 3 columns
                link = col.find('a', href=True)
                if link and '/event-details/' in link.get('href', ''):
                    event_link = link
                    event_name = link.text.strip()
                    break
            
            if not event_link:
                return None
            
            event_url = urljoin(self.BASE_URL, event_link.get('href'))
            
            # Extract date - look for date patterns in all columns
            event_date = None
            for col in cols:
                text = col.text.strip()
                if text and any(month in text for month in ['January', 'February', 'March', 'April', 'May', 'June', 
                                                           'July', 'August', 'September', 'October', 'November', 'December',
                                                           'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                    try:
                        # Try different date formats
                        for fmt in ['%B %d, %Y', '%b %d, %Y', '%m/%d/%Y']:
                            try:
                                event_date = datetime.strptime(text, fmt).strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                        if event_date:
                            break
                    except:
                        continue
            
            # If no date found, use a default recent date for testing
            if not event_date:
                event_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract location
            location = ""
            for col in cols:
                text = col.text.strip()
                if text and text != event_name and not any(month in text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                    if len(text) > 3 and ',' in text:  # Likely a location
                        location = text
                        break
            
            # Generate event ID from URL
            event_id = event_url.split('/')[-1] if event_url else f"event-{hash(event_name)}"
            
            return {
                'id': event_id,
                'name': event_name,
                'date': event_date,
                'location': location,
                'url': event_url,
                'source': 'ufcstats'
            }
            
        except Exception as e:
            logger.error(f"Error parsing event row: {e}")
            return None
    
    async def scrape_event(self, event_id: str) -> Optional[UFCEvent]:
        """Scrape detailed event information"""
        event_url = f"{self.BASE_URL}/event-details/{event_id}"
        
        try:
            soup = await self._fetch_page(event_url)
            return await self._parse_event_details(soup, event_id, event_url)
        except Exception as e:
            logger.error(f"Failed to scrape event {event_id}: {e}")
            return None
    
    async def _parse_event_details(self, soup: BeautifulSoup, event_id: str, event_url: str) -> Optional[UFCEvent]:
        """Parse event details from the event page"""
        try:
            # Extract event header information
            event_name = self._extract_event_name(soup)
            event_date = self._extract_event_date(soup)
            venue = self._extract_venue(soup)
            location = self._extract_location(soup)
            
            # Extract fights
            fights = await self._extract_fights(soup)
            
            # Determine event status
            status = EventStatus.COMPLETED  # UFCStats only has completed events
            
            event = UFCEvent(
                event_id=event_id,
                event_name=event_name,
                event_date=event_date,
                venue=venue,
                location=location,
                status=status,
                fights=fights,
                source_urls={'ufcstats': event_url}
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing event details: {e}")
            return None
    
    def _extract_event_name(self, soup: BeautifulSoup) -> str:
        """Extract event name"""
        name_elem = soup.find('span', class_='b-content__title-highlight')
        if name_elem:
            return name_elem.text.strip()
        
        # Fallback to page title
        title_elem = soup.find('h2', class_='b-content__title')
        if title_elem:
            return title_elem.text.strip()
        
        return "Unknown Event"
    
    def _extract_event_date(self, soup: BeautifulSoup) -> str:
        """Extract event date"""
        # Look for date in event details
        details = soup.find_all('li', class_='b-list__box-list-item')
        for detail in details:
            text = detail.text.strip()
            if 'Date:' in text:
                date_text = text.replace('Date:', '').strip()
                try:
                    return datetime.strptime(date_text, '%B %d, %Y').strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        return datetime.strptime(date_text, '%b %d, %Y').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_venue(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract venue information"""
        details = soup.find_all('li', class_='b-list__box-list-item')
        for detail in details:
            text = detail.text.strip()
            if 'Location:' in text:
                return text.replace('Location:', '').strip()
        return None
    
    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location (same as venue for UFCStats)"""
        return self._extract_venue(soup)
    
    async def _extract_fights(self, soup: BeautifulSoup) -> List[Fight]:
        """Extract fight information from event page"""
        fights = []
        
        # Find all fight rows
        fight_rows = soup.find_all('tr', class_='b-fight-details__table-row')
        
        bout_order = 1
        for row in fight_rows:
            if 'b-fight-details__table-header' in row.get('class', []):
                continue
            
            fight = await self._parse_fight_row(row, bout_order)
            if fight:
                fights.append(fight)
                bout_order += 1
        
        # Reverse order so main event is bout_order 1
        fights.reverse()
        for i, fight in enumerate(fights):
            fight.bout_order = i + 1
        
        return fights
    
    async def _parse_fight_row(self, row, bout_order: int) -> Optional[Fight]:
        """Parse individual fight row"""
        try:
            cols = row.find_all('td')
            if len(cols) < 8:
                return None
            
            # Extract fighter names
            fighter_links = cols[1].find_all('a')
            if len(fighter_links) < 2:
                return None
            
            fighter1_name = fighter_links[0].text.strip()
            fighter2_name = fighter_links[1].text.strip()
            
            # Extract result
            result_text = cols[0].text.strip()
            winner = None
            method = None
            round_num = None
            time = None
            
            if result_text and result_text != 'W/L':
                # Parse result (e.g., "W-U-DEC")
                parts = result_text.split('-')
                if len(parts) >= 2:
                    winner = fighter1_name if parts[0] == 'W' else fighter2_name
                    method = parts[-1] if len(parts) > 2 else None
            
            # Extract weight class
            weight_class = cols[6].text.strip()
            
            # Extract method, round, time
            method_text = cols[7].text.strip()
            round_text = cols[8].text.strip() if len(cols) > 8 else None
            time_text = cols[9].text.strip() if len(cols) > 9 else None
            
            if method_text and method_text != '--':
                method = method_text
            
            if round_text and round_text.isdigit():
                round_num = int(round_text)
            
            if time_text and time_text != '--':
                time = time_text
            
            # Check if title fight
            title_fight = TitleFightType.NONE
            if 'title' in weight_class.lower() or 'championship' in weight_class.lower():
                title_fight = TitleFightType.UNDISPUTED
            
            # Create fighter objects
            fighter1 = Fighter(name=fighter1_name)
            fighter2 = Fighter(name=fighter2_name)
            
            fight = Fight(
                bout_order=bout_order,
                fighter1=fighter1,
                fighter2=fighter2,
                weight_class=weight_class,
                title_fight=title_fight,
                method=method,
                round=round_num,
                time=time,
                winner=winner
            )
            
            return fight
            
        except Exception as e:
            logger.error(f"Error parsing fight row: {e}")
            return None