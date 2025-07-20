import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from common.processor import CsvProcessor
from common.logger import AppLogger


class TestCsvProcessor:
    
    @classmethod
    def setup_class(cls):
        """Setup logging for all tests in this class."""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")
        cls.logger = AppLogger.get_logger(__name__)
        cls.logger.info("Starting CsvProcessor tests")
    
    def test_init(self, csv_processor):
        assert csv_processor is not None
        assert hasattr(csv_processor, 'logger')
        assert hasattr(csv_processor, 'web_client')
        assert hasattr(csv_processor, 'markdown_parser')
        assert hasattr(csv_processor, 'results')
        assert csv_processor.results == []
    
    def test_read_csv_valid_file(self, csv_processor, sample_csv_file):
        rows = csv_processor._read_csv(sample_csv_file)
        
        assert len(rows) == 3
        assert rows[0]['url'] == 'https://example.com/test1.md'
        assert rows[0]['name'] == 'Test Document 1'
        assert rows[1]['url'] == 'https://example.com/test2.md'
        assert rows[2]['url'] == 'https://example.com/test3.md'
    
    def test_read_csv_nonexistent_file(self, csv_processor):
        with pytest.raises(FileNotFoundError):
            csv_processor._read_csv(Path('/nonexistent/file.csv'))
    
    def test_read_csv_empty_file(self, csv_processor):
        with pytest.raises(Exception):
            csv_processor._read_csv(Path('/dev/null'))
    
    @patch('common.processor.WebClient')
    @patch('common.processor.MarkdownParser')
    def test_process_rows_success(self, mock_markdown, mock_web_client, csv_processor, sample_csv_data):
        # Setup mocks
        mock_web_instance = Mock()
        mock_markdown_instance = Mock()
        mock_web_client.return_value = mock_web_instance
        mock_markdown.return_value = mock_markdown_instance
        
        mock_web_instance.fetch.return_value = "# Test Content"
        mock_markdown_instance.parse.return_value = "Test Content"
        
        # Create new processor with mocked dependencies
        processor = CsvProcessor()
        processor.web_client = mock_web_instance
        processor.markdown_parser = mock_markdown_instance
        
        result = processor._process_rows(sample_csv_data)
        
        assert len(result) == 3
        assert all('content' in row for row in result)
        assert result[0]['content'] == "Test Content"
    
    @patch('common.processor.WebClient')
    @patch('common.processor.MarkdownParser')
    def test_process_rows_with_errors(self, mock_markdown, mock_web_client, csv_processor, sample_csv_data):
        # Setup mocks to simulate errors
        mock_web_instance = Mock()
        mock_markdown_instance = Mock()
        mock_web_client.return_value = mock_web_instance
        mock_markdown.return_value = mock_markdown_instance
        
        mock_web_instance.fetch.side_effect = Exception("Network error")
        
        # Create new processor with mocked dependencies
        processor = CsvProcessor()
        processor.web_client = mock_web_instance
        processor.markdown_parser = mock_markdown_instance
        
        result = processor._process_rows(sample_csv_data)
        
        assert len(result) == 3
        assert all('content' in row for row in result)
        assert all(row['content'] == '' for row in result)
    
    def test_process_rows_missing_url_column(self, csv_processor):
        invalid_data = [
            {'name': 'Test Document 1'},
            {'name': 'Test Document 2'}
        ]
        
        result = csv_processor._process_rows(invalid_data)
        
        assert len(result) == 0
    
    @patch('common.processor.WebClient')
    @patch('common.processor.MarkdownParser')
    def test_process_full_workflow(self, mock_markdown, mock_web_client, csv_processor, sample_csv_file):
        # Setup mocks
        mock_web_instance = Mock()
        mock_markdown_instance = Mock()
        mock_web_client.return_value = mock_web_instance
        mock_markdown.return_value = mock_markdown_instance
        
        mock_web_instance.fetch.return_value = "# Test Content"
        mock_markdown_instance.parse.return_value = "Test Content"
        
        # Create new processor with mocked dependencies
        processor = CsvProcessor()
        processor.web_client = mock_web_instance
        processor.markdown_parser = mock_markdown_instance
        
        result = processor.process(sample_csv_file)
        
        assert len(result) == 3
        assert processor.results == result
        assert all('content' in row for row in result)
        assert all(row['content'] == "Test Content" for row in result)