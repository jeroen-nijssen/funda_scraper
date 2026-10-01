"""Tests for property scrapers."""
import json
import logging
from unittest.mock import Mock, patch

import pytest
import requests
from bs4 import BeautifulSoup
from config import Config
from funda import FundaScraper
from huispedia import HuispediaScraper
from pararius import ParariusScraper

# Explicit search parameters for the tests. These are deliberately different
# from the production defaults so that a scraper which ignores its config and
# hardcodes a value cannot pass.
TEST_ENV = {
    'LOCATION': 'gemeente-roermond',
    'DISTANCE': '15',
    'MAX_PRICE': '375000',
    'MIN_ROOMS': '4',
    'MIN_AREA': '120',
}


@pytest.fixture
def config(monkeypatch):
    """Create test configuration from a known set of environment variables."""
    for key, value in TEST_ENV.items():
        monkeypatch.setenv(key, value)
    return Config()


@pytest.fixture
def logger():
    """Create test logger."""
    return logging.getLogger('test')


@pytest.fixture
def mock_response():
    """Create mock HTTP response."""
    response = Mock()
    response.status_code = 200
    response.content = b'<html><body></body></html>'
    return response


class TestScraperConfig:
    """Tests for configuration handling."""

    def test_municipality_strips_gemeente_prefix(self, config):
        assert config.scraper_config.location == 'gemeente-roermond'
        assert config.scraper_config.municipality == 'roermond'

    def test_municipality_is_unchanged_without_prefix(self, monkeypatch):
        monkeypatch.setenv('LOCATION', 'roermond')
        assert Config().scraper_config.municipality == 'roermond'

    def test_search_parameters_come_from_environment(self, config):
        scraper_config = config.scraper_config
        assert scraper_config.distance == 15
        assert scraper_config.max_price == 375000
        assert scraper_config.min_rooms == 4
        assert scraper_config.min_area == 120

    def test_defaults_apply_when_environment_is_empty(self, monkeypatch):
        for key in TEST_ENV:
            monkeypatch.delenv(key, raising=False)
        scraper_config = Config().scraper_config
        assert scraper_config.location == 'gemeente-amsterdam'
        assert scraper_config.municipality == 'amsterdam'
        assert scraper_config.max_price == 450000

    def test_sleep_intervals_default_to_conservative_values(self, monkeypatch):
        for key in ('FUNDA_SLEEP', 'PARARIUS_SLEEP', 'HUISPEDIA_SLEEP'):
            monkeypatch.delenv(key, raising=False)
        intervals = Config().sleep_intervals
        # Guard against anyone lowering these into site-hammering territory.
        assert intervals['funda'] >= 3600
        assert intervals['pararius'] >= 1800
        assert intervals['huispedia'] >= 3600


class TestFundaScraper:
    """Tests for FundaScraper."""

    def test_get_site_name(self, config, logger):
        scraper = FundaScraper(config, logger)
        assert scraper.get_site_name() == "Funda.nl"

    def test_build_url(self, config, logger):
        scraper = FundaScraper(config, logger)
        url = scraper.build_url()
        scraper_config = config.scraper_config

        assert "funda.nl" in url
        # Funda keeps the full 'gemeente-' prefixed location.
        assert scraper_config.location in url
        assert str(scraper_config.max_price) in url
        assert f"+{scraper_config.distance}km" in url

    def test_build_url_follows_location_changes(self, config, logger, monkeypatch):
        monkeypatch.setenv('LOCATION', 'gemeente-utrecht')
        url = FundaScraper(Config(), logger).build_url()
        assert "gemeente-utrecht" in url
        assert "gemeente-roermond" not in url

    def test_parse_listings_empty(self, config, logger):
        scraper = FundaScraper(config, logger)
        soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        listings = scraper.parse_listings(soup)
        assert listings == []

    def test_parse_listings_extracts_fields(self, config, logger):
        html = """
        <div class="search-result-content">
          <h2 class="search-result__header-title fd-m-none"> Teststraat 1 </h2>
          <h4 class="search-result__header-subtitle fd-m-none"> 6041 AB Roermond </h4>
          <span class="search-result-price">&euro; 350.000 k.k.</span>
          <a href="/koop/roermond/huis-123/">link</a>
        </div>
        """
        scraper = FundaScraper(config, logger)
        listings = scraper.parse_listings(BeautifulSoup(html, 'html.parser'))

        assert len(listings) == 1
        assert listings[0]['street'] == 'Teststraat 1'
        assert listings[0]['city'] == '6041 AB Roermond'
        assert listings[0]['url'] == 'https://www.funda.nl/koop/roermond/huis-123/'

    def test_parse_listings_skips_incomplete_entries(self, config, logger):
        # Missing price element, so the listing cannot be processed.
        html = """
        <div class="search-result-content">
          <h2 class="search-result__header-title fd-m-none">Teststraat 1</h2>
          <h4 class="search-result__header-subtitle fd-m-none">Roermond</h4>
          <a href="/koop/roermond/huis-123/">link</a>
        </div>
        """
        scraper = FundaScraper(config, logger)
        assert scraper.parse_listings(BeautifulSoup(html, 'html.parser')) == []

    def test_make_request_renders_with_browser(self, config, logger):
        # Funda blocks plain HTTP clients, so make_request renders with
        # headless Chromium via BaseScraper.render_with_browser instead of
        # issuing a bare requests.Session.get call.
        scraper = FundaScraper(config, logger)
        scraper.render_with_browser = Mock(return_value='<html><body>ok</body></html>')

        response = scraper.make_request('http://test.com')

        scraper.render_with_browser.assert_called_once_with('http://test.com')
        assert response.content == b'<html><body>ok</body></html>'

    def test_make_request_returns_none_when_render_fails(self, config, logger):
        scraper = FundaScraper(config, logger)
        scraper.render_with_browser = Mock(return_value=None)

        assert scraper.make_request('http://test.com') is None

    def test_scrape_success(self, config, logger):
        scraper = FundaScraper(config, logger)
        scraper.render_with_browser = Mock(return_value='<html><body></body></html>')

        # Mock parse_listings to return test data
        scraper.parse_listings = Mock(return_value=[
            {'street': 'Test Street', 'city': 'Test City', 'price': '€300,000', 'url': 'http://test.com'}
        ])

        # Mock Kanban methods
        scraper.check_existing_task = Mock(return_value=(False, 'not existing'))
        scraper.create_kanban_task = Mock(return_value=True)

        # Should not raise exception
        scraper.scrape()

        scraper.render_with_browser.assert_called_once()
        scraper.check_existing_task.assert_called_once()
        scraper.create_kanban_task.assert_called_once()

    def test_scrape_skips_duplicate_listings(self, config, logger):
        scraper = FundaScraper(config, logger)
        scraper.render_with_browser = Mock(return_value='<html><body></body></html>')
        scraper.parse_listings = Mock(return_value=[
            {'street': 'Test Street', 'city': 'Test City', 'price': '€300,000', 'url': 'http://test.com'}
        ])
        scraper.check_existing_task = Mock(return_value=(True, 'http://kanban/task/1'))
        scraper.create_kanban_task = Mock(return_value=True)

        scraper.scrape()

        # An already-known listing must not be recreated on the board.
        scraper.create_kanban_task.assert_not_called()


class TestHuispediaScraper:
    """Tests for HuispediaScraper."""

    def test_get_site_name(self, config, logger):
        scraper = HuispediaScraper(config, logger)
        assert scraper.get_site_name() == "Huispedia.nl"

    def test_build_url(self, config, logger):
        scraper = HuispediaScraper(config, logger)
        url = scraper.build_url()
        scraper_config = config.scraper_config

        assert "huispedia.nl" in url
        # Huispedia uses the bare municipality, so 'gemeente-' must be stripped.
        assert scraper_config.municipality in url
        assert "gemeente-" not in url

    def test_build_url_follows_location_changes(self, logger, monkeypatch):
        monkeypatch.setenv('LOCATION', 'gemeente-utrecht')
        url = HuispediaScraper(Config(), logger).build_url()
        assert "utrecht" in url
        assert "roermond" not in url

    def test_parse_listings_extracts_fields(self, config, logger):
        # Minimal reproduction of the Inertia `data-page` JSON payload that
        # Huispedia embeds in <div id="app">, based on a live search result.
        page_data = {
            "props": {
                "searchData": {
                    "properties": [
                        {
                            "street": "Teststraat", "street_slug": "teststraat",
                            "hnum": 1, "hnumchar": "1", "postcode": "6041 AB",
                            "city_name": "Roermond", "city_slug": "roermond",
                            "object_type": "woonhuis", "aantal_kamers": 5,
                            "woonoppervlakte": 150, "price_sale": None,
                            "price_search": 350000, "id": 42,
                        }
                    ]
                }
            }
        }
        html = f'<div id="app" data-page=\'{json.dumps(page_data)}\'></div>'
        scraper = HuispediaScraper(config, logger)
        listings = scraper.parse_listings(BeautifulSoup(html, 'html.parser'))

        assert len(listings) == 1
        assert listings[0]['street'] == 'Teststraat 1'
        assert listings[0]['city'] == '6041 AB Roermond'
        assert listings[0]['price'] == '€ 350.000 k.k.'
        assert listings[0]['url'] == 'https://www.huispedia.nl/roermond/6041ab/teststraat/1'

    def test_parse_listings_filters_by_config(self, config, logger):
        # config fixture requires min_rooms=4, min_area=120, max_price=375000.
        page_data = {
            "props": {
                "searchData": {
                    "properties": [
                        {
                            "street": "Klein", "street_slug": "klein", "hnum": 2,
                            "hnumchar": "2", "postcode": "6041 AB",
                            "city_name": "Roermond", "city_slug": "roermond",
                            "object_type": "woonhuis", "aantal_kamers": 2,
                            "woonoppervlakte": 150, "price_sale": None,
                            "price_search": 350000, "id": 1,
                        },
                        {
                            "street": "Duur", "street_slug": "duur", "hnum": 3,
                            "hnumchar": "3", "postcode": "6041 AB",
                            "city_name": "Roermond", "city_slug": "roermond",
                            "object_type": "woonhuis", "aantal_kamers": 5,
                            "woonoppervlakte": 150, "price_sale": None,
                            "price_search": 999000, "id": 2,
                        },
                    ]
                }
            }
        }
        html = f'<div id="app" data-page=\'{json.dumps(page_data)}\'></div>'
        scraper = HuispediaScraper(config, logger)
        assert scraper.parse_listings(BeautifulSoup(html, 'html.parser')) == []

    def test_parse_listings_empty_without_app_div(self, config, logger):
        scraper = HuispediaScraper(config, logger)
        soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        assert scraper.parse_listings(soup) == []


class TestParariusScraper:
    """Tests for ParariusScraper."""

    def test_get_site_name(self, config, logger):
        scraper = ParariusScraper(config, logger)
        assert scraper.get_site_name() == "Pararius.nl"

    def test_build_url(self, config, logger):
        scraper = ParariusScraper(config, logger)
        url = scraper.build_url()
        scraper_config = config.scraper_config

        assert "pararius.nl" in url
        # Pararius also uses the bare municipality.
        assert scraper_config.municipality in url
        assert "gemeente-" not in url
        assert str(scraper_config.max_price) in url
        assert f"straal-{scraper_config.distance}" in url
        assert f"{scraper_config.min_area}m2" in url

    def test_build_url_follows_location_changes(self, logger, monkeypatch):
        monkeypatch.setenv('LOCATION', 'gemeente-utrecht')
        url = ParariusScraper(Config(), logger).build_url()
        assert "/utrecht/" in url
        assert "roermond" not in url

    def test_parse_listings_extracts_fields(self, config, logger):
        # Structure taken from a live pararius.nl search result section.
        # Note: the city/location div is "listing-search-item__sub-title",
        # not "listing-search-item__location" - Pararius renamed this class.
        html = """
        <section class="listing-search-item listing-search-item--list listing-search-item--for-sale">
          <a class="listing-search-item__link listing-search-item__link--title"
             href="/huis-te-koop/roermond/abc123/teststraat">Huis Teststraat 1</a>
          <div class="listing-search-item__sub-title">6041 AB Roermond (Centrum)</div>
          <div class="listing-search-item__price">&euro;&nbsp;350.000 k.k.</div>
        </section>
        """
        scraper = ParariusScraper(config, logger)
        listings = scraper.parse_listings(BeautifulSoup(html, 'html.parser'))

        assert len(listings) == 1
        assert listings[0]['street'] == 'Teststraat 1'
        assert listings[0]['city'] == '6041 AB Roermond'
        assert listings[0]['url'] == 'https://www.pararius.nl/huis-te-koop/roermond/abc123/teststraat'

    def test_parse_listings_skips_incomplete_entries(self, config, logger):
        # Missing price element, so the listing cannot be processed.
        html = """
        <section class="listing-search-item listing-search-item--list listing-search-item--for-sale">
          <a class="listing-search-item__link listing-search-item__link--title"
             href="/huis-te-koop/roermond/abc123/teststraat">Huis Teststraat 1</a>
          <div class="listing-search-item__sub-title">6041 AB Roermond (Centrum)</div>
        </section>
        """
        scraper = ParariusScraper(config, logger)
        assert scraper.parse_listings(BeautifulSoup(html, 'html.parser')) == []


class TestBaseScraper:
    """Tests for base scraper functionality."""

    def test_get_headers(self, config, logger):
        scraper = ParariusScraper(config, logger)
        headers = scraper.get_headers()
        assert 'User-Agent' in headers
        assert headers['User-Agent'] in config.user_agents
        # A bare User-Agent gets a 403 from pararius.nl in practice; a full
        # navigation-like header set is required to pass its bot filter.
        assert headers['Accept-Language']
        assert headers['Sec-Fetch-Mode'] == 'navigate'
        assert headers['Sec-Fetch-Dest'] == 'document'

    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get, config, logger, mock_response):
        mock_get.return_value = mock_response
        scraper = ParariusScraper(config, logger)

        response = scraper.make_request('http://test.com')
        assert response == mock_response
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_make_request_failure(self, mock_get, config, logger):
        mock_get.side_effect = requests.RequestException("Network error")
        scraper = ParariusScraper(config, logger)

        with patch('time.sleep'):
            response = scraper.make_request('http://test.com')

        assert response is None
        assert mock_get.call_count == 3  # Should retry 3 times

    @patch('requests.Session.post')
    def test_check_existing_task_found(self, mock_post, config, logger):
        # Mock successful response with existing task
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': [
                {'title': 'Test Title', 'url': 'http://kanban.com/task/1'}
            ]
        }
        mock_post.return_value = mock_response

        scraper = FundaScraper(config, logger)
        found, url = scraper.check_existing_task('Test Title')

        assert found is True
        assert url == 'http://kanban.com/task/1'

    @patch('requests.Session.post')
    def test_check_existing_task_not_found(self, mock_post, config, logger):
        # Mock successful response with no matching task
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': [
                {'title': 'Other Title', 'url': 'http://kanban.com/task/2'}
            ]
        }
        mock_post.return_value = mock_response

        scraper = FundaScraper(config, logger)
        found, url = scraper.check_existing_task('Test Title')

        assert found is False
        assert url == 'not existing'

    @patch('requests.Session.post')
    def test_create_kanban_task_success(self, mock_post, config, logger):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        scraper = FundaScraper(config, logger)
        result = scraper.create_kanban_task('Test Title', 'Test Description')

        assert result is True
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_create_kanban_task_failure(self, mock_post, config, logger):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        scraper = FundaScraper(config, logger)
        result = scraper.create_kanban_task('Test Title', 'Test Description')

        assert result is False
