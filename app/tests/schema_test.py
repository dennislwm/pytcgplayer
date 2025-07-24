import pytest
import tempfile
import csv
from pathlib import Path

from common.helpers import FileHelper
from common.processor import CsvProcessor
from common.logger import AppLogger


class TestSchemaValidation:
    @classmethod
    def setup_class(cls):
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")
        cls.logger = AppLogger.get_logger(__name__)

    def test_valid_input_schema(self):
        """Test schema validation with valid input CSV"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['set', 'type', 'period', 'name', 'url'])
            writer.writerow(['SV01', 'Card', '3M', 'Test Card', 'https://example.com'])
            csv_path = Path(f.name)
        
        try:
            schema_path = Path(__file__).parent.parent / 'schema' / 'input_v1.json'
            is_valid, errors = FileHelper.validate_csv_schema(csv_path, schema_path)
            
            assert is_valid, f"Schema validation should pass: {errors}"
            assert len(errors) == 0
        finally:
            csv_path.unlink()

    def test_invalid_input_schema_missing_headers(self):
        """Test schema validation with missing headers"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['set', 'name', 'url'])  # Missing 'type' and 'period'
            writer.writerow(['SV01', 'Test Card', 'https://example.com'])
            csv_path = Path(f.name)
        
        try:
            schema_path = Path(__file__).parent.parent / 'schema' / 'input_v1.json'
            is_valid, errors = FileHelper.validate_csv_schema(csv_path, schema_path)
            
            assert not is_valid
            assert len(errors) > 0
            assert any('Missing headers' in error for error in errors)
        finally:
            csv_path.unlink()

    def test_invalid_input_schema_extra_headers(self):
        """Test schema validation with extra headers"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['set', 'type', 'period', 'name', 'url', 'extra_column'])
            writer.writerow(['SV01', 'Card', '3M', 'Test Card', 'https://example.com', 'extra'])
            csv_path = Path(f.name)
        
        try:
            schema_path = Path(__file__).parent.parent / 'schema' / 'input_v1.json'
            is_valid, errors = FileHelper.validate_csv_schema(csv_path, schema_path)
            
            assert not is_valid
            assert len(errors) > 0
            assert any('Extra headers' in error for error in errors)
        finally:
            csv_path.unlink()

    def test_invalid_input_schema_wrong_order(self):
        """Test schema validation with wrong header order"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'set', 'type', 'period', 'url'])  # Wrong order
            writer.writerow(['Test Card', 'SV01', 'Card', '3M', 'https://example.com'])
            csv_path = Path(f.name)
        
        try:
            schema_path = Path(__file__).parent.parent / 'schema' / 'input_v1.json'
            is_valid, errors = FileHelper.validate_csv_schema(csv_path, schema_path)
            
            assert not is_valid
            assert len(errors) > 0
            assert any('Header order mismatch' in error for error in errors)
        finally:
            csv_path.unlink()

    def test_processor_schema_validation_success(self):
        """Test CsvProcessor validates schema successfully"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['set', 'type', 'period', 'name', 'url'])
            writer.writerow(['SV01', 'Card', '3M', 'Test Card', 'https://httpbin.org/json'])
            csv_path = Path(f.name)
        
        try:
            processor = CsvProcessor()
            # Should not raise exception
            processor._validate_input_schema(csv_path)
        finally:
            csv_path.unlink()

    def test_processor_schema_validation_failure(self):
        """Test CsvProcessor raises error on invalid schema"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['invalid', 'headers'])  # Wrong schema
            writer.writerow(['data1', 'data2'])
            csv_path = Path(f.name)
        
        try:
            processor = CsvProcessor()
            with pytest.raises(ValueError, match="Input schema validation failed"):
                processor._validate_input_schema(csv_path)
        finally:
            csv_path.unlink()

    def test_schema_file_loading(self):
        """Test schema file loading functionality"""
        schema_path = Path(__file__).parent.parent / 'schema' / 'input_v1.json'
        schema = FileHelper.load_schema(schema_path)
        
        assert schema is not None
        assert 'version' in schema
        assert 'fields' in schema
        assert 'header_order' in schema
        assert schema['version'] == '1.0'
        assert len(schema['fields']) == 5  # set, type, period, name, url

    def test_schema_file_not_found(self):
        """Test handling of missing schema file"""
        non_existent_path = Path('/non/existent/schema.json')
        schema = FileHelper.load_schema(non_existent_path)
        
        assert schema is None