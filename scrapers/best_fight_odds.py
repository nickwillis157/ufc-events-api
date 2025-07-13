"""
BestFightOdds.com betting odds scraper
"""

import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from rapidfuzz import fuzz

from models.ufc_models import FightOdds
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BestFightOddsScraper:
    """Scraper for BestFightOdds.com"""
    
    BASE_URL = "https://www.bestfightodds.com"
    
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
    
    async def get_event_odds(self, event_name: str, event_date: str) -> Dict[str, FightOdds]:
        """
        Get betting odds for an event
        
        Args:
            event_name: Name of the UFC event
            event_date: Date of the event (YYYY-MM-DD)
            
        Returns:
            Dict mapping fight keys to FightOdds objects
        """
        odds_data = {}
        
        try:
            # Search for the event
            event_url = await self._find_event_url(event_name, event_date)
            if not event_url:
                logger.warning(f"Could not find odds for event: {event_name}")
                return odds_data
            
            # Scrape odds from event page
            soup = await self._fetch_page(event_url)
            odds_data = await self._parse_event_odds(soup)
            
        except Exception as e:
            logger.error(f"Error getting odds for {event_name}: {e}")
        
        return odds_data
    
    async def _find_event_url(self, event_name: str, event_date: str) -> Optional[str]:
        """Find the URL for a specific event"""
        try:
            # Try to construct URL from event name
            # BestFightOdds uses format like /events/ufc-305-du-plessis-vs-adesanya
            clean_name = self._clean_event_name(event_name)
            potential_url = f"{self.BASE_URL}/events/{clean_name}"
            
            # Test if URL exists
            await self.rate_limiter.wait()
            response = self.session.head(potential_url, timeout=10)
            if response.status_code == 200:
                return potential_url
            
            # If direct URL doesn't work, try searching the events page
            events_url = f"{self.BASE_URL}/events"
            soup = await self._fetch_page(events_url)
            
            # Look for event links
            event_links = soup.find_all('a', href=re.compile(r'/events/'))
            
            for link in event_links:
                link_text = link.text.strip().lower()
                if self._is_event_match(link_text, event_name, event_date):
                    return urljoin(self.BASE_URL, link.get('href'))
            
        except Exception as e:
            logger.error(f"Error finding event URL: {e}")
        
        return None
    
    def _clean_event_name(self, event_name: str) -> str:
        """Clean event name for URL construction"""
        # Remove "UFC" prefix and convert to URL-friendly format
        name = event_name.lower()
        name = re.sub(r'^ufc\s*\d+:?\s*', '', name)  # Remove UFC number
        name = re.sub(r'[^\w\s-]', '', name)  # Remove special chars
        name = re.sub(r'\s+', '-', name.strip())  # Replace spaces with hyphens
        return name
    
    def _is_event_match(self, link_text: str, event_name: str, event_date: str) -> bool:
        """Check if a link matches the target event"""
        # Use fuzzy matching to compare event names
        similarity = fuzz.partial_ratio(link_text, event_name.lower())
        return similarity > 80  # 80% similarity threshold
    
    async def _parse_event_odds(self, soup: BeautifulSoup) -> Dict[str, FightOdds]:
        """Parse odds from an event page"""
        odds_data = {}
        
        try:
            # Find odds tables or sections
            odds_tables = soup.find_all('table', class_='odds-table')
            if not odds_tables:
                odds_tables = soup.find_all('div', class_='fight-odds')
            
            for table in odds_tables:
                fight_odds = await self._parse_fight_odds(table)
                if fight_odds:
                    # Create a key for the fight (fighter names)
                    fight_key = f"{fight_odds.get('fighter1', 'unknown')}_vs_{fight_odds.get('fighter2', 'unknown')}"
                    odds_data[fight_key] = fight_odds['odds']
        
        except Exception as e:
            logger.error(f"Error parsing event odds: {e}")
        
        return odds_data
    
    async def _parse_fight_odds(self, table_element) -> Optional[Dict]:
        """Parse odds for a single fight"""
        try:
            # Extract fighter names
            fighter_elements = table_element.find_all('td', class_='fighter-name')
            if len(fighter_elements) < 2:
                return None
            
            fighter1 = fighter_elements[0].text.strip()
            fighter2 = fighter_elements[1].text.strip()
            
            # Extract odds
            odds_elements = table_element.find_all('td', class_='odds')
            if len(odds_elements) < 2:
                return None
            
            # Parse opening and closing odds
            f1_odds = self._parse_odds_text(odds_elements[0].text.strip())
            f2_odds = self._parse_odds_text(odds_elements[1].text.strip())
            
            # Try to find opening odds (might be in separate columns)
            opening_odds = table_element.find_all('td', class_='opening-odds')
            f1_open = f1_odds  # Default to current odds
            f2_open = f2_odds
            
            if len(opening_odds) >= 2:
                f1_open = self._parse_odds_text(opening_odds[0].text.strip())
                f2_open = self._parse_odds_text(opening_odds[1].text.strip())
            
            odds = FightOdds(
                f1_open=f1_open,
                f2_open=f2_open,
                f1_close=f1_odds,
                f2_close=f2_odds,
                source="BestFightOdds",
                last_updated=datetime.now()
            )
            
            return {
                'fighter1': fighter1,
                'fighter2': fighter2,
                'odds': odds
            }
            
        except Exception as e:
            logger.error(f"Error parsing fight odds: {e}")
            return None
    
    def _parse_odds_text(self, odds_text: str) -> Optional[float]:
        """Parse odds text to float"""
        if not odds_text or odds_text == '-':
            return None
        
        # Remove any non-numeric characters except +, -, and .
        clean_odds = re.sub(r'[^\d+\-.]', '', odds_text)
        
        try:
            return float(clean_odds)
        except ValueError:
            return None
    
    async def get_fighter_odds_history(self, fighter_name: str) -> List[Dict]:
        """Get historical odds for a specific fighter"""
        try:
            # Search for fighter
            search_url = f"{self.BASE_URL}/search"
            params = {'q': fighter_name}
            
            await self.rate_limiter.wait()
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse search results
            fight_links = soup.find_all('a', href=re.compile(r'/events/'))
            
            odds_history = []
            for link in fight_links:
                # Extract fight information
                fight_info = await self._parse_fight_link(link)
                if fight_info:
                    odds_history.append(fight_info)
            
            return odds_history
            
        except Exception as e:
            logger.error(f"Error getting fighter odds history: {e}")
            return []
    
    async def _parse_fight_link(self, link_element) -> Optional[Dict]:
        """Parse fight information from a search result link"""
        try:
            href = link_element.get('href')
            text = link_element.text.strip()
            
            # Extract event and opponent information
            # This would need to be customized based on BestFightOdds HTML structure
            
            return {
                'event_url': urljoin(self.BASE_URL, href),
                'fight_text': text,
                'date': None  # Would need to extract from page
            }
            
        except Exception as e:
            logger.error(f"Error parsing fight link: {e}")
            return None