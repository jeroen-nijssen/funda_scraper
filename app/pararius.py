"""Pararius.nl property scraper."""
import logging

from base_scraper import BaseScraper
from bs4 import BeautifulSoup
from config import Config


class ParariusScraper(BaseScraper):
    """Scraper for Pararius.nl property listings."""

    def get_site_name(self) -> str:
        return "Pararius.nl"

    def build_url(self) -> str:
        """Build Pararius search URL."""
        config = self.config.scraper_config
        # Pararius uses the bare municipality, without Funda's 'gemeente-' prefix.
        location = config.municipality
        return (f"https://www.pararius.nl/koopwoningen/{location}/huis/0-{config.max_price}/"
                f"straal-{config.distance}/{config.min_rooms}-aantalkamers/3-slaapkamers/{config.min_area}m2")

    def parse_listings(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """Parse Pararius listings from HTML."""
        listings = []
        items = soup.find_all(
            "section",
            class_="listing-search-item listing-search-item--list listing-search-item--for-sale"
        )

        for item in items:
            try:
                # Extract street address
                street_elem = item.find('a', class_="listing-search-item__link listing-search-item__link--title")
                if not street_elem:
                    continue
                street = " ".join(street_elem.get_text().strip().replace("Huis", "").split())

                # Extract city
                city_elem = item.find("div", class_="listing-search-item__sub-title")
                if not city_elem:
                    continue
                city = " ".join(city_elem.get_text().strip().split("(")[0].split())

                # Extract price
                price_elem = item.find("div", class_="listing-search-item__price")
                if not price_elem:
                    continue
                price = " ".join(price_elem.get_text().strip().split())

                # Extract URL
                link_elem = item.find('a', class_="listing-search-item__link listing-search-item__link--title")
                if not link_elem:
                    continue
                relative_url = link_elem.get('href')
                full_url = f"https://www.pararius.nl{relative_url}"

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
    """Main function to run Pararius scraper."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('pararius_scraper')

    config = Config()
    scraper = ParariusScraper(config, logger)
    scraper.scrape()


if __name__ == "__main__":
    main()
