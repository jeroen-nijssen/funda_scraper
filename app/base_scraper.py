"""Base scraper class with common functionality."""
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from config import Config


class BaseScraper(ABC):
    """Base class for all property scrapers."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        
    def get_headers(self) -> Dict[str, str]:
        """Get random user agent headers."""
        return {
            'User-Agent': random.choice(self.config.user_agents)
        }
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=self.get_headers(), timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"All request attempts failed for {url}")
                    return None
    
    def check_existing_task(self, title: str) -> Tuple[bool, str]:
        """Check if task already exists in Kanban board."""
        try:
            body = {
                "jsonrpc": "2.0",
                "method": "getAllTasks",
                "id": 133280317,
                "params": {
                    "project_id": self.config.kanban_config.project_id,
                    "status_id": 1
                }
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Use username/password authentication
            auth = (self.config.kanban_config.username, self.config.kanban_config.password)
            
            response = self.session.post(
                self.config.kanban_config.base_url,
                headers=headers,
                json=body,
                auth=auth,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                for task in data.get('result', []):
                    if task.get('title') == title:
                        return True, task.get('url', 'not existing')
                        
            return False, 'not existing'
            
        except Exception as e:
            self.logger.error(f"Error checking existing task: {e}")
            return False, 'not existing'
    
    def create_kanban_task(self, title: str, description: str) -> bool:
        """Create new task in Kanban board."""
        try:
            body = {
                "jsonrpc": "2.0",
                "method": "createTask",
                "params": {
                    "owner_id": self.config.kanban_config.owner_id,
                    "creator_id": self.config.kanban_config.creator_id,
                    "description": description,
                    "title": title,
                    "project_id": self.config.kanban_config.project_id
                }
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Use username/password authentication
            auth = (self.config.kanban_config.username, self.config.kanban_config.password)
            
            response = self.session.post(
                self.config.kanban_config.base_url,
                headers=headers,
                json=body,
                auth=auth,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error creating Kanban task: {e}")
            return False
    
    def process_listing(self, street: str, city: str, price: str, url: str) -> None:
        """Process a single listing."""
        title = f"{street} - {city}"
        description = f"{street} - {city}\n\n{price}\n\n\n{url}"
        
        exists, existing_url = self.check_existing_task(title)
        
        if not exists:
            self.logger.info(f"Found new listing on {self.get_site_name()}")
            self.logger.info(f"\t{street}")
            self.logger.info(f"\t{city}")
            self.logger.info(f"\t{price}")
            self.logger.info(f"\t{url}")
            
            if self.create_kanban_task(title, description):
                self.logger.info("Successfully created Kanban task")
            else:
                self.logger.error("Failed to create Kanban task")
        else:
            self.logger.info(f"Found existing listing on {self.get_site_name()}")
            self.logger.info(f"\tListing already on the board, URL: {existing_url}")
    
    @abstractmethod
    def get_site_name(self) -> str:
        """Get the name of the site being scraped."""
        pass
    
    @abstractmethod
    def build_url(self) -> str:
        """Build the search URL for the site."""
        pass
    
    @abstractmethod
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse listings from the soup object."""
        pass
    
    def scrape(self) -> None:
        """Main scraping method."""
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        
        self.logger.info("##################################")
        self.logger.info(f"Execution running at: {dt_string}")
        
        url = self.build_url()
        self.logger.info(f"Requesting data from: {url}")
        
        response = self.make_request(url)
        if not response:
            self.logger.error("Failed to fetch data")
            return
        
        soup = BeautifulSoup(response.content, "html.parser")
        listings = self.parse_listings(soup)
        
        if not listings:
            self.logger.warning("No listings found")
            return
        
        for listing in listings:
            try:
                self.process_listing(
                    listing['street'],
                    listing['city'],
                    listing['price'],
                    listing['url']
                )
            except Exception as e:
                self.logger.error(f"Error processing listing: {e}")
                continue
        
        self.logger.info("##################################")