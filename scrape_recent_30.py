#!/usr/bin/env python3
"""
Script to scrape the 30 most recent UFC events
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# List of 30 most recent events based on file modification times
RECENT_EVENTS = [
    "UFC on ESPN: Lewis vs. Teixeira",
    "UFC 317", 
    "UFC on ABC: Hill vs. Rountree Jr.",
    "UFC on ESPN: Usman vs. Buckley",
    "UFC 316",
    "UFC on ESPN: Gamrot vs. Klein", 
    "UFC 315",
    "UFC on ESPN: Sandhagen vs. Figueiredo",
    "UFC on ESPN: Machado Garry vs. Prates",
    "UFC 314",
    "UFC on ESPN: Emmett vs. Murphy",
    "UFC on ESPN: Moreno vs. Erceg",
    "UFC Fight Night: Edwards vs. Brady",
    "UFC Fight Night: Vettori vs. Dolidze 2", 
    "UFC 313",
    "UFC Fight Night: Kape vs. Almabayev",
    "UFC Fight Night: Cejudo vs. Song",
    "UFC Fight Night: Cannonier vs. Rodrigues",
    "UFC 312",
    "UFC Fight Night: Adesanya vs. Imavov",
    "UFC 311",
    "UFC Fight Night: Dern vs. Ribas 2",
    "UFC on ESPN: Covington vs. Buckley",
    "UFC 310",
    "UFC Fight Night: Yan vs. Figueiredo",
    "UFC 309",
    "UFC Fight Night: Magny vs. Prates",
    "UFC Fight Night: Moreno vs. Albazi", 
    "UFC 308",
    "UFC Fight Night: Hernandez vs. Pereira"
]

async def scrape_event(event_id):
    """Scrape a single event"""
    try:
        print(f"Scraping: {event_id}")
        result = subprocess.run([
            sys.executable, "scrape_ufc.py", 
            "--event-id", event_id,
            "--rate-limit", "1.0"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"✓ Successfully scraped: {event_id}")
            return True
        else:
            print(f"✗ Failed to scrape: {event_id}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Exception scraping {event_id}: {e}")
        return False

async def main():
    """Main scraping function"""
    print(f"Starting to scrape {len(RECENT_EVENTS)} recent UFC events...")
    
    successful = 0
    failed = 0
    
    for event_id in RECENT_EVENTS:
        success = await scrape_event(event_id)
        if success:
            successful += 1
        else:
            failed += 1
        
        # Add a small delay between requests
        await asyncio.sleep(1)
    
    print(f"\nScraping complete!")
    print(f"✓ Successfully scraped: {successful} events")
    print(f"✗ Failed to scrape: {failed} events")

if __name__ == "__main__":
    asyncio.run(main())