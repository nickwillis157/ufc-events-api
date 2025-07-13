#!/usr/bin/env python3
"""
Basic usage examples for UFC Scraper
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.ufc_stats import UFCStatsScaper
from scrapers.ufc_official import UFCOfficialScraper
from scrapers.espn_mma import ESPNMMAScraper
from utils.rate_limiter import RateLimiter
from utils.database import DatabaseManager


async def example_basic_scraping():
    """Basic scraping example"""
    print("=== Basic Scraping Example ===")
    
    # Initialize rate limiter
    rate_limiter = RateLimiter(requests_per_second=1.0)
    
    # Initialize scrapers
    ufc_stats = UFCStatsScaper(rate_limiter)
    
    # Discover recent events
    print("Discovering recent events...")
    events = await ufc_stats.discover_events(mode="historical", since="2024-01-01")
    print(f"Found {len(events)} events")
    
    # Scrape first event
    if events:
        event = events[0]
        print(f"Scraping event: {event['name']}")
        
        event_data = await ufc_stats.scrape_event(event['id'])
        if event_data:
            print(f"Event: {event_data.event_name}")
            print(f"Date: {event_data.event_date}")
            print(f"Fights: {len(event_data.fights)}")
            
            # Show main event
            if event_data.fights:
                main_event = event_data.fights[0]  # bout_order 1
                print(f"Main Event: {main_event.fighter1.name} vs {main_event.fighter2.name}")


async def example_database_usage():
    """Database usage example"""
    print("\n=== Database Usage Example ===")
    
    # Initialize database
    db = DatabaseManager("example_ufc_data.db")
    db.create_tables()
    
    # Example event data (you would get this from scraping)
    from models.ufc_models import UFCEvent, Fight, Fighter, EventStatus
    
    event = UFCEvent(
        event_id="example-event",
        event_name="Example UFC Event",
        event_date="2024-12-31",
        venue="Example Arena",
        location="Example City, State",
        status=EventStatus.COMPLETED,
        fights=[
            Fight(
                bout_order=1,
                fighter1=Fighter(name="Fighter One", record="10-0-0"),
                fighter2=Fighter(name="Fighter Two", record="9-1-0"),
                weight_class="Lightweight",
                winner="Fighter One",
                method="KO/TKO (R1 2:45)"
            )
        ]
    )
    
    # Save to database
    success = db.save_event(event)
    print(f"Event saved to database: {success}")
    
    # Retrieve event
    retrieved_event = db.get_event("example-event")
    if retrieved_event:
        print(f"Retrieved event: {retrieved_event.event_name}")
        print(f"Fights: {len(retrieved_event.fights)}")
    
    # List events
    events = db.list_events(limit=5)
    print(f"Total events in database: {len(events)}")
    
    # Clean up
    db.close()


async def example_multiple_sources():
    """Example of using multiple scrapers"""
    print("\n=== Multiple Sources Example ===")
    
    rate_limiter = RateLimiter(requests_per_second=1.0)
    
    # Initialize all scrapers
    ufc_stats = UFCStatsScaper(rate_limiter)
    ufc_official = UFCOfficialScraper(rate_limiter)
    espn_mma = ESPNMMAScraper(rate_limiter)
    
    # Discover events from multiple sources
    print("Discovering events from multiple sources...")
    
    tasks = [
        ufc_stats.discover_events(mode="future"),
        ufc_official.discover_events(mode="future"),
        espn_mma.discover_events(mode="future")
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_events = []
    for i, result in enumerate(results):
        source_name = ["UFCStats", "UFC Official", "ESPN MMA"][i]
        if isinstance(result, Exception):
            print(f"{source_name}: Error - {result}")
        else:
            print(f"{source_name}: {len(result)} events")
            all_events.extend(result)
    
    print(f"Total events discovered: {len(all_events)}")
    
    # Deduplicate events (simple example)
    unique_events = {}
    for event in all_events:
        key = (event.get('date'), event.get('name', '').lower())
        if key not in unique_events:
            unique_events[key] = event
    
    print(f"Unique events after deduplication: {len(unique_events)}")


def example_data_analysis():
    """Example of analyzing scraped data"""
    print("\n=== Data Analysis Example ===")
    
    # Load data from JSON files
    data_dir = Path("data")
    if not data_dir.exists():
        print("No data directory found. Run scraper first.")
        return
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print("No JSON files found. Run scraper first.")
        return
    
    print(f"Found {len(json_files)} event files")
    
    # Analyze events
    total_fights = 0
    weight_classes = {}
    title_fights = 0
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            event_data = json.load(f)
        
        fights = event_data.get('fights', [])
        total_fights += len(fights)
        
        for fight in fights:
            # Count weight classes
            weight_class = fight.get('weight_class', 'Unknown')
            weight_classes[weight_class] = weight_classes.get(weight_class, 0) + 1
            
            # Count title fights
            if fight.get('title_fight') != 'none':
                title_fights += 1
    
    print(f"Total fights analyzed: {total_fights}")
    print(f"Title fights: {title_fights}")
    print(f"Most common weight classes:")
    
    for weight_class, count in sorted(weight_classes.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {weight_class}: {count} fights")


async def main():
    """Run all examples"""
    print("UFC Scraper Usage Examples")
    print("=" * 50)
    
    try:
        await example_basic_scraping()
        await example_database_usage()
        await example_multiple_sources()
        example_data_analysis()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())