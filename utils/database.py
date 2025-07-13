"""
Database management utilities for UFC scraper
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from models.ufc_models import UFCEvent, Fight, Fighter

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite database manager for UFC events and fights"""
    
    def __init__(self, db_path: str = "ufc_data.db"):
        self.db_path = Path(db_path)
        self.connection = None
        self.connect()
    
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def create_tables(self):
        """Create database tables"""
        try:
            cursor = self.connection.cursor()
            
            # Events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    venue TEXT,
                    location TEXT,
                    status TEXT NOT NULL,
                    attendance INTEGER,
                    gate TEXT,
                    tv_broadcast TEXT,
                    start_time TEXT,
                    scraped_at TEXT NOT NULL,
                    source_urls TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Fights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    bout_order INTEGER NOT NULL,
                    fighter1_name TEXT NOT NULL,
                    fighter2_name TEXT NOT NULL,
                    fighter1_record TEXT,
                    fighter2_record TEXT,
                    fighter1_rank INTEGER,
                    fighter2_rank INTEGER,
                    fighter1_country TEXT,
                    fighter2_country TEXT,
                    weight_class TEXT NOT NULL,
                    title_fight TEXT NOT NULL,
                    method TEXT,
                    round INTEGER,
                    time TEXT,
                    winner TEXT,
                    result TEXT,
                    referee TEXT,
                    bonuses TEXT,
                    odds TEXT,
                    stats TEXT,
                    fight_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id),
                    UNIQUE(event_id, bout_order)
                )
            """)
            
            # Indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fights_event ON fights(event_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fights_fighter1 ON fights(fighter1_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fights_fighter2 ON fights(fighter2_name)")
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def save_event(self, event: UFCEvent) -> bool:
        """Save event and its fights to database"""
        try:
            cursor = self.connection.cursor()
            
            # Insert/update event
            cursor.execute("""
                INSERT OR REPLACE INTO events (
                    event_id, event_name, event_date, venue, location, status,
                    attendance, gate, tv_broadcast, start_time, scraped_at, source_urls
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.event_name,
                event.event_date,
                event.venue,
                event.location,
                event.status.value,
                event.attendance,
                event.gate,
                event.tv_broadcast,
                event.start_time,
                event.scraped_at.isoformat(),
                json.dumps(event.source_urls)
            ))
            
            # Delete existing fights for this event
            cursor.execute("DELETE FROM fights WHERE event_id = ?", (event.event_id,))
            
            # Insert fights
            for fight in event.fights:
                cursor.execute("""
                    INSERT INTO fights (
                        event_id, bout_order, fighter1_name, fighter2_name,
                        fighter1_record, fighter2_record, fighter1_rank, fighter2_rank,
                        fighter1_country, fighter2_country, weight_class, title_fight,
                        method, round, time, winner, result, referee, bonuses,
                        odds, stats, fight_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    fight.bout_order,
                    fight.fighter1.name,
                    fight.fighter2.name,
                    fight.fighter1.record,
                    fight.fighter2.record,
                    fight.fighter1.rank,
                    fight.fighter2.rank,
                    fight.fighter1.country,
                    fight.fighter2.country,
                    fight.weight_class,
                    fight.title_fight.value,
                    fight.method,
                    fight.round,
                    fight.time,
                    fight.winner,
                    fight.result.value if fight.result else None,
                    fight.referee,
                    json.dumps(fight.bonuses) if fight.bonuses else None,
                    fight.odds.model_dump_json() if fight.odds else None,
                    fight.stats.model_dump_json() if fight.stats else None,
                    fight.fight_url
                ))
            
            self.connection.commit()
            logger.info(f"Saved event {event.event_id} with {len(event.fights)} fights")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save event {event.event_id}: {e}")
            self.connection.rollback()
            return False
    
    def get_event(self, event_id: str) -> Optional[UFCEvent]:
        """Retrieve event from database"""
        try:
            cursor = self.connection.cursor()
            
            # Get event
            cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
            event_row = cursor.fetchone()
            
            if not event_row:
                return None
            
            # Get fights
            cursor.execute("""
                SELECT * FROM fights WHERE event_id = ? ORDER BY bout_order
            """, (event_id,))
            fight_rows = cursor.fetchall()
            
            # Build event object
            fights = []
            for fight_row in fight_rows:
                fighter1 = Fighter(
                    name=fight_row['fighter1_name'],
                    record=fight_row['fighter1_record'],
                    rank=fight_row['fighter1_rank'],
                    country=fight_row['fighter1_country']
                )
                
                fighter2 = Fighter(
                    name=fight_row['fighter2_name'],
                    record=fight_row['fighter2_record'],
                    rank=fight_row['fighter2_rank'],
                    country=fight_row['fighter2_country']
                )
                
                fight = Fight(
                    bout_order=fight_row['bout_order'],
                    fighter1=fighter1,
                    fighter2=fighter2,
                    weight_class=fight_row['weight_class'],
                    title_fight=fight_row['title_fight'],
                    method=fight_row['method'],
                    round=fight_row['round'],
                    time=fight_row['time'],
                    winner=fight_row['winner'],
                    referee=fight_row['referee'],
                    fight_url=fight_row['fight_url']
                )
                
                fights.append(fight)
            
            event = UFCEvent(
                event_id=event_row['event_id'],
                event_name=event_row['event_name'],
                event_date=event_row['event_date'],
                venue=event_row['venue'],
                location=event_row['location'],
                status=event_row['status'],
                attendance=event_row['attendance'],
                gate=event_row['gate'],
                tv_broadcast=event_row['tv_broadcast'],
                start_time=event_row['start_time'],
                fights=fights,
                scraped_at=datetime.fromisoformat(event_row['scraped_at']),
                source_urls=json.loads(event_row['source_urls']) if event_row['source_urls'] else {}
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Failed to retrieve event {event_id}: {e}")
            return None
    
    def list_events(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List events from database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT event_id, event_name, event_date, venue, location, status
                FROM events
                ORDER BY event_date DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            return []
    
    def get_fighter_stats(self, fighter_name: str) -> Dict:
        """Get fighter statistics from database"""
        try:
            cursor = self.connection.cursor()
            
            # Get fights where fighter participated
            cursor.execute("""
                SELECT * FROM fights
                WHERE fighter1_name = ? OR fighter2_name = ?
                ORDER BY (SELECT event_date FROM events WHERE events.event_id = fights.event_id) DESC
            """, (fighter_name, fighter_name))
            
            fights = cursor.fetchall()
            
            stats = {
                'total_fights': len(fights),
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'fights': []
            }
            
            for fight in fights:
                fight_dict = dict(fight)
                stats['fights'].append(fight_dict)
                
                # Count wins/losses
                if fight['winner'] == fighter_name:
                    stats['wins'] += 1
                elif fight['winner'] and fight['winner'] != fighter_name:
                    stats['losses'] += 1
                
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get fighter stats for {fighter_name}: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()