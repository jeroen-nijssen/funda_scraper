"""Tests for property scrapers."""
import json
import logging
from unittest.mock import Mock, patch

import pytest
import requests
from bs4 import BeautifulSoup

from config import Config
from funda import FundaScraper
from jaap import JaapScraper
from pararius import ParariusScraper


@pytest.fixture
def config():
    """Create test configuration."""
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


class TestFundaScraper:
    """Tests for FundaScraper."""
    
    def test_get_site_name(self, config, logger):
        scraper = FundaScraper(config, logger)
        assert scraper.get_site_name() == "Funda.nl"
    
    def test_build_url(self, config, logger):
        scraper = FundaScraper(config, logger)
        url = scraper.build_url()
        assert "funda.nl" in url
        assert "gemeente-amsterdam" in url
        assert "450000" in url
        assert "5km" in url
    
    def test_parse_listings_empty(self, config, logger):
        scraper = FundaScraper(config, logger)
        soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        listings = scraper.parse_listings(soup)
        assert listings == []
    
    @patch('requests.Session.get')
    def test_scrape_success(self, mock_get, config, logger, mock_response):
        mock_get.return_value = mock_response
        scraper = FundaScraper(config, logger)
        
        # Mock parse_listings to return test data
        scraper.parse_listings = Mock(return_value=[
            {'street': 'Test Street', 'city': 'Test City', 'price': '€300,000', 'url': 'http://test.com'}
        ])
        
        # Mock Kanban methods
        scraper.check_existing_task = Mock(return_value=(False, 'not existing'))
        scraper.create_kanban_task = Mock(return_value=True)
        
        # Should not raise exception
        scraper.scrape()
        
        mock_get.assert_called_once()
        scraper.check_existing_task.assert_called_once()
        scraper.create_kanban_task.assert_called_once()


class TestJaapScraper:
    """Tests for JaapScraper."""
    
    def test_get_site_name(self, config, logger):
        scraper = JaapScraper(config, logger)
        assert scraper.get_site_name() == "Jaap.nl"
    
    def test_build_url(self, config, logger):
        scraper = JaapScraper(config, logger)
        url = scraper.build_url()
        assert "jaap.nl" in url
        assert "roermond" in url  # gemeente- should be removed
        assert "450000" in url
        assert "5km" in url


class TestParariusScraper:
    """Tests for ParariusScraper."""
    
    def test_get_site_name(self, config, logger):
        scraper = ParariusScraper(config, logger)
        assert scraper.get_site_name() == "Pararius.nl"
    
    def test_build_url(self, config, logger):
        scraper = ParariusScraper(config, logger)
        url = scraper.build_url()
        assert "pararius.nl" in url
        assert "roermond" in url  # gemeente- should be removed
        assert "450000" in url
        assert "straal-5" in url


class TestBaseScraper:
    """Tests for base scraper functionality."""
    
    def test_get_headers(self, config, logger):
        scraper = FundaScraper(config, logger)
        headers = scraper.get_headers()
        assert 'User-Agent' in headers
        assert headers['User-Agent'] in config.user_agents
    
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get, config, logger, mock_response):
        mock_get.return_value = mock_response
        scraper = FundaScraper(config, logger)
        
        response = scraper.make_request('http://test.com')
        assert response == mock_response
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_make_request_failure(self, mock_get, config, logger):
        mock_get.side_effect = requests.RequestException("Network error")
        scraper = FundaScraper(config, logger)
        
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