"""
Configuration settings for UFC Scraper
"""

import os
from pathlib import Path


class Config:
    """Configuration class for UFC Scraper"""
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 2.0  # requests per second
    MAX_RATE_LIMIT = 5.0      # maximum allowed rate
    MIN_RATE_LIMIT = 0.1      # minimum allowed rate
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2
    RETRY_MIN_WAIT = 1
    RETRY_MAX_WAIT = 10
    
    # Request settings
    REQUEST_TIMEOUT = 30
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    # Database settings
    DEFAULT_DB_PATH = "ufc_data.db"
    DB_TIMEOUT = 30
    
    # Output settings
    DEFAULT_OUTPUT_DIR = "data"
    JSON_INDENT = 2
    JSON_ENSURE_ASCII = False
    
    # Scraper URLs
    UFCSTATS_BASE_URL = "http://ufcstats.com"
    UFCSTATS_EVENTS_URL = f"{UFCSTATS_BASE_URL}/statistics/events/completed"
    
    UFC_OFFICIAL_BASE_URL = "https://www.ufc.com"
    UFC_OFFICIAL_API_URL = f"{UFC_OFFICIAL_BASE_URL}/api/v3/events"
    
    ESPN_MMA_BASE_URL = "https://site.web.api.espn.com/apis/v2/sports/mma/ufc"
    ESPN_MMA_EVENTS_URL = f"{ESPN_MMA_BASE_URL}/events"
    
    BEST_FIGHT_ODDS_BASE_URL = "https://www.bestfightodds.com"
    
    # Date formats
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Fuzzy matching thresholds
    EVENT_NAME_SIMILARITY_THRESHOLD = 80
    FIGHTER_NAME_SIMILARITY_THRESHOLD = 85
    
    # Pagination limits
    MAX_EVENTS_PER_REQUEST = 50
    MAX_PAGES_TO_SCRAPE = 100
    
    # Environment variable overrides
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        config = cls()
        
        # Rate limiting
        if os.getenv('UFC_SCRAPER_RATE_LIMIT'):
            config.DEFAULT_RATE_LIMIT = float(os.getenv('UFC_SCRAPER_RATE_LIMIT'))
        
        # Database
        if os.getenv('UFC_SCRAPER_DB_PATH'):
            config.DEFAULT_DB_PATH = os.getenv('UFC_SCRAPER_DB_PATH')
        
        # Output directory
        if os.getenv('UFC_SCRAPER_OUTPUT_DIR'):
            config.DEFAULT_OUTPUT_DIR = os.getenv('UFC_SCRAPER_OUTPUT_DIR')
        
        # Logging
        if os.getenv('UFC_SCRAPER_LOG_LEVEL'):
            config.LOG_LEVEL = os.getenv('UFC_SCRAPER_LOG_LEVEL')
        
        return config
    
    def validate(self):
        """Validate configuration settings"""
        if not (self.MIN_RATE_LIMIT <= self.DEFAULT_RATE_LIMIT <= self.MAX_RATE_LIMIT):
            raise ValueError(f"Rate limit must be between {self.MIN_RATE_LIMIT} and {self.MAX_RATE_LIMIT}")
        
        if self.MAX_RETRIES < 1:
            raise ValueError("MAX_RETRIES must be at least 1")
        
        if self.REQUEST_TIMEOUT < 1:
            raise ValueError("REQUEST_TIMEOUT must be at least 1 second")
        
        # Ensure output directory exists
        Path(self.DEFAULT_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    def __repr__(self):
        return f"Config(rate_limit={self.DEFAULT_RATE_LIMIT}, db_path='{self.DEFAULT_DB_PATH}')"


# Global configuration instance
config = Config.from_env()
config.validate()