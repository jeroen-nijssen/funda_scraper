"""Funda.nl property scraper."""
import logging
from typing import Dict, List

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from config import Config


class FundaScraper(BaseScraper):
    """Scraper for Funda.nl property listings."""
    
    def get_site_name(self) -> str:
        return "Funda.nl"
    
    def build_url(self) -> str:
        """Build Funda search URL."""
        config = self.config.scraper_config
        return (f"https://www.funda.nl/koop/{config.location}/0-{config.max_price}/"
                f"1-dag/+{config.distance}km/")
    
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse Funda listings from HTML."""
        listings = []
        items = soup.find_all("div", class_="search-result-content")
        
        for item in items:
            try:
                # Extract street address
                street_elem = item.find("h2", class_="search-result__header-title fd-m-none")
                if not street_elem:
                    continue
                street = " ".join(street_elem.get_text().strip().split())
                
                # Extract city
                city_elem = item.find("h4", class_="search-result__header-subtitle fd-m-none")
                if not city_elem:
                    continue
                city = " ".join(city_elem.get_text().strip().split())
                
                # Extract price
                price_elem = item.find("span", class_="search-result-price")
                if not price_elem:
                    continue
                price = " ".join(price_elem.get_text().strip().split())
                
                # Extract URL
                link_elem = item.find('a', href=True)
                if not link_elem:
                    continue
                relative_url = link_elem.get('href')
                full_url = f"https://www.funda.nl{relative_url}"
                
                listings.append({
                    'street': street,
                    'city': city,
                    'price': price,
                    'url': full_url
                })
                
            except Exception as e:
                self.logger.warning(f"Error parsing listing: {e}")
                continue
        
        return listings


def main():
    """Main function to run Funda scraper."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('funda_scraper')
    
    config = Config()
    scraper = FundaScraper(config, logger)
    scraper.scrape()


if __name__ == "__main__":
    main()