"""
Wikipedia UFC scraper - Much more reliable and structured data
"""

import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from models.ufc_models import UFCEvent, Fight, Fighter, FighterRecord, EventStatus, TitleFightType
from utils.rate_limiter import RateLimiter
from scrapers.fighter_database import build_fighter_database
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class WikipediaUFCScraper:
    """Scraper for Wikipedia UFC data - much more reliable"""
    
    BASE_URL = "https://en.wikipedia.org"
    EVENTS_LIST_URL = f"{BASE_URL}/wiki/List_of_UFC_events"
    
    # Hardcoded dates for events with problematic Wikipedia pages
    HARDCODED_DATES = {
        'UFC_on_FX:_Belfort_vs._Bisping': '2013-01-19',
        'UFC_on_Fox:_Evans_vs._Davis': '2012-01-28',
        'UFC_on_Fox:_Henderson_vs._Melendez': '2013-04-20',
        'UFC_on_Fuel_TV:_Sanchez_vs._Ellenberger': '2012-02-15'
    }
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UFC-Scraper/1.0 (Educational/Research Purpose)'
        })
        # Initialize fighter database
        self.fighter_database = None
        self._database_loaded = False
    
    async def _load_fighter_database(self):
        """Load fighter database from file or build it"""
        if self._database_loaded:
            return
        
        database_file = Path('data/fighter_database.json')
        
        try:
            # Try to load existing database
            if database_file.exists():
                with open(database_file, 'r') as f:
                    fighters_data = json.load(f)
                
                # Convert to Fighter objects
                self.fighter_database = {}
                for name, fighter_data in fighters_data.items():
                    # Reconstruct Fighter object from dict
                    fighter = Fighter(**fighter_data)
                    self.fighter_database[name.lower()] = fighter  # Use lowercase for lookup
                
                logger.info(f"Loaded fighter database with {len(self.fighter_database)} fighters")
            else:
                logger.info("No existing fighter database found, building new one...")
                # Build database from scratch
                fighters_dict = await build_fighter_database()
                self.fighter_database = {name.lower(): fighter for name, fighter in fighters_dict.items()}
                logger.info(f"Built fighter database with {len(self.fighter_database)} fighters")
            
            self._database_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load fighter database: {e}")
            self.fighter_database = {}
            self._database_loaded = True
    
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
        """Discover UFC events from Wikipedia"""
        events = []
        
        try:
            soup = await self._fetch_page(self.EVENTS_LIST_URL)
            events = self._parse_events_list(soup, mode, since)
        except Exception as e:
            logger.error(f"Error discovering events from Wikipedia: {e}")
        
        logger.info(f"Discovered {len(events)} events from Wikipedia")
        return events
    
    def _parse_events_list(self, soup: BeautifulSoup, mode: str, since: Optional[str] = None) -> List[Dict]:
        """Parse the events list page"""
        events = []
        
        # Find tables containing event data
        tables = soup.find_all('table')
        
        for table in tables:
            # Look for tables that have event information
            headers = table.find('tr')
            if not headers:
                continue
            
            header_texts = [th.get_text(strip=True).lower() for th in headers.find_all(['th', 'td'])]
            
            # Check if this looks like an events table
            if not any(keyword in ' '.join(header_texts) for keyword in ['event', 'date', 'venue']):
                continue
            
            # Parse event rows
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                
                event_info = self._parse_event_row(cells)
                if event_info:
                    # Filter by mode and date
                    if self._should_include_event(event_info, mode, since):
                        events.append(event_info)
        
        return events
    
    def _parse_date_from_text(self, text: str) -> Optional[str]:
        """Parse date from a string using multiple patterns."""
        patterns = [
            r'\b(\w+)\s+(\d{1,2}),\s+(\d{4})\b',  # "June 28, 2025" or "Jun 28, 2025"
            r'\b(\d{1,2})\s+(\w+)\s+(\d{4})\b',   # "28 June 2025" or "28 Jun 2025"
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b'    # "2025-06-28"
        ]
        
        for pattern in patterns:
            date_match = re.search(pattern, text)
            if date_match:
                try:
                    groups = date_match.groups()
                    if len(groups) == 3:
                        if pattern == patterns[0]:  # Month Day, Year
                            month_name, day, year = groups
                            # Try full month name first, then abbreviated
                            try:
                                return datetime.strptime(f"{month_name} {day}, {year}", "%B %d, %Y").strftime('%Y-%m-%d')
                            except ValueError:
                                return datetime.strptime(f"{month_name} {day}, {year}", "%b %d, %Y").strftime('%Y-%m-%d')
                        elif pattern == patterns[1]:  # Day Month Year
                            day, month_name, year = groups
                            # Try full month name first, then abbreviated
                            try:
                                return datetime.strptime(f"{month_name} {day}, {year}", "%B %d, %Y").strftime('%Y-%m-%d')
                            except ValueError:
                                return datetime.strptime(f"{month_name} {day}, {year}", "%b %d, %Y").strftime('%Y-%m-%d')
                        elif pattern == patterns[2]:  # YYYY-MM-DD
                            year, month, day = groups
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except ValueError:
                    continue
        return None

    def _parse_event_row(self, cells) -> Optional[Dict]:
        """Parse an individual event row"""
        try:
            num_cells = len(cells)
            if num_cells < 4:
                return None

            # Determine column offsets based on table structure (past vs. scheduled)
            # Past events table has a '#' column which is a digit.
            is_past_event = cells[0].get_text(strip=True).isdigit()
            if is_past_event:
                if num_cells < 5:
                    return None
                event_col, date_col, venue_col, location_col = 1, 2, 3, 4
            else:  # Scheduled events table
                event_col, date_col, venue_col, location_col = 0, 1, 2, 3

            # --- Extract Event Name and URL ---
            event_cell = cells[event_col]
            event_link = event_cell.find('a', href=re.compile(r'/wiki/UFC'))
            if not event_link:
                return None
            
            event_name = event_link.get_text(strip=True)
            event_url = urljoin(self.BASE_URL, event_link.get('href'))
            event_id = event_link.get('href').split('/')[-1]
            
            # Note: Some events redirect to annual summary pages (handled by HARDCODED_DATES)
            # These events will get their correct dates when individually scraped

            # --- Extract Date ---
            date_cell = cells[date_col]
            date_text = date_cell.get_text(strip=True)
            event_date = self._parse_date_from_text(date_text)
            
            # --- Extract Venue and Location ---
            venue = cells[venue_col].get_text(strip=True)
            location = cells[location_col].get_text(strip=True)

            return {
                'id': event_id,
                'name': event_name,
                'date': event_date or datetime.now().strftime('%Y-%m-%d'),
                'venue': venue,
                'location': location,
                'url': event_url,
                'source': 'wikipedia'
            }
            
        except Exception as e:
            logger.error(f"Error parsing event row: {e}")
            return None
    
    def _should_include_event(self, event_info: Dict, mode: str, since: Optional[str]) -> bool:
        """Check if event should be included based on filters"""
        try:
            event_date = datetime.strptime(event_info['date'], '%Y-%m-%d')
            now = datetime.now()
            
            # Mode filter
            if mode == "future" and event_date <= now:
                return False
            elif mode == "historical" and event_date > now:
                return False
            
            # Date filter
            if since:
                since_date = datetime.strptime(since, '%Y-%m-%d')
                if event_date < since_date:
                    return False
            
            return True
            
        except ValueError:
            return True  # Include if date parsing fails
    
    async def scrape_event(self, event_id: str) -> Optional[UFCEvent]:
        """Scrape detailed event information"""
        event_url = f"{self.BASE_URL}/wiki/{event_id}"
        
        try:
            soup = await self._fetch_page(event_url)
            return await self._parse_event_details(soup, event_id, event_url)
        except Exception as e:
            logger.error(f"Failed to scrape event {event_id}: {e}")
            return None
    
    async def _parse_event_details(self, soup: BeautifulSoup, event_id: str, event_url: str) -> Optional[UFCEvent]:
        """Parse event details from Wikipedia event page"""
        try:
            # Check if this is a hardcoded event first (before any other extraction)
            if event_id in self.HARDCODED_DATES:
                logger.info(f"Using hardcoded date {self.HARDCODED_DATES[event_id]} for event {event_id}")
                event_date = self.HARDCODED_DATES[event_id]
                # For hardcoded events, use simplified event name from event_id
                event_name = event_id.replace('_', ' ').replace(':', ':')
            else:
                # Extract basic event information normally
                event_name = self._extract_event_name(soup)
                event_date = self._extract_event_date(soup, event_id)
            
            location_data = self._extract_venue_location(soup)
            status = self._determine_event_status(event_date)
            
            # Extract fight card with fighter records
            fights = await self._extract_fight_card_with_records(soup)

            # If no fights found in structured section, try parsing from results text
            if not fights:
                logger.info(f"No structured fight card found for {event_id}, attempting to parse from results text.")
                fights = await self._extract_fights_from_results_section_with_records(soup)
            
            event = UFCEvent(
                event_id=event_id,
                event_name=event_name,
                event_date=event_date,
                venue=location_data['venue'],
                location=location_data['location'],
                city=location_data['city'],
                state=location_data['state'],
                country=location_data['country'],
                status=status,
                fights=fights,
                source_urls={'wikipedia': event_url}
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error parsing event details: {e}")
            return None

    def _extract_fights_from_results_section(self, soup: BeautifulSoup) -> List[Fight]:
        """Extract fights from a less structured 'Results' section, typically a list."""
        fights = []
        
        # Look for the "Results" heading
        results_heading = soup.find(["h2", "h3"], string=re.compile(r'Results', re.I))
        if not results_heading:
            return fights

        # Find the next unordered list or ordered list
        current_element = results_heading.find_next_sibling()
        bout_order = 1
        while current_element:
            if current_element.name == 'ul' or current_element.name == 'ol':
                for item in current_element.find_all('li'):
                    fight_data = self._parse_fight_text(item.get_text())
                    if fight_data:
                        fight = self._create_fight_from_data(fight_data, bout_order, "main-card")
                        if fight:
                            fights.append(fight)
                            bout_order += 1
                break # Stop after finding the first list
            elif current_element.name == 'p': # Sometimes results are in paragraphs
                fight_data = self._parse_fight_text(current_element.get_text())
                if fight_data:
                    fight = self._create_fight_from_data(fight_data, bout_order, "main-card")
                    if fight:
                        fights.append(fight)
                        bout_order += 1
            
            # Stop if we hit another major heading or a table (which would be handled by _extract_fight_card)
            if current_element.name in ['h2', 'h3', 'table'] and current_element != results_heading:
                break

            current_element = current_element.find_next_sibling()

        return fights
    
    def _extract_event_name(self, soup: BeautifulSoup) -> str:
        """Extract event name from page title"""
        title = soup.find('h1', {'id': 'firstHeading'})
        if title:
            return title.get_text(strip=True)
        return "Unknown Event"
    
    def _extract_event_date(self, soup: BeautifulSoup, event_id: str = None) -> str:
        """Extract event date from infobox"""
        # First check if this is one of our hardcoded events
        if event_id and event_id in self.HARDCODED_DATES:
            logger.info(f"Using hardcoded date {self.HARDCODED_DATES[event_id]} for event {event_id}")
            return self.HARDCODED_DATES[event_id]
        
        infobox = soup.find('table', class_='infobox')
        if infobox:
            # Look for the Date row in infobox
            for row in infobox.find_all('tr'):
                th = row.find('th')
                td = row.find('td')
                
                if th and td and 'date' in th.get_text().lower():
                    # Found the date row, extract from td
                    date_text = td.get_text(strip=True)
                    parsed_date = self._parse_date_from_text(date_text)
                    if parsed_date:
                        return parsed_date
                    
                    # If first parsing failed, try cleaning the text more
                    # Remove references like [1], [2] etc.
                    cleaned_date = re.sub(r'\[\d+\]', '', date_text).strip()
                    parsed_date = self._parse_date_from_text(cleaned_date)
                    if parsed_date:
                        return parsed_date
        
        # Try to find date in page title (sometimes events have dates in titles)
        if title:
            title_text = title.get_text()
            parsed_date = self._parse_date_from_text(title_text)
            if parsed_date:
                return parsed_date
        
        # Try searching for common date patterns anywhere on the page
        page_text = soup.get_text()
        parsed_date = self._parse_date_from_text(page_text[:2000])  # First 2000 chars
        if parsed_date:
            return parsed_date
        
        logger.warning("Could not extract event date, using placeholder")
        return "1900-01-01"  # Use obvious placeholder instead of today's date
    
    def _extract_venue_location(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract venue and location details from infobox"""
        venue = None
        location = None
        city = None
        state = None
        country = None
        
        infobox = soup.find('table', class_='infobox')
        if infobox:
            for row in infobox.find_all('tr'):
                row_text = row.get_text().lower()
                if 'venue' in row_text:
                    venue = row.find_all('td')[-1].get_text(strip=True) if row.find_all('td') else None
                elif 'location' in row_text or 'city' in row_text:
                    location = row.find_all('td')[-1].get_text(strip=True) if row.find_all('td') else None
        
        # Parse location into components
        if location:
            location_details = self._parse_location_details(location)
            city = location_details['city']
            state = location_details['state']
            country = location_details['country']
        
        return {
            'venue': venue,
            'location': location,
            'city': city,
            'state': state,
            'country': country
        }
    
    def _determine_event_status(self, event_date: str) -> EventStatus:
        """Determine if event is completed or scheduled"""
        try:
            date_obj = datetime.strptime(event_date, '%Y-%m-%d')
            return EventStatus.COMPLETED if date_obj < datetime.now() else EventStatus.SCHEDULED
        except ValueError:
            return EventStatus.SCHEDULED
    
    async def _extract_fight_card(self, soup: BeautifulSoup) -> List[Fight]:
        """Extract fight card with proper segment classification"""
        raw_fights_data = []
        
        # Look for "Fight card" section
        fight_card_section = self._find_fight_card_section(soup)
        if not fight_card_section:
            logger.warning("Could not find fight card section")
            return []
        
        # Parse each segment
        segments = self._parse_fight_segments(fight_card_section)
        
        for segment_name, segment_fights in segments.items():
            for fight_data in segment_fights:
                raw_fights_data.append((fight_data, segment_name))
        
        # If no fights found in structured section, try parsing from results text
        if not raw_fights_data:
            logger.info("No structured fight card found, attempting to parse from results text.")
            text_fights_data = self._extract_fights_from_results_section(soup)
            for fight_data in text_fights_data:
                raw_fights_data.append((fight_data, "main-card")) # Default segment for text parsed fights

        fights = []
        total_fights = len(raw_fights_data)
        
        # Assign bout_order in descending order (main event gets highest bout_order)
        for i, (fight_data, segment_name) in enumerate(raw_fights_data):
            bout_order = total_fights - i
            fight = self._create_fight_from_data(fight_data, bout_order, segment_name)
            if fight:
                fights.append(fight)
        
        # Extract bonus awards
        bonuses = self._extract_bonus_awards(soup)
        self._assign_bonuses_to_fights(fights, bonuses)

        return fights

    def _extract_bonus_awards(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract bonus awards from the 'Bonus awards' section."""
        bonuses = {
            "fight_of_the_night": [],
            "performance_of_the_night": []
        }
        
        # Find the "Bonus awards" heading
        bonus_heading = soup.find(["h2", "h3"], string=re.compile(r'Bonus awards', re.I))
        if not bonus_heading:
            return bonuses

        # Find the list of bonus winners
        bonus_list = bonus_heading.find_next_sibling('ul')
        if not bonus_list:
            return bonuses

        for item in bonus_list.find_all('li'):
            text = item.get_text(strip=True)
            if "Fight of the Night:" in text:
                fighters = text.replace("Fight of the Night:", "").strip().split(' vs. ')
                bonuses["fight_of_the_night"].extend([f.strip() for f in fighters])
            elif "Performance of the Night:" in text:
                fighters = text.replace("Performance of the Night:", "").strip().split(',')
                bonuses["performance_of_the_night"].extend([f.strip() for f in fighters])
        
        return bonuses

    def _assign_bonuses_to_fights(self, fights: List[Fight], bonuses: Dict[str, List[str]]):
        """Assign bonus awards to the corresponding fights and fighters."""
        for fight in fights:
            # Assign Fight of the Night
            if (fight.fighter1.name in bonuses["fight_of_the_night"] and
                fight.fighter2.name in bonuses["fight_of_the_night"]):
                fight.fighter1.bonus = "Fight of the Night"
                fight.fighter2.bonus = "Fight of the Night"

            # Assign Performance of the Night
            if fight.fighter1.name in bonuses["performance_of_the_night"]:
                fight.fighter1.bonus = "Performance of the Night"
            if fight.fighter2.name in bonuses["performance_of_the_night"]:
                fight.fighter2.bonus = "Performance of the Night"
    
    def _find_fight_card_section(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the fight card section - Wikipedia uses 'Results' section"""
        # Look for the fight results table with class 'toccolours'
        fight_table = soup.find('table', class_='toccolours')
        
        if not fight_table:
            # Fallback to looking for "Fight card" section
            headings = soup.find_all(['h2', 'h3'], string=re.compile(r'Fight\s+card', re.I))
            
            for heading in headings:
                # Find the section after this heading
                current = heading.parent
                while current:
                    if current.name in ['h2', 'h3'] and current != heading.parent:
                        break
                    if current.find_all(['h4', 'h5']) or current.find_all('table'):
                        return current
                    current = current.next_sibling
            
            return None
        
        # Create a container div to hold the table for consistent parsing
        container = soup.new_tag('div')
        container.append(fight_table)
        return container
    
    def _parse_fight_segments(self, section: BeautifulSoup) -> Dict[str, List[Dict]]:
        """Parse fight segments from the fight card section"""
        segments = {}
        
        # Find the toccolours table
        table = section.find('table', class_='toccolours')
        if not table:
            return segments
        
        # Parse the table structure
        rows = table.find_all('tr')
        current_segment = "main-card"  # Default
        
        i = 0
        while i < len(rows):
            row = rows[i]
            cells = row.find_all(['th', 'td'])
            
            if len(cells) == 1:
                # This is a segment header row
                header_text = cells[0].get_text().lower()
                if 'main card' in header_text:
                    current_segment = "main-card"
                elif 'preliminary card' in header_text or 'prelim' in header_text:
                    if 'early' in header_text:
                        current_segment = "early-prelims"
                    else:
                        current_segment = "prelims"
                i += 1
                continue
            
            elif len(cells) > 1:
                # Check if this is a header row (contains "Weight class", etc.)
                first_cell_text = cells[0].get_text().lower()
                if 'weight class' in first_cell_text:
                    # Skip header rows
                    i += 1
                    continue
                
                # This is a fight data row
                if current_segment not in segments:
                    segments[current_segment] = []
                
                fight_data = self._parse_fight_row(row)
                if fight_data:
                    segments[current_segment].append(fight_data)
            
            i += 1
        
        return segments
    
    def _extract_fights_from_element(self, element: BeautifulSoup) -> List[Dict]:
        """Extract individual fights from a table or list"""
        fights = []
        
        if element.name == 'table':
            # Parse table rows
            rows = element.find_all('tr')[1:]  # Skip header
            for row in rows:
                fight_data = self._parse_fight_row(row)
                if fight_data:
                    fights.append(fight_data)
        
        elif element.name in ['ul', 'ol']:
            # Parse list items
            items = element.find_all('li')
            for item in items:
                fight_data = self._parse_fight_text(item.get_text())
                if fight_data:
                    fights.append(fight_data)
        
        return fights
    
    def _parse_fight_row(self, row: BeautifulSoup) -> Optional[Dict]:
        """Parse a fight from a table row."""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 5:  # Expect at least 5 columns for a valid fight
            return None

        try:
            # --- Column Mapping ---
            # Find the indices of key columns to handle table variations
            header_texts = [th.get_text(strip=True).lower() for th in row.find_previous('tr').find_all('th')]
            col_map = {text: i for i, text in enumerate(header_texts)}

            wc_col = col_map.get('weight class', 0)
            fighter1_col = col_map.get('fighter 1', 1)
            fighter2_col = col_map.get('fighter 2', 3)
            method_col = col_map.get('method', 4)
            round_col = col_map.get('round', 5)
            time_col = col_map.get('time', 6)

            # --- Data Extraction ---
            weight_class = cells[wc_col].get_text(strip=True)
            fighter1 = cells[fighter1_col].get_text(strip=True)
            fighter2 = cells[fighter2_col].get_text(strip=True)
            method = cells[method_col].get_text(strip=True) if len(cells) > method_col else ""
            round_num = cells[round_col].get_text(strip=True) if len(cells) > round_col else ""
            time = cells[time_col].get_text(strip=True) if len(cells) > time_col else ""

            # --- Winner Determination ---
            # The winner is usually the first fighter listed in the row
            winner = fighter1

            # --- Title Fight Detection ---
            # Check for champion notation "(c)" before cleaning names
            fighter1_is_champion = bool(re.search(r'\(c\)', fighter1, re.IGNORECASE))
            fighter2_is_champion = bool(re.search(r'\(c\)', fighter2, re.IGNORECASE))
            is_title_fight = fighter1_is_champion or fighter2_is_champion

            # Clean up fighter names (remove titles like "(c)")
            fighter1_clean = re.sub(r'\s*\([^)]*\)', '', fighter1).strip()
            fighter2_clean = re.sub(r'\s*\([^)]*\)', '', fighter2).strip()
            winner_clean = re.sub(r'\s*\([^)]*\)', '', winner).strip()

            return {
                'fighter1': fighter1_clean,
                'fighter2': fighter2_clean,
                'fighter1_is_champion': fighter1_is_champion,
                'fighter2_is_champion': fighter2_is_champion,
                'is_title_fight': is_title_fight,
                'winner': winner_clean,
                'method': method,
                'round': round_num,
                'time': time,
                'weight_class': weight_class
            }

        except (IndexError, AttributeError) as e:
            logger.error(f"Error parsing fight row: {e}\nRow: {row.prettify()}")
            return None
    
    def _parse_fight_text(self, text: str, weight_class: str = "Unknown") -> Optional[Dict]:
        """Parse fight information from text"""
        try:
            # Look for pattern: "Fighter1 def. Fighter2 via Method"
            match = re.search(r'(.+?)\s+def\.\s+(.+?)\s+(?:via|by)\s+(.+)', text)
            if match:
                winner, loser, method = match.groups()
                
                # Check for champion notation
                winner_is_champion = bool(re.search(r'\(c\)', winner, re.IGNORECASE))
                loser_is_champion = bool(re.search(r'\(c\)', loser, re.IGNORECASE))
                is_title_fight = winner_is_champion or loser_is_champion
                
                # Clean names
                winner_clean = re.sub(r'\s*\([^)]*\)', '', winner).strip()
                loser_clean = re.sub(r'\s*\([^)]*\)', '', loser).strip()
                
                return {
                    'fighter1': winner_clean,
                    'fighter2': loser_clean,
                    'fighter1_is_champion': winner_is_champion,
                    'fighter2_is_champion': loser_is_champion,
                    'is_title_fight': is_title_fight,
                    'winner': winner_clean,
                    'method': method.strip(),
                    'weight_class': weight_class
                }
            
            # Look for vs pattern: "Fighter1 vs Fighter2"
            vs_match = re.search(r'(.+?)\s+vs\.?\s+(.+)', text)
            if vs_match:
                fighter1, fighter2 = vs_match.groups()
                
                # Check for champion notation
                fighter1_is_champion = bool(re.search(r'\(c\)', fighter1, re.IGNORECASE))
                fighter2_is_champion = bool(re.search(r'\(c\)', fighter2, re.IGNORECASE))
                is_title_fight = fighter1_is_champion or fighter2_is_champion
                
                # Clean names
                fighter1_clean = re.sub(r'\s*\([^)]*\)', '', fighter1).strip()
                fighter2_clean = re.sub(r'\s*\([^)]*\)', '', fighter2).strip()
                
                return {
                    'fighter1': fighter1_clean,
                    'fighter2': fighter2_clean,
                    'fighter1_is_champion': fighter1_is_champion,
                    'fighter2_is_champion': fighter2_is_champion,
                    'is_title_fight': is_title_fight,
                    'weight_class': weight_class
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing fight text: {e}")
            return None
    
    def _create_fight_from_data(self, fight_data: Dict, bout_order: int, segment: str) -> Optional[Fight]:
        """Create a Fight object from parsed data"""
        try:
            # Create fighters with champion status
            fighter1 = Fighter(
                name=fight_data.get('fighter1', 'Unknown'),
                is_champion=fight_data.get('fighter1_is_champion', False)
            )
            fighter2 = Fighter(
                name=fight_data.get('fighter2', 'Unknown'),
                is_champion=fight_data.get('fighter2_is_champion', False)
            )
            
            weight_class = fight_data.get('weight_class', 'Unknown')
            
            # Determine title fight type - prioritize champion notation over weight class keywords
            if fight_data.get('is_title_fight', False):
                title_fight = TitleFightType.UNDISPUTED
            elif 'championship' in weight_class.lower() or 'title' in weight_class.lower():
                title_fight = TitleFightType.UNDISPUTED
            else:
                title_fight = TitleFightType.NONE
            
            # Clean fight data - convert empty strings to None for missing results
            method = fight_data.get('method')
            winner = fight_data.get('winner')
            
            # Convert empty/blank results to None
            if method is not None and method.strip() == "":
                method = None
                winner = None  # If no method, then no winner determined yet
            if winner is not None and winner.strip() == "":
                winner = None
                
            fight = Fight(
                bout_order=bout_order,
                fighter1=fighter1,
                fighter2=fighter2,
                weight_class=weight_class,
                title_fight=title_fight,
                method=method,
                winner=winner,
                segment=segment
            )
            
            return fight
            
        except Exception as e:
            logger.error(f"Error creating fight: {e}")
            return None

    async def _fetch_fighter_record(self, fighter_name: str) -> Optional[FighterRecord]:
        """Fetch fighter's MMA record from database only (fast lookup)"""
        try:
            # Ensure fighter database is loaded
            await self._load_fighter_database()
            
            if not self.fighter_database:
                return None
            
            # Try exact match first
            fighter_key = fighter_name.lower().strip()
            if fighter_key in self.fighter_database:
                database_fighter = self.fighter_database[fighter_key]
                if database_fighter.record_breakdown:
                    logger.debug(f"Found database record for {fighter_name}: {database_fighter.record_breakdown.to_record_string()}")
                    return database_fighter.record_breakdown
            
            # Try fuzzy matching for name variations
            for db_name, db_fighter in self.fighter_database.items():
                if self._names_match_fuzzy(fighter_name, db_name):
                    if db_fighter.record_breakdown:
                        logger.debug(f"Found database record for {fighter_name} (matched as {db_name}): {db_fighter.record_breakdown.to_record_string()}")
                        return db_fighter.record_breakdown
            
            # Fighter not found in database - that's okay, just return None
            logger.debug(f"Fighter {fighter_name} not found in database (likely retired/historical)")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching record for {fighter_name}: {e}")
            return None

    def _names_match_fuzzy(self, target_name: str, candidate_name: str) -> bool:
        """Fuzzy name matching for fighter database lookup"""
        target = target_name.lower().strip()
        candidate = candidate_name.lower().strip()
        
        # Exact match
        if target == candidate:
            return True
        
        # Remove common variations
        target_clean = target.replace('.', '').replace('-', ' ').replace('  ', ' ')
        candidate_clean = candidate.replace('.', '').replace('-', ' ').replace('  ', ' ')
        
        if target_clean == candidate_clean:
            return True
        
        # Check if all words in target are in candidate
        target_words = target_clean.split()
        candidate_words = candidate_clean.split()
        
        if len(target_words) >= 2 and len(candidate_words) >= 2:
            # Check if first and last names match
            if (target_words[0] == candidate_words[0] and 
                target_words[-1] == candidate_words[-1]):
                return True
        
        return False

    def _generate_fighter_urls(self, fighter_name: str) -> List[str]:
        """Generate potential Wikipedia URLs for a fighter"""
        urls = []
        
        # Clean fighter name for URL generation
        clean_name = fighter_name.strip()
        
        # Replace common name patterns
        url_name = clean_name.replace(' ', '_')
        url_name = re.sub(r'[^\w\s-]', '', url_name)  # Remove special characters except hyphens
        
        # Primary URL attempt
        urls.append(f"{self.BASE_URL}/wiki/{url_name}")
        
        # Try with disambiguation pages
        urls.append(f"{self.BASE_URL}/wiki/{url_name}_(fighter)")
        urls.append(f"{self.BASE_URL}/wiki/{url_name}_(mixed_martial_artist)")
        
        # Try with different name formats
        if ' ' in clean_name:
            # Try Last_Name,_First_Name format
            parts = clean_name.split(' ')
            if len(parts) >= 2:
                last_first = f"{parts[-1]},_{' '.join(parts[:-1])}"
                urls.append(f"{self.BASE_URL}/wiki/{last_first}")
        
        return urls

    def _parse_fighter_record_from_page(self, soup: BeautifulSoup) -> Optional[FighterRecord]:
        """Parse MMA record from fighter's Wikipedia page"""
        try:
            # Look for MMA record in infobox
            infobox = soup.find('table', class_='infobox')
            if not infobox:
                return None
            
            record_info = {}
            
            # Search for record-related rows in infobox
            for row in infobox.find_all('tr'):
                th = row.find('th')
                td = row.find('td')
                
                if not th or not td:
                    continue
                    
                header_text = th.get_text().lower().strip()
                value_text = td.get_text().strip()
                
                # Look for different record formats
                if 'mma record' in header_text or 'record' in header_text:
                    # Parse traditional W-L-D format like "22-5-0"
                    record_match = re.search(r'(\d+)[-–](\d+)[-–](\d+)', value_text)
                    if record_match:
                        record_info['wins'] = int(record_match.group(1))
                        record_info['losses'] = int(record_match.group(2))
                        record_info['draws'] = int(record_match.group(3))
                        
                        # Check for no contests
                        nc_match = re.search(r'\((\d+)\s*NC\)', value_text, re.IGNORECASE)
                        if nc_match:
                            record_info['no_contests'] = int(nc_match.group(1))
                
                elif 'wins' in header_text:
                    wins_match = re.search(r'(\d+)', value_text)
                    if wins_match:
                        record_info['wins'] = int(wins_match.group(1))
                        
                elif 'losses' in header_text:
                    losses_match = re.search(r'(\d+)', value_text)
                    if losses_match:
                        record_info['losses'] = int(losses_match.group(1))
                        
                elif 'draws' in header_text:
                    draws_match = re.search(r'(\d+)', value_text)
                    if draws_match:
                        record_info['draws'] = int(draws_match.group(1))
            
            # Create FighterRecord if we found any record data
            if record_info:
                return FighterRecord(**record_info)
                
            return None
            
        except Exception as e:
            logger.error(f"Error parsing fighter record from page: {e}")
            return None

    def _parse_location_details(self, location_text: str) -> Dict[str, Optional[str]]:
        """Parse location string into city, state, and country components"""
        if not location_text:
            return {'city': None, 'state': None, 'country': None}
        
        try:
            # Clean up the location text
            location = location_text.strip()
            
            # Common patterns for location parsing
            # Format: "City, State, Country" or "City, Country"
            parts = [part.strip() for part in location.split(',')]
            
            city = None
            state = None
            country = None
            
            if len(parts) >= 3:
                # City, State, Country
                city = parts[0]
                state = parts[1]
                country = parts[2]
            elif len(parts) == 2:
                # City, Country (or City, State)
                city = parts[0]
                # Try to determine if second part is a US state or country
                second_part = parts[1].strip()
                
                # Common US states and territories
                us_states = {
                    'california', 'nevada', 'new york', 'florida', 'texas', 'illinois',
                    'massachusetts', 'new jersey', 'pennsylvania', 'georgia', 'ohio',
                    'michigan', 'north carolina', 'virginia', 'washington', 'arizona',
                    'colorado', 'maryland', 'tennessee', 'indiana', 'missouri', 'wisconsin',
                    'alabama', 'louisiana', 'kentucky', 'oregon', 'oklahoma', 'connecticut',
                    'utah', 'iowa', 'arkansas', 'mississippi', 'kansas', 'new mexico',
                    'nebraska', 'west virginia', 'idaho', 'hawaii', 'new hampshire',
                    'maine', 'montana', 'rhode island', 'delaware', 'south dakota',
                    'north dakota', 'alaska', 'vermont', 'wyoming'
                }
                
                if second_part.lower() in us_states:
                    state = second_part
                    country = 'United States'
                else:
                    country = second_part
            elif len(parts) == 1:
                # Just city or country
                city = parts[0]
            
            return {
                'city': city,
                'state': state, 
                'country': country
            }
            
        except Exception as e:
            logger.error(f"Error parsing location '{location_text}': {e}")
            return {'city': None, 'state': None, 'country': None}

    async def _extract_fight_card_with_records(self, soup: BeautifulSoup) -> List[Fight]:
        """Extract fight card with fighter records"""
        raw_fights_data = []
        
        # Look for "Fight card" section
        fight_card_section = self._find_fight_card_section(soup)
        if not fight_card_section:
            logger.warning("Could not find fight card section")
            return []
        
        # Parse each segment
        segments = self._parse_fight_segments(fight_card_section)
        
        for segment_name, segment_fights in segments.items():
            for fight_data in segment_fights:
                raw_fights_data.append((fight_data, segment_name))
        
        fights = []
        total_fights = len(raw_fights_data)
        
        # Assign bout_order in descending order (main event gets highest bout_order)
        for i, (fight_data, segment_name) in enumerate(raw_fights_data):
            bout_order = total_fights - i
            fight = await self._create_fight_with_records(fight_data, bout_order, segment_name)
            if fight:
                fights.append(fight)
        
        # Extract bonus awards
        bonuses = self._extract_bonus_awards(soup)
        self._assign_bonuses_to_fights(fights, bonuses)

        return fights

    async def _extract_fights_from_results_section_with_records(self, soup: BeautifulSoup) -> List[Fight]:
        """Extract fights from results section with fighter records"""
        fights = []
        
        # Look for the "Results" heading
        results_heading = soup.find(["h2", "h3"], string=re.compile(r'Results', re.I))
        if not results_heading:
            return fights

        # Find the next unordered list or ordered list
        current_element = results_heading.find_next_sibling()
        bout_order = 1
        while current_element:
            if current_element.name == 'ul' or current_element.name == 'ol':
                for item in current_element.find_all('li'):
                    fight_data = self._parse_fight_text(item.get_text())
                    if fight_data:
                        fight = await self._create_fight_with_records(fight_data, bout_order, "main-card")
                        if fight:
                            fights.append(fight)
                            bout_order += 1
                break # Stop after finding the first list
            elif current_element.name == 'p': # Sometimes results are in paragraphs
                fight_data = self._parse_fight_text(current_element.get_text())
                if fight_data:
                    fight = await self._create_fight_with_records(fight_data, bout_order, "main-card")
                    if fight:
                        fights.append(fight)
                        bout_order += 1
            
            # Stop if we hit another major heading or a table
            if current_element.name in ['h2', 'h3', 'table'] and current_element != results_heading:
                break

            current_element = current_element.find_next_sibling()

        return fights

    async def _create_fight_with_records(self, fight_data: Dict, bout_order: int, segment: str) -> Optional[Fight]:
        """Create a Fight object with fighter records"""
        try:
            # Extract fighter names and champion status
            fighter1_name = fight_data.get('fighter1', 'Unknown')
            fighter2_name = fight_data.get('fighter2', 'Unknown')
            fighter1_is_champion = fight_data.get('fighter1_is_champion', False)
            fighter2_is_champion = fight_data.get('fighter2_is_champion', False)
            
            # Fetch fighter records (with rate limiting built in)
            logger.info(f"Fetching records for {fighter1_name} vs {fighter2_name}")
            
            fighter1_record = await self._fetch_fighter_record(fighter1_name)
            fighter2_record = await self._fetch_fighter_record(fighter2_name)
            
            # Create fighters with records
            fighter1 = Fighter(
                name=fighter1_name,
                is_champion=fighter1_is_champion,
                record_breakdown=fighter1_record,
                record=fighter1_record.to_record_string() if fighter1_record else None,
                wikipedia_url=self._generate_fighter_urls(fighter1_name)[0] if fighter1_record else None
            )
            fighter2 = Fighter(
                name=fighter2_name,
                is_champion=fighter2_is_champion,
                record_breakdown=fighter2_record,
                record=fighter2_record.to_record_string() if fighter2_record else None,
                wikipedia_url=self._generate_fighter_urls(fighter2_name)[0] if fighter2_record else None
            )
            
            weight_class = fight_data.get('weight_class', 'Unknown')
            
            # Determine title fight type
            if fight_data.get('is_title_fight', False):
                title_fight = TitleFightType.UNDISPUTED
            elif 'championship' in weight_class.lower() or 'title' in weight_class.lower():
                title_fight = TitleFightType.UNDISPUTED
            else:
                title_fight = TitleFightType.NONE
            
            # Clean fight data
            method = fight_data.get('method')
            winner = fight_data.get('winner')
            
            if method is not None and method.strip() == "":
                method = None
                winner = None
            if winner is not None and winner.strip() == "":
                winner = None
                
            fight = Fight(
                bout_order=bout_order,
                fighter1=fighter1,
                fighter2=fighter2,
                weight_class=weight_class,
                title_fight=title_fight,
                method=method,
                winner=winner,
                segment=segment
            )
            
            return fight
            
        except Exception as e:
            logger.error(f"Error creating fight with records: {e}")
            return None