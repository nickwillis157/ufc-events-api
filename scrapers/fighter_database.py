"""
UFC Fighter Database Scraper - Scrapes comprehensive fighter list from Wikipedia
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ufc_models import Fighter, FighterRecord
from utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class UFCFighterDatabaseScraper:
    """Scraper for Wikipedia's List of current UFC fighters page"""
    
    FIGHTERS_LIST_URL = "https://en.wikipedia.org/wiki/List_of_current_UFC_fighters"
    
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
    
    async def scrape_fighter_database(self) -> Dict[str, Fighter]:
        """Scrape all fighters from the UFC fighters list page"""
        try:
            logger.info("Fetching UFC fighters database...")
            soup = await self._fetch_page(self.FIGHTERS_LIST_URL)
            
            fighters_dict = {}
            
            # Find all weight class sections
            weight_class_sections = self._find_weight_class_sections(soup)
            
            for weight_class, table in weight_class_sections.items():
                logger.info(f"Processing {weight_class} fighters...")
                fighters = self._parse_fighters_table(table, weight_class)
                
                for fighter in fighters:
                    # Use name as key, handle duplicates by adding weight class
                    key = fighter.name
                    if key in fighters_dict:
                        # Handle duplicate names by adding weight class
                        key = f"{fighter.name} ({weight_class})"
                    
                    fighters_dict[key] = fighter
            
            logger.info(f"Successfully scraped {len(fighters_dict)} fighters")
            return fighters_dict
            
        except Exception as e:
            logger.error(f"Error scraping fighter database: {e}")
            return {}
    
    def _find_weight_class_sections(self, soup: BeautifulSoup) -> Dict[str, BeautifulSoup]:
        """Find all weight class sections and their tables"""
        weight_class_sections = {}
        
        # Look for weight class headings
        weight_class_patterns = [
            r'Heavyweight', r'Light Heavyweight', r'Middleweight', r'Welterweight',
            r'Lightweight', r'Featherweight', r'Bantamweight', r'Flyweight',
            r"Women's Featherweight", r"Women's Bantamweight", r"Women's Flyweight", 
            r"Women's Strawweight"
        ]
        
        for pattern in weight_class_patterns:
            # Find heading
            heading = soup.find(['h2', 'h3', 'h4'], string=re.compile(pattern, re.IGNORECASE))
            if not heading:
                # Try finding by id or class
                heading = soup.find(['h2', 'h3', 'h4'], id=re.compile(pattern.replace(' ', '_'), re.IGNORECASE))
            
            if heading:
                # Find the next table after this heading
                table = heading.find_next('table', class_='wikitable')
                if table:
                    weight_class_sections[pattern] = table
                    logger.debug(f"Found table for {pattern}")
        
        return weight_class_sections
    
    def _parse_fighters_table(self, table: BeautifulSoup, weight_class: str) -> List[Fighter]:
        """Parse fighters from a weight class table"""
        fighters = []
        
        # Find table headers to understand column structure
        header_row = table.find('tr')
        if not header_row:
            return fighters
        
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        # Map column names - focus on MMA record only
        name_col = self._find_column_index(headers, ['name', 'fighter'])
        record_col = self._find_column_index(headers, ['mma record'])  # Only MMA record
        country_col = self._find_column_index(headers, ['iso', 'country'])
        age_col = self._find_column_index(headers, ['age'])
        height_col = self._find_column_index(headers, ['ht.', 'height'])
        nickname_col = self._find_column_index(headers, ['nickname'])
        
        logger.debug(f"Headers found: {headers}")
        logger.debug(f"MMA record column: {record_col}")
        
        # Process each fighter row
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:  # Skip rows with too few columns
                continue
            
            try:
                fighter = self._parse_fighter_row(
                    cells, name_col, record_col, country_col, 
                    age_col, height_col, nickname_col, weight_class
                )
                if fighter:
                    fighters.append(fighter)
            except Exception as e:
                logger.debug(f"Error parsing fighter row: {e}")
                continue
        
        return fighters
    
    def _find_column_index(self, headers: List[str], possible_names: List[str]) -> Optional[int]:
        """Find the index of a column by possible header names"""
        for i, header in enumerate(headers):
            for name in possible_names:
                if name in header:
                    return i
        return None
    
    def _parse_fighter_row(self, cells, name_col: Optional[int], record_col: Optional[int], 
                          country_col: Optional[int], age_col: Optional[int], 
                          height_col: Optional[int], nickname_col: Optional[int], 
                          weight_class: str) -> Optional[Fighter]:
        """Parse a single fighter row"""
        
        # Extract name
        name = None
        if name_col is not None and name_col < len(cells):
            name_cell = cells[name_col]
            # Look for links first (fighter names are usually linked)
            name_link = name_cell.find('a')
            if name_link:
                name = name_link.get_text(strip=True)
            else:
                name = name_cell.get_text(strip=True)
        
        if not name:
            return None
        
        # Extract record
        record_breakdown = None
        record_string = None
        if record_col is not None and record_col < len(cells):
            record_text = cells[record_col].get_text(strip=True)
            record_breakdown = self._parse_record_string(record_text)
            if record_breakdown:
                record_string = record_breakdown.to_record_string()
        
        # Extract country
        country = None
        if country_col is not None and country_col < len(cells):
            country_cell = cells[country_col]
            # Look for country name in text or alt text of flag images
            img = country_cell.find('img')
            if img and img.get('alt'):
                country = img.get('alt')
            else:
                country = country_cell.get_text(strip=True)
        
        # Extract age
        age = None
        if age_col is not None and age_col < len(cells):
            age_text = cells[age_col].get_text(strip=True)
            age_match = re.search(r'(\d+)', age_text)
            if age_match:
                age = int(age_match.group(1))
        
        # Extract height
        height = None
        if height_col is not None and height_col < len(cells):
            height = cells[height_col].get_text(strip=True)
        
        # Extract nickname
        nickname = None
        if nickname_col is not None and nickname_col < len(cells):
            nickname = cells[nickname_col].get_text(strip=True)
            if nickname and nickname.strip() in ['', '-', 'N/A']:
                nickname = None
        
        # Create Fighter object
        fighter = Fighter(
            name=name,
            record=record_string,
            record_breakdown=record_breakdown,
            country=country,
            age=age,
            height=height,
            nickname=nickname
        )
        
        return fighter
    
    def _parse_record_string(self, record_text: str) -> Optional[FighterRecord]:
        """Parse MMA record string like '22-3-0' or '22-3-0 (1 NC)'"""
        if not record_text:
            return None
        
        # Look for W-L-D pattern (handles both regular hyphens and en-dashes)
        record_match = re.search(r'(\d+)[-–](\d+)[-–](\d+)', record_text)
        if not record_match:
            # Try W-L pattern (no draws column)
            record_match = re.search(r'(\d+)[-–](\d+)', record_text)
            if record_match:
                wins = int(record_match.group(1))
                losses = int(record_match.group(2))
                draws = 0  # Default to 0 draws
            else:
                return None
        else:
            wins = int(record_match.group(1))
            losses = int(record_match.group(2))
            draws = int(record_match.group(3))
        
        # Look for no contests
        no_contests = None
        nc_match = re.search(r'\((\d+)\s*NC\)', record_text, re.IGNORECASE)
        if nc_match:
            no_contests = int(nc_match.group(1))
        
        return FighterRecord(
            wins=wins,
            losses=losses,
            draws=draws if draws > 0 else None,
            no_contests=no_contests
        )


async def build_fighter_database() -> Dict[str, Fighter]:
    """Build comprehensive fighter database from Wikipedia"""
    rate_limiter = RateLimiter(requests_per_second=1.0)
    scraper = UFCFighterDatabaseScraper(rate_limiter)
    return await scraper.scrape_fighter_database()


if __name__ == "__main__":
    import asyncio
    import json
    
    async def main():
        fighters_db = await build_fighter_database()
        
        print(f"Scraped {len(fighters_db)} fighters")
        
        # Save to file
        fighters_dict = {}
        for name, fighter in fighters_db.items():
            fighters_dict[name] = fighter.model_dump()
        
        with open('data/fighter_database.json', 'w') as f:
            json.dump(fighters_dict, f, indent=2, default=str)
        
        print("Fighter database saved to data/fighter_database.json")
    
    asyncio.run(main())