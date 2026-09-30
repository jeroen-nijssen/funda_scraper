"""Configuration management for the funda scraper."""
import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ScraperConfig:
    """Configuration for individual scrapers."""
    location: str
    distance: int
    max_price: int
    min_rooms: int = 5
    min_area: int = 100


@dataclass
class KanbanConfig:
    """Configuration for Kanban board integration."""
    base_url: str
    username: str
    password: str
    project_id: int = 1
    owner_id: int = 1
    creator_id: int = 1


class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.scraper_config = ScraperConfig(
            location=os.getenv('LOCATION', 'gemeente-amsterdam'),
            distance=int(os.getenv('DISTANCE', '5')),
            max_price=int(os.getenv('MAX_PRICE', '450000')),
            min_rooms=int(os.getenv('MIN_ROOMS', '5')),
            min_area=int(os.getenv('MIN_AREA', '100'))
        )
        
        self.kanban_config = KanbanConfig(
            base_url=os.getenv('KANBAN_URL', 'http://kanboard/jsonrpc.php'),
            username=os.getenv('KANBAN_USERNAME', 'admin'),
            password=os.getenv('KANBAN_PASSWORD', 'admin'),
            project_id=int(os.getenv('KANBAN_PROJECT_ID', '1')),
            owner_id=int(os.getenv('KANBAN_OWNER_ID', '1')),
            creator_id=int(os.getenv('KANBAN_CREATOR_ID', '1'))
        )
        
        self.sleep_intervals = {
            'funda': int(os.getenv('FUNDA_SLEEP', '3600')),  # 1 hour
            'pararius': int(os.getenv('PARARIUS_SLEEP', '1800')),  # 30 minutes
            'jaap': int(os.getenv('JAAP_SLEEP', '3600'))  # 1 hour
        }
        
        self.log_dir = os.getenv('LOG_DIR', '/app/log')
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]