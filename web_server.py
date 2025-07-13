#!/usr/bin/env python3
"""
Simple web server to serve UFC data and static files
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

from models.ufc_models import UFCEvent


class UFCDataHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for serving UFC data and static files"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve from
        super().__init__(*args, directory=str(Path(__file__).parent / "web"), **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # API endpoints
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path)
        else:
            # Serve static files
            super().do_GET()
    
    def handle_api_request(self, parsed_path):
        """Handle API requests"""
        try:
            if parsed_path.path == '/api/events':
                self.serve_events_data()
            elif parsed_path.path == '/api/events/upcoming':
                self.serve_upcoming_events()
            elif parsed_path.path == '/api/events/recent':
                self.serve_recent_events()
            elif parsed_path.path.startswith('/api/events/'):
                # Get specific event
                event_id = parsed_path.path.split('/')[-1]
                self.serve_event_details(event_id)
            else:
                self.send_error(404, "API endpoint not found")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def serve_events_data(self):
        """Serve all events data"""
        events = self.load_all_events()
        self.send_json_response(events)
    
    def serve_upcoming_events(self):
        """Serve upcoming events only"""
        events = self.load_all_events()
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        upcoming = [e for e in events if datetime.strptime(e['event_date'], '%Y-%m-%d') >= today]
        upcoming.sort(key=lambda x: x['event_date'])
        self.send_json_response(upcoming)
    
    def serve_recent_events(self):
        """Serve recent completed events"""
        events = self.load_all_events()
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        recent = [e for e in events if datetime.strptime(e['event_date'], '%Y-%m-%d') < today]
        recent.sort(key=lambda x: x['event_date'], reverse=True)
        self.send_json_response(recent[:10])  # Last 10 events
    
    def serve_event_details(self, event_id):
        """Serve details for a specific event"""
        events = self.load_all_events()
        event = next((e for e in events if e['event_id'] == event_id), None)
        
        if event:
            self.send_json_response(event)
        else:
            self.send_error(404, f"Event {event_id} not found")
    
    def load_all_events(self) -> List[Dict]:
        """Load all events from JSON files"""
        data_dir = Path(__file__).parent / "data"
        events = []
        
        if not data_dir.exists():
            return []
        
        # Load all JSON files
        for json_file in data_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    event_data = json.load(f)
                    events.append(event_data)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        # Sort by date (newest first)
        events.sort(key=lambda x: x.get('event_date', ''), reverse=True)
        return events
    
    def send_json_response(self, data):
        """Send JSON response with proper headers"""
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(json_data.encode('utf-8')))
        self.end_headers()
        
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")


def create_sample_events():
    """Create sample event data if no data directory exists"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Check if we already have data
    if list(data_dir.glob("*.json")):
        return
    
    print("Creating sample event data...")
    
    # Sample events from the JavaScript code
    sample_events = [
        {
            "event_id": "ufc-305",
            "event_name": "UFC 305: Du Plessis vs Adesanya",
            "event_date": "2024-08-17",
            "venue": "RAC Arena",
            "location": "Perth, Australia",
            "status": "completed",
            "fights": [
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
                        "record": "24-3-0",
                        "rank": 2,
                        "country": "Nigeria"
                    },
                    "weight_class": "Middleweight Championship",
                    "title_fight": "undisputed",
                    "method": "Submission (R4 3:38)",
                    "winner": "Dricus du Plessis"
                }
            ],
            "scraped_at": datetime.now().isoformat(),
            "source_urls": {"sample": "generated"}
        },
        {
            "event_id": "ufc-311",
            "event_name": "UFC 311: Makhachev vs Moicano",
            "event_date": "2025-01-18",
            "venue": "Intuit Dome",
            "location": "Inglewood, CA",
            "status": "scheduled",
            "fights": [
                {
                    "bout_order": 1,
                    "fighter1": {
                        "name": "Islam Makhachev",
                        "record": "26-1-0",
                        "rank": 1,
                        "country": "Russia"
                    },
                    "fighter2": {
                        "name": "Renato Moicano",
                        "record": "19-5-1",
                        "rank": 4,
                        "country": "Brazil"
                    },
                    "weight_class": "Lightweight Championship",
                    "title_fight": "undisputed"
                }
            ],
            "scraped_at": datetime.now().isoformat(),
            "source_urls": {"sample": "generated"}
        }
    ]
    
    # Save sample events
    for event in sample_events:
        filename = f"{event['event_id']}.json"
        with open(data_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(event, f, indent=2, ensure_ascii=False)
    
    print(f"Created {len(sample_events)} sample events in {data_dir}")


def main():
    """Start the web server"""
    PORT = 8000
    
    # Create sample data if needed
    create_sample_events()
    
    # Start server
    with socketserver.TCPServer(("", PORT), UFCDataHandler) as httpd:
        print(f"🥊 UFC Events Dashboard Server")
        print(f"Server running at: http://localhost:{PORT}")
        print(f"API endpoints:")
        print(f"  - http://localhost:{PORT}/api/events")
        print(f"  - http://localhost:{PORT}/api/events/upcoming")
        print(f"  - http://localhost:{PORT}/api/events/recent")
        print(f"  - http://localhost:{PORT}/api/events/{{event_id}}")
        print(f"\nPress Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()


if __name__ == "__main__":
    main()