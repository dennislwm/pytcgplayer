import pytest
import csv
from pathlib import Path

from common.csv_writer import CsvWriter
from common.logger import AppLogger


class TestCsvWriter:
    
    @classmethod
    def setup_class(cls):
        """Setup logging for all tests in this class."""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")
        cls.logger = AppLogger.get_logger(__name__)
        cls.logger.info("Starting CsvWriter tests")
    
    def test_init(self, csv_writer):
        assert csv_writer is not None
        assert hasattr(csv_writer, 'logger')
    
    def test_write_valid_data(self, csv_writer, sample_csv_data, sample_output_file):
        # Add content to sample data
        test_data = [
            {'url': 'https://example.com/test1.md', 'name': 'Test Document 1', 'content': 'Content 1'},
            {'url': 'https://example.com/test2.md', 'name': 'Test Document 2', 'content': 'Content 2'},
            {'url': 'https://example.com/test3.md', 'name': 'Test Document 3', 'content': 'Content 3'}
        ]
        
        csv_writer.write(test_data, sample_output_file)
        
        # Verify file was created and contains correct data
        assert sample_output_file.exists()
        
        with open(sample_output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]['url'] == 'https://example.com/test1.md'
        assert rows[0]['name'] == 'Test Document 1'
        assert rows[0]['content'] == 'Content 1'
        assert rows[1]['content'] == 'Content 2'
        assert rows[2]['content'] == 'Content 3'
    
    def test_write_empty_data(self, csv_writer):
        import tempfile
        import os
        
        # Use a non-existent file path
        temp_dir = tempfile.gettempdir()
        output_file = Path(temp_dir) / "test_empty_output.csv"
        
        # Ensure file doesn't exist initially
        if output_file.exists():
            os.remove(output_file)
        
        csv_writer.write([], output_file)
        
        # File should not be created for empty data
        assert not output_file.exists()
    
    def test_write_single_row(self, csv_writer, sample_output_file):
        test_data = [
            {'url': 'https://example.com/test.md', 'name': 'Single Test', 'content': 'Single content'}
        ]
        
        csv_writer.write(test_data, sample_output_file)
        
        assert sample_output_file.exists()
        
        with open(sample_output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['url'] == 'https://example.com/test.md'
        assert rows[0]['name'] == 'Single Test'
        assert rows[0]['content'] == 'Single content'
    
    def test_write_special_characters(self, csv_writer, sample_output_file):
        test_data = [
            {
                'url': 'https://example.com/special.md',
                'name': 'Special "Characters" Test',
                'content': 'Content with\nnewlines and "quotes" and, commas'
            }
        ]
        
        csv_writer.write(test_data, sample_output_file)
        
        assert sample_output_file.exists()
        
        with open(sample_output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['name'] == 'Special "Characters" Test'
        assert 'newlines' in rows[0]['content']
        assert '"quotes"' in rows[0]['content']
        assert 'commas' in rows[0]['content']
    
    def test_write_unicode_characters(self, csv_writer, sample_output_file):
        test_data = [
            {
                'url': 'https://example.com/unicode.md',
                'name': 'Unicode Test 🚀',
                'content': 'Content with émojis 😀 and accénts'
            }
        ]
        
        csv_writer.write(test_data, sample_output_file)
        
        assert sample_output_file.exists()
        
        with open(sample_output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert '🚀' in rows[0]['name']
        assert '😀' in rows[0]['content']
        assert 'émojis' in rows[0]['content']
        assert 'accénts' in rows[0]['content']
    
    def test_write_different_field_orders(self, csv_writer, sample_output_file):
        # Test that fieldnames are taken from first row's keys
        test_data = [
            {'content': 'Content 1', 'name': 'Test 1', 'url': 'https://example.com/test1.md'},
            {'content': 'Content 2', 'name': 'Test 2', 'url': 'https://example.com/test2.md'}
        ]
        
        csv_writer.write(test_data, sample_output_file)
        
        assert sample_output_file.exists()
        
        with open(sample_output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
        
        # Should preserve the order from the first row
        assert fieldnames == ['content', 'name', 'url']
        assert len(rows) == 2
    
    def test_write_missing_fields_in_subsequent_rows(self, csv_writer, sample_output_file):
        test_data = [
            {'url': 'https://example.com/test1.md', 'name': 'Test 1', 'content': 'Content 1'},
            {'url': 'https://example.com/test2.md', 'name': 'Test 2'},  # Missing content field
        ]
        
        csv_writer.write(test_data, sample_output_file)
        
        assert sample_output_file.exists()
        
        with open(sample_output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['content'] == 'Content 1'
        assert rows[1]['content'] == ''  # Missing field should be empty string
    
    def test_write_to_nonexistent_directory(self, csv_writer):
        nonexistent_path = Path('/nonexistent/directory/output.csv')
        test_data = [{'test': 'data'}]
        
        with pytest.raises(FileNotFoundError):
            csv_writer.write(test_data, nonexistent_path)
    
    def test_write_unique_new_file(self, csv_writer, tmp_path):
        """Test writing unique data to a new file"""
        test_file = tmp_path / "unique_test.csv"
        
        data = [
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/1 to 1/3', 'holofoil_price': '$100.00', 'additional_price': '$0.00'},
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/4 to 1/6', 'holofoil_price': '$105.00', 'additional_price': '$1.00'}
        ]
        
        csv_writer.write_unique(data, test_file)
        
        assert test_file.exists()
        
        # Read and verify content
        with open(test_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['name'] == 'Test Card'
        assert rows[0]['date'] == '1/1 to 1/3'
        assert rows[1]['date'] == '1/4 to 1/6'
    
    def test_write_unique_existing_file_no_duplicates(self, csv_writer, tmp_path):
        """Test writing unique data when no duplicates exist"""
        test_file = tmp_path / "unique_existing.csv"
        
        # Create initial data
        initial_data = [
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/1 to 1/3', 'holofoil_price': '$100.00', 'additional_price': '$0.00'}
        ]
        csv_writer.write(initial_data, test_file)
        
        # Add new unique data
        new_data = [
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/4 to 1/6', 'holofoil_price': '$105.00', 'additional_price': '$1.00'}
        ]
        csv_writer.write_unique(new_data, test_file)
        
        # Verify combined data
        with open(test_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['date'] == '1/1 to 1/3'
        assert rows[1]['date'] == '1/4 to 1/6'
    
    def test_write_unique_existing_file_with_duplicates(self, csv_writer, tmp_path):
        """Test writing unique data when duplicates exist"""
        test_file = tmp_path / "unique_duplicates.csv"
        
        # Create initial data
        initial_data = [
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/1 to 1/3', 'holofoil_price': '$100.00', 'additional_price': '$0.00'},
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/4 to 1/6', 'holofoil_price': '$105.00', 'additional_price': '$1.00'}
        ]
        csv_writer.write(initial_data, test_file)
        
        # Try to add data with duplicates and one new entry
        new_data = [
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/1 to 1/3', 'holofoil_price': '$100.00', 'additional_price': '$0.00'},  # Duplicate
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/7 to 1/9', 'holofoil_price': '$110.00', 'additional_price': '$2.00'}   # New
        ]
        csv_writer.write_unique(new_data, test_file)
        
        # Verify only unique data was added
        with open(test_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        assert len(rows) == 3  # 2 original + 1 new
        dates = [row['date'] for row in rows]
        assert '1/1 to 1/3' in dates
        assert '1/4 to 1/6' in dates
        assert '1/7 to 1/9' in dates
    
    def test_write_unique_custom_key_columns(self, csv_writer, tmp_path):
        """Test writing unique data with custom key columns"""
        test_file = tmp_path / "unique_custom_keys.csv"
        
        # Create initial data
        initial_data = [
            {'id': '1', 'name': 'Test', 'value': '100'},
            {'id': '2', 'name': 'Test2', 'value': '200'}
        ]
        csv_writer.write(initial_data, test_file)
        
        # Add data with same id (should be duplicate) and new id
        new_data = [
            {'id': '1', 'name': 'Test', 'value': '150'},  # Same id, different value - should be duplicate
            {'id': '3', 'name': 'Test3', 'value': '300'}  # New id
        ]
        
        csv_writer.write_unique(new_data, test_file, key_columns=['id'])
        
        # Verify only new id was added
        with open(test_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        assert len(rows) == 3
        ids = [row['id'] for row in rows]
        assert '1' in ids
        assert '2' in ids
        assert '3' in ids
    
    def test_write_unique_empty_data(self, csv_writer, tmp_path):
        """Test writing empty data to existing file"""
        test_file = tmp_path / "unique_empty.csv"
        
        # Create initial data
        initial_data = [
            {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Test Card', 'date': '1/1 to 1/3', 'holofoil_price': '$100.00', 'additional_price': '$0.00'}
        ]
        csv_writer.write(initial_data, test_file)
        
        # Try to add empty data
        csv_writer.write_unique([], test_file)
        
        # Verify original data is unchanged
        with open(test_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['name'] == 'Test Card'