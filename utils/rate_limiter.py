"""
Rate limiter utility for polite web scraping
"""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """Simple rate limiter for HTTP requests"""
    
    def __init__(self, requests_per_second: float = 2.0):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: Optional[float] = None
    
    async def wait(self):
        """Wait if necessary to respect rate limit"""
        current_time = time.time()
        
        if self.last_request_time is not None:
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def set_rate(self, requests_per_second: float):
        """Update the rate limit"""
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second