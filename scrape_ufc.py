#!/usr/bin/env python3
"""
UFC Event and Fight Data Scraper

A comprehensive scraper for UFC events and fight data from multiple sources.
Supports both historical and upcoming events with rich fight details.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import click
from scrapers.ufc_stats import UFCStatsScaper
from scrapers.ufc_official import UFCOfficialScraper
from scrapers.espn_mma import ESPNMMAScraper
from scrapers.wikipedia_ufc import WikipediaUFCScraper
from models.ufc_models import UFCEvent, Fight
from utils.database import DatabaseManager
from utils.rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UFCScraper:
    """Main UFC scraper orchestrator"""
    
    def __init__(self, rate_limit: float = 2.0, output_dir: str = "data"):
        self.rate_limiter = RateLimiter(rate_limit)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize scrapers
        self.ufc_stats = UFCStatsScaper(self.rate_limiter)
        self.ufc_official = UFCOfficialScraper(self.rate_limiter)
        self.espn_mma = ESPNMMAScraper(self.rate_limiter)
        self.wikipedia = WikipediaUFCScraper(self.rate_limiter)
        
        self.db_manager = None
    
    def enable_database(self, db_path: str = "ufc_data.db"):
        """Enable SQLite database storage"""
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.create_tables()
    
    async def scrape_events(self, 
                          mode: str = "full",
                          since: Optional[str] = None,
                          event_id: Optional[str] = None) -> List[UFCEvent]:
        """
        Scrape UFC events based on mode
        
        Args:
            mode: 'full', 'future', 'historical'
            since: ISO date string for filtering
            event_id: Specific event ID to scrape
        """
        events = []
        
        if event_id:
            # Scrape single event
            event = await self._scrape_single_event(event_id)
            if event:
                events.append(event)
        else:
            # Discover events from multiple sources
            discovered_events = await self._discover_events(mode, since)
            
            # Scrape each event
            for event_info in discovered_events:
                try:
                    event = await self._scrape_event_details(event_info)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.error(f"Failed to scrape event {event_info}: {e}")
                    continue
        
        return events
    
    async def _discover_events(self, mode: str, since: Optional[str]) -> List[Dict]:
        """Discover events from multiple sources"""
        discovered = []
        
        # Get events from Wikipedia (primary source for reliability)
        wikipedia_events = await self.wikipedia.discover_events(mode, since)
        discovered.extend(wikipedia_events)
        
        # Only use other sources as fallback if Wikipedia found no events
        if not wikipedia_events:
            logger.info("Wikipedia found no events, trying fallback sources...")
            
            # Get events from UFCStats (backup)
            ufc_stats_events = await self.ufc_stats.discover_events(mode, since)
            discovered.extend(ufc_stats_events)
            
            # Get events from UFC.com (backup)
            ufc_official_events = await self.ufc_official.discover_events(mode, since)
            discovered.extend(ufc_official_events)
        
        # Deduplicate events
        unique_events = self._deduplicate_events(discovered)
        
        logger.info(f"Discovered {len(unique_events)} unique events")
        return unique_events
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """Remove duplicate events based on date and name similarity"""
        unique = []
        seen = set()
        
        for event in events:
            # Create a key for deduplication
            key = (event.get('date'), event.get('name', '').lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(event)
        
        return unique
    
    async def _scrape_single_event(self, event_id: str) -> Optional[UFCEvent]:
        """Scrape a single event by ID"""
        # Try Wikipedia first (most reliable for fight cards)
        event = await self.wikipedia.scrape_event(event_id)
        if event:
            return event
        
        # Try UFCStats
        event = await self.ufc_stats.scrape_event(event_id)
        if event:
            return event
        
        # Try UFC.com
        event = await self.ufc_official.scrape_event(event_id)
        return event
    
    async def _scrape_event_details(self, event_info: Dict) -> Optional[UFCEvent]:
        """Scrape detailed event information"""
        # Primary scraper based on source
        if event_info.get('source') == 'wikipedia':
            return await self.wikipedia.scrape_event(event_info['id'])
        elif event_info.get('source') == 'ufcstats':
            return await self.ufc_stats.scrape_event(event_info['id'])
        elif event_info.get('source') == 'ufc_official':
            return await self.ufc_official.scrape_event(event_info['id'])
        
        return None
    
    def save_events(self, events: List[UFCEvent]):
        """Save events to JSON files and optionally database"""
        for event in events:
            # Save to JSON
            filename = f"{event.event_id}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Use model_dump with mode='json' to handle datetime serialization
                event_dict = event.model_dump(mode='json')
                json.dump(event_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved event data to {filepath}")
            
            # Save to database if enabled
            if self.db_manager:
                self.db_manager.save_event(event)


@click.command()
@click.option('--mode', type=click.Choice(['full', 'future', 'historical']), 
              default='full', help='Scraping mode')
@click.option('--since', type=str, help='Start date (YYYY-MM-DD)')
@click.option('--event-id', type=str, help='Specific event ID to scrape')
@click.option('--db', is_flag=True, help='Enable database storage')
@click.option('--rate-limit', type=float, default=2.0, 
              help='Rate limit (requests per second)')
@click.option('--output-dir', type=str, default='data', 
              help='Output directory for JSON files')
def cli(mode: str, since: Optional[str], event_id: Optional[str], 
        db: bool, rate_limit: float, output_dir: str):
    """UFC Event and Fight Data Scraper"""
    
    async def run_scraper():
        scraper = UFCScraper(rate_limit=rate_limit, output_dir=output_dir)
        
        if db:
            scraper.enable_database()
        
        try:
            events = await scraper.scrape_events(mode=mode, since=since, event_id=event_id)
            scraper.save_events(events)
            
            click.echo(f"Successfully scraped {len(events)} events")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            click.echo(f"Error: {e}", err=True)
    
    asyncio.run(run_scraper())


if __name__ == '__main__':
    cli()