import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from main import main
from common.logger import AppLogger


class TestMain:
    
    @classmethod
    def setup_class(cls):
        """Setup logging for all tests in this class."""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")
        cls.logger = AppLogger.get_logger(__name__)
        cls.logger.info("Starting Main CLI tests")
    
    def test_main_help(self, runner):
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'Process CSV data with web requests and markdown parsing' in result.stdout
        assert 'input_file' in result.stdout
        assert 'output_file' in result.stdout
    
    def test_main_missing_arguments(self, runner):
        result = runner.invoke(main, [])
        
        assert result.exit_code != 0
        # argparse outputs errors to stderr, and our message may vary
        assert result.stderr or 'required' in result.stdout.lower() or 'argument' in result.stdout.lower()
    
    def test_main_nonexistent_input_file(self, runner):
        result = runner.invoke(main, ['/nonexistent/input.csv', '/tmp/output.csv'])
        
        assert result.exit_code == 1
        assert 'does not exist' in result.stdout
    
    @patch('main.CsvProcessor')
    @patch('main.CsvWriter')
    def test_main_success(self, mock_csv_writer, mock_csv_processor, runner, sample_csv_file, sample_output_file):
        # Setup mocks
        mock_processor_instance = Mock()
        mock_writer_instance = Mock()
        mock_csv_processor.return_value = mock_processor_instance
        mock_csv_writer.return_value = mock_writer_instance
        
        mock_processor_instance.process.return_value = [
            {'url': 'https://example.com/test.md', 'name': 'Test', 'content': 'Processed content'}
        ]
        
        result = runner.invoke(main, [str(sample_csv_file), str(sample_output_file)])
        
        assert result.exit_code == 0
        assert 'Processing complete' in result.stdout
        
        # Verify mocks were called
        mock_processor_instance.process.assert_called_once_with(sample_csv_file)
        mock_writer_instance.write_unique.assert_called_once()
    
    @patch('main.CsvProcessor')
    @patch('main.CsvWriter')
    def test_main_processing_error(self, mock_csv_writer, mock_csv_processor, runner, sample_csv_file, sample_output_file):
        # Setup mocks to raise exception
        mock_processor_instance = Mock()
        mock_csv_processor.return_value = mock_processor_instance
        mock_processor_instance.process.side_effect = Exception("Processing failed")
        
        result = runner.invoke(main, [str(sample_csv_file), str(sample_output_file)])
        
        assert result.exit_code == 1
        assert 'Processing failed' in result.stdout
    
    @patch('main.CsvProcessor')
    @patch('main.CsvWriter')
    def test_main_verbose_mode(self, mock_csv_writer, mock_csv_processor, runner, sample_csv_file, sample_output_file):
        # Setup mocks
        mock_processor_instance = Mock()
        mock_writer_instance = Mock()
        mock_csv_processor.return_value = mock_processor_instance
        mock_csv_writer.return_value = mock_writer_instance
        
        mock_processor_instance.process.return_value = []
        
        result = runner.invoke(main, [str(sample_csv_file), str(sample_output_file), '--verbose'])
        
        assert result.exit_code == 0
        
        # Verbose mode should still work (logging level change is internal)
        mock_processor_instance.process.assert_called_once()
        mock_writer_instance.write_unique.assert_called_once()
    
    @patch('main.CsvProcessor')
    @patch('main.CsvWriter')
    def test_main_short_verbose_flag(self, mock_csv_writer, mock_csv_processor, runner, sample_csv_file, sample_output_file):
        # Setup mocks
        mock_processor_instance = Mock()
        mock_writer_instance = Mock()
        mock_csv_processor.return_value = mock_processor_instance
        mock_csv_writer.return_value = mock_writer_instance
        
        mock_processor_instance.process.return_value = []
        
        result = runner.invoke(main, [str(sample_csv_file), str(sample_output_file), '-v'])
        
        assert result.exit_code == 0
        
        # Short verbose flag should work
        mock_processor_instance.process.assert_called_once()
        mock_writer_instance.write_unique.assert_called_once()
    
    def test_main_invalid_arguments(self, runner):
        result = runner.invoke(main, ['--invalid-flag'])
        
        assert result.exit_code != 0
        # argparse may output different error messages
        assert result.stderr or 'unrecognized' in result.stdout.lower() or 'invalid' in result.stdout.lower()
    
    @patch('main.AppLogger')
    @patch('main.CsvProcessor')
    @patch('main.CsvWriter')
    def test_main_logging_setup(self, mock_csv_writer, mock_csv_processor, mock_app_logger, runner, sample_csv_file, sample_output_file):
        # Setup mocks
        mock_processor_instance = Mock()
        mock_writer_instance = Mock()
        mock_logger_instance = Mock()
        
        mock_csv_processor.return_value = mock_processor_instance
        mock_csv_writer.return_value = mock_writer_instance
        mock_app_logger.return_value = mock_logger_instance
        
        mock_processor_instance.process.return_value = []
        
        # Test normal mode
        result = runner.invoke(main, [str(sample_csv_file), str(sample_output_file)])
        assert result.exit_code == 0
        mock_logger_instance.setup_logging.assert_called()
        
        # Reset mock
        mock_logger_instance.reset_mock()
        
        # Test verbose mode
        result = runner.invoke(main, [str(sample_csv_file), str(sample_output_file), '--verbose'])
        assert result.exit_code == 0
        mock_logger_instance.setup_logging.assert_called()