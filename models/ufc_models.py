"""
Pydantic models for UFC event and fight data
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class EventStatus(str, Enum):
    """Event status enumeration"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"


class TitleFightType(str, Enum):
    """Title fight type enumeration"""
    UNDISPUTED = "undisputed"
    INTERIM = "interim"
    NONE = "none"


class FightResult(str, Enum):
    """Fight result enumeration"""
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"
    NC = "no_contest"


class Fighter(BaseModel):
    """Individual fighter model"""
    name: str = Field(..., min_length=1, description="Fighter's full name")
    record: Optional[str] = Field(None, description="Win-Loss-Draw record (e.g., '22-2-0')")
    rank: Optional[int] = Field(None, ge=1, le=15, description="Current ranking in division")
    country: Optional[str] = Field(None, description="Fighter's country")
    age: Optional[int] = Field(None, ge=18, le=60, description="Fighter's age")
    height: Optional[str] = Field(None, description="Fighter's height")
    weight: Optional[str] = Field(None, description="Fighter's weight")
    reach: Optional[str] = Field(None, description="Fighter's reach")
    stance: Optional[str] = Field(None, description="Fighting stance (Orthodox, Southpaw, etc.)")
    nickname: Optional[str] = Field(None, description="Fighter's nickname")
    bonus: Optional[str] = Field(None, description="Performance bonus (e.g., 'Fight of the Night')")
    
    @validator('record')
    def validate_record(cls, v):
        if v and not v.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').replace('NC', '').isdigit():
            # Allow format like "22-2-0", "22-2-0 (1 NC)", etc.
            pass
        return v





class FightStats(BaseModel):
    """Detailed fight statistics"""
    total_strikes_f1: Optional[int] = Field(None, ge=0)
    total_strikes_f2: Optional[int] = Field(None, ge=0)
    significant_strikes_f1: Optional[int] = Field(None, ge=0)
    significant_strikes_f2: Optional[int] = Field(None, ge=0)
    takedowns_f1: Optional[int] = Field(None, ge=0)
    takedowns_f2: Optional[int] = Field(None, ge=0)
    submissions_f1: Optional[int] = Field(None, ge=0)
    submissions_f2: Optional[int] = Field(None, ge=0)
    control_time_f1: Optional[str] = Field(None, description="Control time in MM:SS format")
    control_time_f2: Optional[str] = Field(None, description="Control time in MM:SS format")


class Fight(BaseModel):
    """Individual fight/bout model"""
    bout_order: int = Field(..., ge=1, description="Fight order on card (1=main event)")
    fighter1: Fighter = Field(..., description="First fighter")
    fighter2: Fighter = Field(..., description="Second fighter")
    weight_class: str = Field(..., min_length=1, description="Weight class")
    title_fight: TitleFightType = Field(TitleFightType.NONE, description="Title fight type")
    
    # Fight result (populated after event)
    method: Optional[str] = Field(None, description="Fight finish method")
    round: Optional[int] = Field(None, ge=1, le=5, description="Round fight ended")
    time: Optional[str] = Field(None, description="Time in round (MM:SS)")
    winner: Optional[str] = Field(None, description="Winner's name")
    result: Optional[FightResult] = Field(None, description="Fight result")
    
    # Additional data
    stats: Optional[FightStats] = Field(None, description="Fight statistics")
    referee: Optional[str] = Field(None, description="Referee name")
    bonuses: Optional[List[str]] = Field(None, description="Performance bonuses")
    
    # Metadata
    fight_url: Optional[str] = Field(None, description="Source URL for fight details")
    segment: Optional[str] = Field(None, description="Broadcast segment (main-card, prelims, early-prelims)")
    
    @validator('bout_order')
    def validate_bout_order(cls, v):
        if v < 1:
            raise ValueError('bout_order must be at least 1')
        return v


class UFCEvent(BaseModel):
    """UFC Event model"""
    event_id: str = Field(..., min_length=1, description="Unique event identifier")
    event_name: str = Field(..., min_length=1, description="Full event name")
    event_date: str = Field(..., description="Event date (YYYY-MM-DD)")
    venue: Optional[str] = Field(None, description="Venue name and location")
    location: Optional[str] = Field(None, description="City, State/Country")
    status: EventStatus = Field(EventStatus.SCHEDULED, description="Event status")
    
    # Event details
    attendance: Optional[int] = Field(None, ge=0, description="Attendance count")
    gate: Optional[str] = Field(None, description="Gate revenue")
    tv_broadcast: Optional[str] = Field(None, description="TV broadcast info")
    start_time: Optional[str] = Field(None, description="Event start time")
    
    # Fights
    fights: List[Fight] = Field(default_factory=list, description="List of fights on card")
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.now, description="Scrape timestamp")
    source_urls: Dict[str, str] = Field(default_factory=dict, description="Source URLs by scraper")
    
    @validator('event_date')
    def validate_event_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('event_date must be in YYYY-MM-DD format')
        return v
    
    @validator('fights')
    def validate_fights_order(cls, v):
        if v:
            bout_orders = [fight.bout_order for fight in v]
            if len(bout_orders) != len(set(bout_orders)):
                raise ValueError('All fights must have unique bout_order values')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScrapingResult(BaseModel):
    """Result of a scraping operation"""
    success: bool = Field(..., description="Whether scraping was successful")
    events: List[UFCEvent] = Field(default_factory=list, description="Scraped events")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Scrape timestamp")
    source: str = Field(..., description="Scraper source")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }