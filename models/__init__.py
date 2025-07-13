"""
Models package for UFC scraper
"""

from .ufc_models import (
    UFCEvent,
    Fight,
    Fighter,
    FightStats,
    EventStatus,
    TitleFightType,
    FightResult,
    ScrapingResult
)

__all__ = [
    'UFCEvent',
    'Fight',
    'Fighter',
    'FightStats',
    'EventStatus',
    'TitleFightType',
    'FightResult',
    'ScrapingResult'
]