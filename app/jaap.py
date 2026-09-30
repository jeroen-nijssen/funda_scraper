"""Jaap.nl property scraper."""
import logging
import re
from typing import Dict, List

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from config import Config


class JaapScraper(BaseScraper):
    """Scraper for Jaap.nl property listings."""
    
    def get_site_name(self) -> str:
        return "Jaap.nl"
    
    def build_url(self) -> str:
        """Build Jaap search URL."""
        config = self.config.scraper_config
        # Convert gemeente-amsterdam to roermond for Jaap
        location = config.location.replace('gemeente-', '')
        return (f"https://www.jaap.nl/koophuizen/limburg/midden-limburg/{location}/"
                f"+{config.distance}km/0-{config.max_price}/woonhuis/"
                f"{config.min_area}+-woonopp/{config.min_rooms}+kamers/sort4")
    
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse Jaap listings from HTML."""
        listings = []
        items = soup.find_all("div", id=re.compile('^house_result_'))

        
        for item in items:
            try:
                # Extract street address
                street_elem = item.find("h2", class_="property-address-street")
                if not street_elem:
                    continue
                street = " ".join(street_elem.get_text().strip().split())
                
                # Extract city
                city_elem = item.find("div", class_="property-address-zipcity")
                if not city_elem:
                    continue
                city = " ".join(city_elem.get_text().strip().replace(",", "").split())
                
                # Extract price
                price_elem = item.find("div", class_="property-price")
                if not price_elem:
                    continue
                price = " ".join(price_elem.get_text().strip().split())
                
                # Extract URL
                link_elem = item.find('a', href=True)
                if not link_elem:
                    continue
                url = link_elem.get('href').split("?")[0]
                
                listings.append({
                    'street': street,
                    'city': city,
                    'price': price,
                    'url': url
                })
                
            except Exception as e:
                self.logger.warning(f"Error parsing listing: {e}")
                continue
        
        return listings


def main():
    """Main function to run Jaap scraper."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('jaap_scraper')
    
    config = Config()
    scraper = JaapScraper(config, logger)
    scraper.scrape()


if __name__ == "__main__":
    main()