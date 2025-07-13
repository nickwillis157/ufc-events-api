#!/usr/bin/env python3
"""
Easy setup and run script for UFC Dashboard
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import requests
        import bs4
        import pydantic
        import click
        print("✅ All required dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False


def run_scraper_sample():
    """Run the scraper to get some sample data"""
    print("🥊 Running UFC scraper to get sample data...")
    
    try:
        # Run a quick scrape for recent events
        result = subprocess.run([
            "python3", "scrape_ufc.py", 
            "--mode", "historical", 
            "--since", "2024-01-01",
            "--rate-limit", "1.0"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Sample data collected successfully")
        else:
            print("⚠️  Scraper had issues, but dashboard will still work with sample data")
            print(f"Scraper output: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("⚠️  Scraper timed out, using built-in sample data")
    except Exception as e:
        print(f"⚠️  Could not run scraper: {e}")
        print("Dashboard will use built-in sample data")


def start_server():
    """Start the web server"""
    print("🚀 Starting UFC Dashboard server...")
    
    try:
        # Start the server
        subprocess.run(["python3", "web_server.py"])
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")


def open_browser():
    """Open the dashboard in the default browser"""
    print("🌐 Opening dashboard in browser...")
    time.sleep(2)  # Give server time to start
    
    try:
        webbrowser.open("http://localhost:8000")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print("Please open http://localhost:8000 in your browser")


def main():
    """Main setup and run function"""
    print("=" * 50)
    print("🥊 UFC Events Dashboard Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("scrape_ufc.py").exists():
        print("❌ Please run this script from the UFC Scraper directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n📦 To install dependencies, run:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n🎯 Setup Options:")
    print("1. Quick start with sample data (recommended)")
    print("2. Scrape fresh data then start dashboard")
    print("3. Just start the dashboard")
    
    try:
        choice = input("\nChoose an option (1-3): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled")
        sys.exit(0)
    
    if choice == "1":
        print("\n🚀 Starting dashboard with sample data...")
        # Open browser in background
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start server (this will block)
        start_server()
    
    elif choice == "2":
        print("\n📡 Collecting fresh UFC data...")
        run_scraper_sample()
        
        print("\n🚀 Starting dashboard...")
        # Open browser in background
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start server (this will block)
        start_server()
    
    elif choice == "3":
        print("\n🚀 Starting dashboard...")
        # Open browser in background
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start server (this will block)
        start_server()
    
    else:
        print("❌ Invalid choice. Please run the script again.")
        sys.exit(1)


if __name__ == "__main__":
    main()