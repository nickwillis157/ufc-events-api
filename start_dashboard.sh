#!/bin/bash

echo "🥊 UFC Events Dashboard Launcher"
echo "================================="

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 is not installed. Please install Python 3."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "scrape_ufc.py" ]; then
    echo "❌ Please run this script from the UFC Scraper directory"
    exit 1
fi

echo "🚀 Starting UFC Dashboard..."
echo "Dashboard will open at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the web server
python3 web_server.py