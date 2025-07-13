"""
ESPN MMA API scraper
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from models.ufc_models import UFCEvent, Fight, Fighter, EventStatus, TitleFightType
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class ESPNMMAScraper:
    """Scraper for ESPN MMA API"""
    
    BASE_URL = "https://site.web.api.espn.com/apis/v2/sports/mma/ufc"
    EVENTS_URL = f"{BASE_URL}/events"
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
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
    
    async def discover_events(self, mode: str = "full", since: Optional[str] = None) -> List[Dict]:
        """Discover UFC events from ESPN MMA API"""
        events = []
        
        try:
            # Fetch events
            params = {'limit': 100}
            data = await self._fetch_json(self.EVENTS_URL, params)
            
            for event_data in data.get('events', []):
                event_info = self._parse_api_event(event_data)
                if event_info:
                    # Filter by date if specified
                    if since:
                        event_date = datetime.strptime(event_info['date'], '%Y-%m-%d')
                        since_date = datetime.strptime(since, '%Y-%m-%d')
                        if event_date < since_date:
                            continue
                    
                    # Filter by mode
                    event_datetime = datetime.strptime(event_info['date'], '%Y-%m-%d')
                    now = datetime.now()
                    
                    if mode == "future" and event_datetime <= now:
                        continue
                    elif mode == "historical" and event_datetime > now:
                        continue
                    
                    events.append(event_info)
            
        except Exception as e:
            logger.error(f"Error discovering events from ESPN: {e}")
        
        logger.info(f"Discovered {len(events)} events from ESPN MMA")
        return events
    
    def _parse_api_event(self, event_data: Dict) -> Optional[Dict]:
        """Parse event data from ESPN API response"""
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
            location = None
            venue = None
            
            competitions = event_data.get('competitions', [])
            if competitions:
                venue_data = competitions[0].get('venue', {})
                if venue_data:
                    venue = venue_data.get('fullName')
                    address = venue_data.get('address', {})
                    if address:
                        city = address.get('city')
                        state = address.get('state')
                        country = address.get('country')
                        location_parts = [city, state, country]
                        location = ', '.join(filter(None, location_parts))
            
            return {
                'id': str(event_id),
                'name': name,
                'date': event_date,
                'venue': venue,
                'location': location,
                'url': f"https://www.espn.com/mma/event/_/id/{event_id}",
                'source': 'espn_mma'
            }
            
        except Exception as e:
            logger.error(f"Error parsing ESPN API event: {e}")
            return None
    
    async def scrape_event(self, event_id: str) -> Optional[UFCEvent]:
        """Scrape detailed event information"""
        event_url = f"{self.EVENTS_URL}/{event_id}"
        
        try:
            data = await self._fetch_json(event_url)
            return await self._parse_event_details(data, event_id)
        except Exception as e:
            logger.error(f"Failed to scrape event {event_id}: {e}")
            return None
    
    async def _parse_event_details(self, data: Dict, event_id: str) -> Optional[UFCEvent]:
        """Parse event details from ESPN API response"""
        try:
            event_data = data.get('event', {})
            
            # Extract basic information
            event_name = event_data.get('name', 'Unknown Event')
            
            # Parse date
            date_str = event_data.get('date')
            if date_str:
                try:
                    event_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                except ValueError:
                    event_date = datetime.now().strftime('%Y-%m-%d')
            else:
                event_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract venue and location
            venue = None
            location = None
            
            competitions = event_data.get('competitions', [])
            if competitions:
                venue_data = competitions[0].get('venue', {})
                if venue_data:
                    venue = venue_data.get('fullName')
                    address = venue_data.get('address', {})
                    if address:
                        city = address.get('city')
                        state = address.get('state')
                        country = address.get('country')
                        location_parts = [city, state, country]
                        location = ', '.join(filter(None, location_parts))
            
            # Determine status
            status = EventStatus.SCHEDULED
            event_datetime = datetime.strptime(event_date, '%Y-%m-%d')
            if event_datetime < datetime.now():
                status = EventStatus.COMPLETED
            
            # Extract fights
            fights = await self._extract_fights(competitions)
            
            event = UFCEvent(
                event_id=event_id,
                event_name=event_name,
                event_date=event_date,
                venue=venue,
                location=location,
                status=status,
                fights=fights,
                source_urls={'espn_mma': f"https://www.espn.com/mma/event/_/id/{event_id}"}
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing ESPN event details: {e}")
            return None
    
    async def _extract_fights(self, competitions: List[Dict]) -> List[Fight]:
        """Extract fight information from competitions"""
        fights = []
        
        for competition in competitions:
            competitors = competition.get('competitors', [])
            if len(competitors) < 2:
                continue
            
            # Extract fighter information
            fighter1_data = competitors[0].get('athlete', {})
            fighter2_data = competitors[1].get('athlete', {})
            
            fighter1_name = fighter1_data.get('displayName', 'Unknown')
            fighter2_name = fighter2_data.get('displayName', 'Unknown')
            
            # Extract weight class
            weight_class = competition.get('weightClass', {}).get('displayName', 'Unknown')
            
            # Check for title fight
            title_fight = TitleFightType.NONE
            if competition.get('titleBout', False):
                title_fight = TitleFightType.UNDISPUTED
            
            # Extract fight result if available
            winner = None
            method = None
            
            if competition.get('status', {}).get('type', {}).get('completed', False):
                winner_data = competition.get('winner')
                if winner_data:
                    winner_id = winner_data.get('id')
                    if winner_id == competitors[0].get('id'):
                        winner = fighter1_name
                    elif winner_id == competitors[1].get('id'):
                        winner = fighter2_name
                
                # Extract method if available
                fight_result = competition.get('result', {})
                method = fight_result.get('description')
            
            # Create fighter objects with additional details
            fighter1 = Fighter(
                name=fighter1_name,
                record=fighter1_data.get('record', {}).get('displayValue'),
                country=fighter1_data.get('flag', {}).get('alt')
            )
            
            fighter2 = Fighter(
                name=fighter2_name,
                record=fighter2_data.get('record', {}).get('displayValue'),
                country=fighter2_data.get('flag', {}).get('alt')
            )
            
            fight = Fight(
                bout_order=len(fights) + 1,  # Will be reordered later
                fighter1=fighter1,
                fighter2=fighter2,
                weight_class=weight_class,
                title_fight=title_fight,
                method=method,
                winner=winner
            )
            
            fights.append(fight)
        
        # Reverse order so main event is first
        fights.reverse()
        for i, fight in enumerate(fights):
            fight.bout_order = i + 1
        
        return fights