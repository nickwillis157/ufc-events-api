
import asyncio
import json
from pathlib import Path
from scrapers.wikipedia_ufc import WikipediaUFCScraper
from utils.rate_limiter import RateLimiter

async def scrape_and_save(event_id):
    """Scrapes a single event and saves it to a JSON file."""
    print(f"Scraping event: {event_id}...")
    rate_limiter = RateLimiter(requests_per_second=1.0)
    scraper = WikipediaUFCScraper(rate_limiter)
    
    event_data = await scraper.scrape_event(event_id)
    
    if event_data:
        # Use Pydantic's json() method which handles datetime correctly
        json_str = event_data.model_dump_json(indent=2)
        
        # Define the output path
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        file_path = data_dir / f"{event_id.replace(':', '')}.json"
        
        # Save the JSON string to a file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"✓ Successfully saved {file_path}")
    else:
        print(f"✗ Failed to scrape event: {event_id}")

async def main():
    # Scrape events from UFC 317 down to UFC 300
    for i in range(317, 299, -1):
        event_id = f"UFC_{i}"
        await scrape_and_save(event_id)

if __name__ == "__main__":
    asyncio.run(main())
