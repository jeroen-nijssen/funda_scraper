"""Funda.nl property scraper.

Funda serves a static Akamai bot-check page ("Je bent bijna op de pagina die
je zoekt") to plain HTTP clients, so this scraper renders pages with headless
Chromium via BaseScraper.render_with_browser() instead of a bare request.

This is a best-effort attempt, NOT a confirmed fix: rendering with headless
Chromium (plain, with anti-automation flags, and with playwright-stealth) was
tested against the live site and still hit the same static bot-check page,
which looks like an IP-reputation block at the CDN edge rather than a
solvable JS/fingerprint challenge - something a headless browser can't get
around, and something that couldn't be confirmed either way from this
environment. It may behave differently from a different network.

Because of this, the parse_listings selectors below are also unverified
against real Funda markup - there was no way to see past the bot-check page
to confirm they still match the site's current HTML structure.
"""
import logging

import requests
from base_scraper import BaseScraper
from bs4 import BeautifulSoup
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

    def make_request(self, url: str, max_retries: int = 3) -> requests.Response | None:
        """Render the page with headless Chromium instead of a bare HTTP request.

        Wraps the rendered HTML in a minimal shim exposing `.content` so the
        base class's `scrape()` can keep calling `BeautifulSoup(response.content, ...)`
        unmodified.
        """
        html = self.render_with_browser(url)
        if html is None:
            return None

        class _RenderedResponse:
            def __init__(self, html: str):
                self.content = html.encode('utf-8')

        return _RenderedResponse(html)

    def parse_listings(self, soup: BeautifulSoup) -> list[dict[str, str]]:
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
