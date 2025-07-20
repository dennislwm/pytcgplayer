import pytest
import requests
from unittest.mock import patch, Mock

from common.web_client import WebClient
from common.logger import AppLogger


class TestWebClient:
    
    @classmethod
    def setup_class(cls):
        """Setup logging for all tests in this class."""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")
        cls.logger = AppLogger.get_logger(__name__)
        cls.logger.info("Starting WebClient tests")
    
    def test_init(self, web_client):
        assert web_client is not None
        assert hasattr(web_client, 'logger')
        assert hasattr(web_client, 'timeout')
        assert hasattr(web_client, 'session')
        assert web_client.timeout == 30
        assert 'User-Agent' in web_client.session.headers
    
    def test_init_custom_timeout(self):
        client = WebClient(timeout=60)
        assert client.timeout == 60
    
    @patch('common.web_client.requests.Session')
    def test_fetch_success(self, mock_session, web_client):
        # Setup mock
        mock_response = Mock()
        mock_response.text = "Test content"
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        client = WebClient()
        client.session = mock_session_instance
        
        result = client.fetch("https://example.com/test.md")
        
        assert result == "Test content"
        mock_session_instance.get.assert_called_once_with("https://example.com/test.md", timeout=30)
        mock_response.raise_for_status.assert_called_once()
    
    @patch('common.web_client.requests.Session')
    def test_fetch_http_error(self, mock_session, web_client):
        # Setup mock to raise HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        client = WebClient()
        client.session = mock_session_instance
        
        with pytest.raises(requests.exceptions.HTTPError):
            client.fetch("https://example.com/nonexistent.md")
    
    @patch('common.web_client.requests.Session')
    def test_fetch_connection_error(self, mock_session, web_client):
        # Setup mock to raise connection error
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        mock_session.return_value = mock_session_instance
        
        client = WebClient()
        client.session = mock_session_instance
        
        with pytest.raises(requests.exceptions.ConnectionError):
            client.fetch("https://example.com/test.md")
    
    @patch('common.web_client.requests.Session')
    def test_fetch_timeout_error(self, mock_session, web_client):
        # Setup mock to raise timeout error
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = requests.exceptions.Timeout("Request timed out")
        mock_session.return_value = mock_session_instance
        
        client = WebClient()
        client.session = mock_session_instance
        
        with pytest.raises(requests.exceptions.Timeout):
            client.fetch("https://example.com/test.md")
    
    def test_fetch_with_mock_requests(self, web_client, mock_requests, sample_markdown_content):
        result = web_client.fetch("https://example.com/test1.md")
        
        assert result == sample_markdown_content
        assert len(result) > 0
    
    def test_fetch_404_with_mock_requests(self, web_client, mock_requests):
        with pytest.raises(requests.exceptions.HTTPError):
            web_client.fetch("https://example.com/test2.md")
    
    def test_fetch_timeout_with_mock_requests(self, web_client, mock_requests):
        with pytest.raises(requests.exceptions.ConnectTimeout):
            web_client.fetch("https://example.com/test3.md")
    
    def test_user_agent_header(self, web_client):
        assert web_client.session.headers['User-Agent'] == 'CSVProcessor/1.0'