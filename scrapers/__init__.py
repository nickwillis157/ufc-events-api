"""
Scrapers package for UFC scraper
"""

from .ufc_stats import UFCStatsScaper
from .ufc_official import UFCOfficialScraper
from .espn_mma import ESPNMMAScraper
from .wikipedia_ufc import WikipediaUFCScraper

__all__ = ['UFCStatsScaper', 'UFCOfficialScraper', 'ESPNMMAScraper', 'WikipediaUFCScraper']