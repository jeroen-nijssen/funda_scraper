"""Huispedia.nl property scraper.

Replaces the old Jaap.nl scraper: Jaap.nl was shut down by its owner
Mediahuis in January 2024, and its listings were absorbed into Huispedia.
Unlike the other scrapers, listing data isn't scraped from rendered HTML -
Huispedia's search page is an Inertia.js (Laravel + Vue) app that embeds the
full result set as JSON in the `data-page` attribute of `<div id="app">`, so
it can be parsed directly with no CSS selectors involved.
"""
import json
import logging

from base_scraper import BaseScraper
from bs4 import BeautifulSoup
from config import Config


class HuispediaScraper(BaseScraper):
    """Scraper for Huispedia.nl property listings."""

    def get_site_name(self) -> str:
        return "Huispedia.nl"

    def build_url(self) -> str:
        """Build Huispedia search URL."""
        config = self.config.scraper_config
        # /woonhuis restricts server-side to houses, matching what Funda/Jaap
        # searched for. No server-side price/room/area filter was found, so
        # those are applied client-side in parse_listings.
        return f"https://www.huispedia.nl/koopwoningen/{config.municipality}/woonhuis"

    def parse_listings(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """Parse Huispedia listings from the embedded Inertia JSON payload."""
        listings = []
        config = self.config.scraper_config

        app_elem = soup.find("div", id="app")
        if not app_elem or not app_elem.get('data-page'):
            return listings

        try:
            page_data = json.loads(app_elem['data-page'])
            properties = page_data['props']['searchData']['properties']
        except (KeyError, ValueError) as e:
            self.logger.warning(f"Error parsing Huispedia page data: {e}")
            return listings

        for prop in properties:
            try:
                rooms = prop.get('aantal_kamers') or 0
                area = prop.get('woonoppervlakte') or 0
                price = prop.get('price_sale') or prop.get('price_search') or 0

                if rooms < config.min_rooms or area < config.min_area or price > config.max_price:
                    continue

                street = f"{prop['street']} {prop['hnumchar']}"
                city = f"{prop['postcode']} {prop['city_name']}"
                formatted_price = f"€ {price:,}".replace(',', '.') + " k.k."
                url = (f"https://www.huispedia.nl/{prop['city_slug']}/"
                       f"{prop['postcode'].lower().replace(' ', '')}/"
                       f"{prop['street_slug']}/{prop['hnum']}")

                listings.append({
                    'street': street,
                    'city': city,
                    'price': formatted_price,
                    'url': url
                })

            except Exception as e:
                self.logger.warning(f"Error parsing listing: {e}")
                continue

        return listings


def main():
    """Main function to run Huispedia scraper."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('huispedia_scraper')

    config = Config()
    scraper = HuispediaScraper(config, logger)
    scraper.scrape()


if __name__ == "__main__":
    main()
