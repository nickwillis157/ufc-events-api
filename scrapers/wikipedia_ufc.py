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

from models.ufc_models import UFCEvent, Fight, Fighter, EventStatus, TitleFightType
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class WikipediaUFCScraper:
    """Scraper for Wikipedia UFC data - much more reliable"""
    
    BASE_URL = "https://en.wikipedia.org"
    EVENTS_LIST_URL = f"{BASE_URL}/wiki/List_of_UFC_events"
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'UFC-Scraper/1.0 (Educational/Research Purpose)'
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
            # Extract basic event information
            event_name = self._extract_event_name(soup)
            event_date = self._extract_event_date(soup)
            venue, location = self._extract_venue_location(soup)
            status = self._determine_event_status(event_date)
            
            # Extract fight card
            fights = await self._extract_fight_card(soup)

            # If no fights found in structured section, try parsing from results text
            if not fights:
                logger.info(f"No structured fight card found for {event_id}, attempting to parse from results text.")
                fights = self._extract_fights_from_results_section(soup)
            
            event = UFCEvent(
                event_id=event_id,
                event_name=event_name,
                event_date=event_date,
                venue=venue,
                location=location,
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
    
    def _extract_event_date(self, soup: BeautifulSoup) -> str:
        """Extract event date from infobox"""
        infobox = soup.find('table', class_='infobox')
        if infobox:
            for row in infobox.find_all('tr'):
                if 'date' in row.get_text().lower():
                    date_text = row.get_text()
                    parsed_date = self._parse_date_from_text(date_text)
                    if parsed_date:
                        return parsed_date
        
        logger.warning("Could not extract event date, using today's date as fallback")
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_venue_location(self, soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
        """Extract venue and location from infobox"""
        venue = None
        location = None
        
        infobox = soup.find('table', class_='infobox')
        if infobox:
            for row in infobox.find_all('tr'):
                row_text = row.get_text().lower()
                if 'venue' in row_text:
                    venue = row.find_all('td')[-1].get_text(strip=True) if row.find_all('td') else None
                elif 'location' in row_text:
                    location = row.find_all('td')[-1].get_text(strip=True) if row.find_all('td') else None
        
        return venue, location
    
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

            # Clean up fighter names (remove titles like "(c)")
            fighter1 = re.sub(r'\s*\([^)]*\)', '', fighter1).strip()
            fighter2 = re.sub(r'\s*\([^)]*\)', '', fighter2).strip()
            winner = re.sub(r'\s*\([^)]*\)', '', winner).strip()

            return {
                'fighter1': fighter1,
                'fighter2': fighter2,
                'winner': winner,
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
                return {
                    'fighter1': winner.strip(),
                    'fighter2': loser.strip(),
                    'winner': winner.strip(),
                    'method': method.strip(),
                    'weight_class': weight_class
                }
            
            # Look for vs pattern: "Fighter1 vs Fighter2"
            vs_match = re.search(r'(.+?)\s+vs\.?\s+(.+)', text)
            if vs_match:
                fighter1, fighter2 = vs_match.groups()
                return {
                    'fighter1': fighter1.strip(),
                    'fighter2': fighter2.strip(),
                    'weight_class': weight_class
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing fight text: {e}")
            return None
    
    def _create_fight_from_data(self, fight_data: Dict, bout_order: int, segment: str) -> Optional[Fight]:
        """Create a Fight object from parsed data"""
        try:
            fighter1 = Fighter(name=fight_data.get('fighter1', 'Unknown'))
            fighter2 = Fighter(name=fight_data.get('fighter2', 'Unknown'))
            
            weight_class = fight_data.get('weight_class', 'Unknown')
            title_fight = TitleFightType.UNDISPUTED if 'championship' in weight_class.lower() or 'title' in weight_class.lower() else TitleFightType.NONE
            
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