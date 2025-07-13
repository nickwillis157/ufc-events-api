# UFC Event and Fight Data Scraper

A comprehensive Python-based web scraper for UFC events and fight data from multiple sources. Supports both historical and upcoming events with rich fight details, polite rate-limiting, and fault-tolerance.

## Features

- **Multiple Data Sources**: Scrapes from UFCStats.com, UFC.com, and ESPN MMA API for redundancy
- **Rich Fight Data**: Captures fighter details, records, rankings, fight results, and statistics
- **Flexible Output**: Saves to clean JSON files and optionally to SQLite database
- **Rate Limiting**: Polite scraping with configurable rate limits (default: 2 requests/second)
- **Fault Tolerance**: Retry logic with exponential backoff for failed requests
- **CLI Interface**: Easy-to-use command-line interface with multiple options
- **Data Validation**: Pydantic models ensure data integrity and type safety

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd "UFC Scraper"
```

2. **Install Python dependencies:**
```bash
pip3 install -r requirements.txt
```

3. **Install Playwright browsers (if needed):**
```bash
playwright install
```

## 🌐 Web Dashboard

A beautiful, responsive web interface to view your scraped UFC data!

### **Quick Start Dashboard**
```bash
# Super easy - one command start
./start_dashboard.sh

# Or using Python directly
python3 run_dashboard.py
```

### **Dashboard Features**
- 🎨 **Beautiful dark theme** with UFC-style orange accents
- 📱 **Fully responsive** - works on desktop, tablet, mobile
- 🔍 **Search & filter** events by name, fighters, venue, year
- 🥊 **Rich event cards** with main event previews
- 🏆 **Title fight indicators** and championship highlighting
- 📊 **Detailed fight cards** in modal popups
- ⚡ **Real-time data** from your scraper + sample data

### **Manual Dashboard Setup**
```bash
# Start the web server
python3 web_server.py

# Open in browser
open http://localhost:8000
```

The dashboard automatically loads your scraped data or uses built-in sample data for demonstration.

## Usage

### Basic Usage

```bash
# Scrape all events (historical + upcoming)
python3 scrape_ufc.py --mode full

# Scrape only upcoming events
python3 scrape_ufc.py --mode future

# Scrape only historical events
python3 scrape_ufc.py --mode historical

# Scrape events since a specific date
python3 scrape_ufc.py --since 2020-01-01

# Scrape a specific event by ID
python3 scrape_ufc.py --event-id ufc-305
```

### Advanced Usage

```bash
# Enable database storage
python3 scrape_ufc.py --mode full --db

# Customize rate limiting (requests per second)
python3 scrape_ufc.py --mode full --rate-limit 1.5

# Specify output directory
python3 scrape_ufc.py --mode full --output-dir ./ufc_data

# Combine multiple options
python3 scrape_ufc.py --mode full --since 2023-01-01 --db --rate-limit 1.0
```

### CLI Options

- `--mode`: Scraping mode (`full`, `future`, `historical`)
- `--since`: Start date filter (YYYY-MM-DD format)
- `--event-id`: Specific event ID to scrape
- `--db`: Enable SQLite database storage
- `--rate-limit`: Requests per second (default: 2.0)
- `--output-dir`: Output directory for JSON files (default: `data`)

## Data Schema

The scraper captures the following data structure:

### Event Data
```json
{
  "event_id": "ufc-305",
  "event_name": "UFC 305: Du Plessis vs Adesanya",
  "event_date": "2025-08-10",
  "venue": "T-Mobile Arena",
  "location": "Las Vegas, NV",
  "status": "scheduled",
  "fights": [...],
  "scraped_at": "2025-01-15T10:30:00Z",
  "source_urls": {
    "ufcstats": "http://ufcstats.com/event-details/...",
    "ufc_official": "https://www.ufc.com/event/..."
  }
}
```

### Fight Data
```json
{
  "bout_order": 1,
  "fighter1": {
    "name": "Dricus du Plessis",
    "record": "22-2-0",
    "rank": 1,
    "country": "South Africa"
  },
  "fighter2": {
    "name": "Israel Adesanya",
    "record": "25-3-0",
    "rank": 2,
    "country": "Nigeria"
  },
  "weight_class": "Middleweight",
  "title_fight": "undisputed",
  "method": "KO/TKO (R2 4:15)",
  "winner": "Dricus du Plessis",
  "odds": {
    "f1_open": -135,
    "f2_open": +115,
    "f1_close": -150,
    "f2_close": +130
  }
}
```

## Data Sources

### UFCStats.com
- **Purpose**: Official UFC statistics and historical data
- **Coverage**: UFC 1 to present (completed events only)
- **Data Quality**: High - official statistics
- **Access**: Static HTML parsing

### UFC.com
- **Purpose**: Official UFC event listings and fight cards
- **Coverage**: Upcoming and recent events
- **Data Quality**: High - authoritative source
- **Access**: HTML parsing and JSON API

### ESPN MMA
- **Purpose**: Event details and fighter information
- **Coverage**: Current and upcoming events
- **Data Quality**: Good - comprehensive coverage
- **Access**: JSON API

## Database Schema

When using `--db` flag, data is stored in SQLite with the following tables:

### Events Table
- `event_id` (PRIMARY KEY)
- `event_name`
- `event_date`
- `venue`
- `location`
- `status`
- `scraped_at`
- `source_urls`

### Fights Table
- `id` (PRIMARY KEY)
- `event_id` (FOREIGN KEY)
- `bout_order`
- `fighter1_name`, `fighter2_name`
- `fighter1_record`, `fighter2_record`
- `weight_class`
- `title_fight`
- `method`
- `winner`
- `odds` (JSON)

## Rate Limiting and Ethics

This scraper implements polite crawling practices:

- **Default Rate Limit**: 2 requests per second
- **Configurable**: Adjust with `--rate-limit` option
- **Retry Logic**: Exponential backoff for failed requests
- **Respectful Headers**: Proper User-Agent strings
- **Error Handling**: Graceful handling of rate limits and errors

**Please respect the terms of service of all scraped websites.**

## Output Files

### JSON Files
- One file per event in the format: `{event_id}.json`
- Stored in `data/` directory (or specified `--output-dir`)
- Human-readable with proper formatting

### Database
- SQLite database: `ufc_data.db`
- Optimized for querying and analysis
- Includes indexes for performance

## Error Handling

The scraper includes comprehensive error handling:

- **Network Errors**: Retry with exponential backoff
- **Parsing Errors**: Log and continue with next item
- **Data Validation**: Pydantic models ensure data integrity
- **Rate Limiting**: Automatic backoff when rate limited

## Development

### Project Structure
```
UFC Scraper/
├── scrape_ufc.py          # Main CLI script
├── requirements.txt       # Python dependencies
├── models/
│   └── ufc_models.py     # Pydantic data models
├── scrapers/
│   ├── ufc_stats.py      # UFCStats.com scraper
│   ├── ufc_official.py   # UFC.com scraper
│   └── espn_mma.py       # ESPN MMA scraper
├── utils/
│   ├── rate_limiter.py   # Rate limiting utility
│   └── database.py       # Database management
└── data/                 # Output directory
```

### Adding New Scrapers
1. Create a new file in `scrapers/` directory
2. Implement the scraper class with required methods:
   - `discover_events()`
   - `scrape_event()`
3. Add to `scrapers/__init__.py`
4. Import in `scrape_ufc.py`

## Examples

### Scraping Recent Events
```bash
# Get all events from 2024
python scrape_ufc.py --mode full --since 2024-01-01 --db

# Get upcoming events only
python scrape_ufc.py --mode future --db
```

### Analyzing Data
```python
from utils.database import DatabaseManager

# Connect to database
db = DatabaseManager("ufc_data.db")

# Get fighter statistics
stats = db.get_fighter_stats("Conor McGregor")
print(f"Total fights: {stats['total_fights']}")
print(f"Wins: {stats['wins']}")

# List recent events
events = db.list_events(limit=10)
for event in events:
    print(f"{event['event_date']}: {event['event_name']}")
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**: Reduce `--rate-limit` value if getting blocked
2. **Network Errors**: Check internet connection and retry
3. **Import Errors**: Ensure all dependencies are installed
4. **Database Errors**: Check write permissions in output directory

### Debugging
```bash
# Run with verbose logging
python scrape_ufc.py --mode full --rate-limit 1.0 2>&1 | tee scraper.log
```

## License

This project is for educational and research purposes only. Please respect the terms of service of all scraped websites and use responsibly.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Disclaimer

This scraper is provided as-is for educational purposes. Users are responsible for complying with all applicable terms of service and legal requirements when using this software.