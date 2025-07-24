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
        assert rows[0]['set'] == 'SV08.5'
        assert rows[0]['type'] == 'Card'
        assert rows[0]['period'] == '3M'
        assert rows[0]['name'] == 'Test Document 1'
        assert rows[0]['url'] == 'https://example.com/test1.md'
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
        assert all('date' in row for row in result)
        assert all(row['date'] == 'ERROR' for row in result)
        assert all('volume' in row for row in result)
        assert all(row['volume'] == 0 for row in result)
    
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
    
    def test_tcgplayer_url_detection(self, csv_processor):
        """Test TCGPlayer URL detection"""
        assert csv_processor._is_tcgplayer_url("https://www.tcgplayer.com/product/123") is True
        assert csv_processor._is_tcgplayer_url("https://r.jina.ai/https://www.tcgplayer.com/product/123") is True
        assert csv_processor._is_tcgplayer_url("https://TCGPLAYER.COM/product/123") is True
        assert csv_processor._is_tcgplayer_url("https://example.com") is False
        assert csv_processor._is_tcgplayer_url("https://google.com") is False
    
    def test_calculate_price_trend_insufficient_data(self, csv_processor):
        """Test price trend calculation with insufficient data"""
        # Empty data
        result = csv_processor._calculate_price_trend([])
        assert result == 'insufficient_data'
        
        # Single data point
        price_data = [{'date': '7/16 to 7/18', 'holofoil': '$1,088.28', 'price': '$0.00'}]
        result = csv_processor._calculate_price_trend(price_data)
        assert result == 'insufficient_data'
    
    def test_calculate_price_trend_upward(self, csv_processor):
        """Test price trend calculation for upward trend"""
        price_data = [
            {'date': '7/16 to 7/18', 'holofoil': '$1,200.00', 'price': '$0.00'},  # newest
            {'date': '7/13 to 7/15', 'holofoil': '$1,150.00', 'price': '$0.00'},
            {'date': '7/10 to 7/12', 'holofoil': '$1,000.00', 'price': '$0.00'}   # oldest
        ]
        result = csv_processor._calculate_price_trend(price_data)
        assert result == 'up_20.0%'
    
    def test_calculate_price_trend_downward(self, csv_processor):
        """Test price trend calculation for downward trend"""
        price_data = [
            {'date': '7/16 to 7/18', 'holofoil': '$800.00', 'price': '$0.00'},   # newest
            {'date': '7/13 to 7/15', 'holofoil': '$900.00', 'price': '$0.00'},
            {'date': '7/10 to 7/12', 'holofoil': '$1,000.00', 'price': '$0.00'}  # oldest
        ]
        result = csv_processor._calculate_price_trend(price_data)
        assert result == 'down_20.0%'
    
    def test_calculate_price_trend_stable(self, csv_processor):
        """Test price trend calculation for stable prices"""
        price_data = [
            {'date': '7/16 to 7/18', 'holofoil': '$1,020.00', 'price': '$0.00'},  # newest
            {'date': '7/13 to 7/15', 'holofoil': '$1,010.00', 'price': '$0.00'},
            {'date': '7/10 to 7/12', 'holofoil': '$1,000.00', 'price': '$0.00'}   # oldest
        ]
        result = csv_processor._calculate_price_trend(price_data)
        assert result == 'stable_2.0%'
    
    def test_calculate_price_trend_with_commas(self, csv_processor):
        """Test price trend calculation with comma-formatted prices"""
        price_data = [
            {'date': '7/16 to 7/18', 'holofoil': '$1,200.00', 'price': '$0.00'},  # newest
            {'date': '7/10 to 7/12', 'holofoil': '$1,000.00', 'price': '$0.00'}   # oldest
        ]
        result = csv_processor._calculate_price_trend(price_data)
        assert result == 'up_20.0%'
    
    def test_calculate_price_trend_invalid_data(self, csv_processor):
        """Test price trend calculation with invalid price data"""
        price_data = [
            {'date': '7/16 to 7/18', 'holofoil': 'invalid', 'price': '$0.00'},
            {'date': '7/10 to 7/12', 'holofoil': '$1,000.00', 'price': '$0.00'}
        ]
        result = csv_processor._calculate_price_trend(price_data)
        assert result == 'calculation_error'
    
    def test_calculate_price_trend_zero_baseline(self, csv_processor):
        """Test price trend calculation with zero baseline price"""
        price_data = [
            {'date': '7/16 to 7/18', 'holofoil': '$100.00', 'price': '$0.00'},
            {'date': '7/10 to 7/12', 'holofoil': '$0.00', 'price': '$0.00'}
        ]
        result = csv_processor._calculate_price_trend(price_data)
        assert result == 'no_baseline'
    
    @patch('common.processor.WebClient')
    @patch('common.processor.MarkdownParser')
    def test_tcgplayer_normalized_output(self, mock_markdown, mock_web_client, csv_processor):
        """Test TCGPlayer URL generates normalized price history rows"""
        # Setup mocks
        mock_web_instance = Mock()
        mock_markdown_instance = Mock()
        mock_web_client.return_value = mock_web_instance
        mock_markdown.return_value = mock_markdown_instance
        
        mock_web_instance.fetch.return_value = "# Test Content"
        mock_markdown_instance.parse.return_value = "Test Content"
        
        # Mock price history data
        mock_price_data = [
            {'date': '7/16 to 7/18', 'holofoil': '$1,200.00', 'price': '$0.00'},
            {'date': '7/13 to 7/15', 'holofoil': '$1,150.00', 'price': '$1.00'},
            {'date': '7/10 to 7/12', 'holofoil': '$1,100.00', 'price': '$2.00'}
        ]
        mock_markdown_instance.parse_price_history_data.return_value = mock_price_data
        
        # Create test data with TCGPlayer URL
        test_data = [{
            'set': 'SV08.5',
            'type': 'Card', 
            'period': '3M',
            'name': 'Test Card',
            'url': 'https://www.tcgplayer.com/product/123'
        }]
        
        # Create processor with mocked dependencies
        processor = CsvProcessor()
        processor.web_client = mock_web_instance
        processor.markdown_parser = mock_markdown_instance
        
        result = processor._process_rows(test_data)
        
        # Should have 3 normalized rows (one for each price record)
        assert len(result) == 3
        
        # Check first normalized row
        assert result[0]['set'] == 'SV08.5'
        assert result[0]['type'] == 'Card'
        assert result[0]['period'] == '3M'
        assert result[0]['name'] == 'Test Card'
        assert result[0]['date'] == '7/16 to 7/18'
        assert result[0]['holofoil_price'] == '$1,200.00'
        assert result[0]['volume'] == 0
        
        # Check second normalized row
        assert result[1]['date'] == '7/13 to 7/15'
        assert result[1]['holofoil_price'] == '$1,150.00'
        assert result[1]['volume'] == 1
        
        # Check third normalized row
        assert result[2]['date'] == '7/10 to 7/12'
        assert result[2]['holofoil_price'] == '$1,100.00'
        assert result[2]['volume'] == 2