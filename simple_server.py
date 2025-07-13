#!/usr/bin/env python3
"""
Simple HTTP server for UFC data - simplified version
"""
import json
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

class UFCHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        # Handle API requests
        if path == '/api/events':
            self.serve_all_events()
        else:
            self.send_error(404)
    
    def serve_all_events(self):
        """Load and serve all UFC events from data directory"""
        data_dir = Path(__file__).parent / "data"
        events = []
        
        # Load all JSON files
        for json_file in sorted(data_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    event = json.load(f)
                    events.append(event)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        # Send JSON response
        response = json.dumps(events, indent=2)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f"[SERVER] {format % args}")

if __name__ == '__main__':
    PORT = 8000
    server = HTTPServer(('localhost', PORT), UFCHandler)
    print(f"🥊 UFC API Server running at http://localhost:{PORT}")
    print(f"📡 API endpoint: http://localhost:{PORT}/api/events")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()