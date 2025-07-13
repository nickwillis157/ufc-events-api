#!/usr/bin/env python3
"""
Simple test script to verify UFC Scraper functionality
"""

import asyncio
import json
import sys
from pathlib import Path

# Test imports
try:
    from models.ufc_models import UFCEvent, Fight, Fighter, EventStatus, TitleFightType
    from utils.rate_limiter import RateLimiter
    from utils.database import DatabaseManager
    from scrapers.ufc_stats import UFCStatsScaper
    from scrapers.ufc_official import UFCOfficialScraper
    from scrapers.espn_mma import ESPNMMAScraper
    from config import config
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_models():
    """Test pydantic models"""
    print("\n=== Testing Pydantic Models ===")
    
    try:
        # Test Fighter model
        fighter = Fighter(
            name="Test Fighter",
            record="10-2-0",
            rank=5,
            country="USA"
        )
        print(f"✓ Fighter model: {fighter.name}")
        
        # Test Fight model
        fight = Fight(
            bout_order=1,
            fighter1=fighter,
            fighter2=Fighter(name="Opponent", record="8-3-0"),
            weight_class="Lightweight",
            title_fight=TitleFightType.UNDISPUTED,
            method="KO/TKO (R2 3:45)",
            winner="Test Fighter"
        )
        print(f"✓ Fight model: {fight.fighter1.name} vs {fight.fighter2.name}")
        
        # Test UFCEvent model
        event = UFCEvent(
            event_id="test-event",
            event_name="Test UFC Event",
            event_date="2024-12-31",
            venue="Test Arena",
            location="Test City",
            status=EventStatus.COMPLETED,
            fights=[fight]
        )
        print(f"✓ UFCEvent model: {event.event_name}")
        
        # Test JSON serialization
        json_data = event.model_dump()
        json_str = json.dumps(json_data, indent=2, default=str)
        print(f"✓ JSON serialization: {len(json_str)} characters")
        
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False
    
    return True


async def test_rate_limiter():
    """Test rate limiter"""
    print("\n=== Testing Rate Limiter ===")
    
    try:
        import time
        
        rate_limiter = RateLimiter(requests_per_second=10.0)  # Fast for testing
        
        start_time = time.time()
        
        # Test async context
        async def test_async():
            await rate_limiter.wait()
            await rate_limiter.wait()
            await rate_limiter.wait()
        
        await test_async()
        
        elapsed = time.time() - start_time
        print(f"✓ Rate limiter: {elapsed:.2f} seconds for 3 requests")
        
    except Exception as e:
        print(f"✗ Rate limiter test failed: {e}")
        return False
    
    return True


def test_database():
    """Test database functionality"""
    print("\n=== Testing Database ===")
    
    try:
        # Use temporary database for testing
        db_path = "test_ufc_data.db"
        db = DatabaseManager(db_path)
        db.create_tables()
        print("✓ Database created and tables initialized")
        
        # Test event saving
        event = UFCEvent(
            event_id="test-db-event",
            event_name="Test Database Event",
            event_date="2024-01-01",
            venue="Test DB Arena",
            status=EventStatus.COMPLETED,
            fights=[
                Fight(
                    bout_order=1,
                    fighter1=Fighter(name="DB Fighter 1", record="5-0-0"),
                    fighter2=Fighter(name="DB Fighter 2", record="4-1-0"),
                    weight_class="Welterweight",
                    winner="DB Fighter 1"
                )
            ]
        )
        
        success = db.save_event(event)
        print(f"✓ Event saved: {success}")
        
        # Test event retrieval
        retrieved = db.get_event("test-db-event")
        if retrieved:
            print(f"✓ Event retrieved: {retrieved.event_name}")
        
        # Test event listing
        events = db.list_events(limit=5)
        print(f"✓ Events listed: {len(events)} found")
        
        # Cleanup
        db.close()
        Path(db_path).unlink(missing_ok=True)
        print("✓ Database cleanup completed")
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False
    
    return True


async def test_scrapers():
    """Test scraper initialization"""
    print("\n=== Testing Scrapers ===")
    
    try:
        rate_limiter = RateLimiter(requests_per_second=1.0)
        
        # Test UFCStats scraper
        ufc_stats = UFCStatsScaper(rate_limiter)
        print("✓ UFCStats scraper initialized")
        
        # Test UFC Official scraper
        ufc_official = UFCOfficialScraper(rate_limiter)
        print("✓ UFC Official scraper initialized")
        
        # Test ESPN MMA scraper
        espn_mma = ESPNMMAScraper(rate_limiter)
        print("✓ ESPN MMA scraper initialized")
        
        # Note: We don't test actual scraping to avoid hitting websites during testing
        
    except Exception as e:
        print(f"✗ Scraper test failed: {e}")
        return False
    
    return True


def test_config():
    """Test configuration"""
    print("\n=== Testing Configuration ===")
    
    try:
        print(f"✓ Config loaded: {config}")
        print(f"✓ Rate limit: {config.DEFAULT_RATE_LIMIT}")
        print(f"✓ Database path: {config.DEFAULT_DB_PATH}")
        print(f"✓ Output directory: {config.DEFAULT_OUTPUT_DIR}")
        
        # Test validation
        config.validate()
        print("✓ Configuration validation passed")
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False
    
    return True


def test_directory_structure():
    """Test project directory structure"""
    print("\n=== Testing Directory Structure ===")
    
    try:
        required_dirs = [
            "models",
            "scrapers", 
            "utils",
            "data"
        ]
        
        required_files = [
            "scrape_ufc.py",
            "requirements.txt",
            "README.md",
            "setup.py",
            "config.py"
        ]
        
        for directory in required_dirs:
            if Path(directory).exists():
                print(f"✓ Directory exists: {directory}")
            else:
                print(f"✗ Directory missing: {directory}")
                return False
        
        for file in required_files:
            if Path(file).exists():
                print(f"✓ File exists: {file}")
            else:
                print(f"✗ File missing: {file}")
                return False
        
    except Exception as e:
        print(f"✗ Directory structure test failed: {e}")
        return False
    
    return True


async def main():
    """Run all tests"""
    print("UFC Scraper Test Suite")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Configuration", test_config),
        ("Pydantic Models", test_models),
        ("Rate Limiter", test_rate_limiter),
        ("Database", test_database),
        ("Scrapers", test_scrapers),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! UFC Scraper is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)