import os
import pytest
import tempfile
from pathlib import Path
from typing import List, Dict
from unittest.mock import Mock

import requests_mock
# Using subprocess for CLI testing instead of typer
import subprocess

from common.processor import CsvProcessor
from common.web_client import WebClient
from common.markdown_parser import MarkdownParser
from common.csv_writer import CsvWriter
from common.logger import AppLogger


SAMPLE_CSV = """set,type,period,name,url
SV08.5,Card,3M,Umbreon ex 161,https://r.jina.ai/https://www.tcgplayer.com/product/610516/pokemon-sv-prismatic-evolutions-umbreon-ex-161-131?page=1&Language=English
SV08,Card,3M,Pikachu ex 238,https://r.jina.ai/https://www.tcgplayer.com/product/590027/pokemon-sv08-surging-sparks-pikachu-ex-238-191?page=1&Language=English
SV07,Card,3M,Squirtle 148,https://r.jina.ai/https://www.tcgplayer.com/product/567429/pokemon-sv07-stellar-crown-squirtle?page=1&Language=English"""

SAMPLE_MARKDOWN = """# Test Document

This is a **test** document with some _italic_ text.

## Features

- Feature 1
- Feature 2
- Feature 3

[Link to example](https://example.com)

```python
print("Hello World")
```

Some regular text at the end."""

SAMPLE_OUTPUT_CSV = """url,name,content
https://example.com/test1.md,Test Document 1,"Test Document

This is a test document with some italic text.

Features

Feature 1
Feature 2
Feature 3

Link to example

Some regular text at the end."
https://example.com/test2.md,Test Document 2,""
https://example.com/test3.md,Test Document 3,""
"""


@pytest.fixture
def sample_csv_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(SAMPLE_CSV)
        f.flush()
        yield Path(f.name)
    os.remove(f.name)


@pytest.fixture
def sample_output_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.flush()
        yield Path(f.name)
    if os.path.exists(f.name):
        os.remove(f.name)


@pytest.fixture
def sample_markdown_content():
    return SAMPLE_MARKDOWN


@pytest.fixture
def sample_csv_data():
    return [
        {'set': 'SV08.5', 'type': 'Card', 'period': '3M', 'name': 'Umbreon ex 161', 'url': 'https://r.jina.ai/https://www.tcgplayer.com/product/610516/pokemon-sv-prismatic-evolutions-umbreon-ex-161-131?page=1&Language=English'},
        {'set': 'SV08', 'type': 'Card', 'period': '3M', 'name': 'Pikachu ex 238', 'url': 'https://r.jina.ai/https://www.tcgplayer.com/product/590027/pokemon-sv08-surging-sparks-pikachu-ex-238-191?page=1&Language=English'},
        {'set': 'SV07', 'type': 'Card', 'period': '3M', 'name': 'Squirtle 148', 'url': 'https://r.jina.ai/https://www.tcgplayer.com/product/567429/pokemon-sv07-stellar-crown-squirtle?page=1&Language=English'}
    ]


# V2.0 Schema Test Data Fixtures

@pytest.fixture
def sample_v2_card_data():
    """Sample TCGPlayer card data in v2.0 format"""
    return [
        {
            'set': 'SV08.5',
            'type': 'Card',
            'period': '3M',
            'name': 'Test Card',
            'period_start_date': '2025-01-01',
            'period_end_date': '2025-01-03',
            'timestamp': '2025-07-24 15:00:00',
            'holofoil_price': 100.00,
            'volume': 0
        },
        {
            'set': 'SV08.5',
            'type': 'Card',
            'period': '3M',
            'name': 'Test Card',
            'period_start_date': '2025-01-04',
            'period_end_date': '2025-01-06',
            'timestamp': '2025-07-24 15:00:00',
            'holofoil_price': 105.00,
            'volume': 1
        },
        {
            'set': 'SV08.5',
            'type': 'Card',
            'period': '3M',
            'name': 'Test Card',
            'period_start_date': '2025-01-07',
            'period_end_date': '2025-01-09',
            'timestamp': '2025-07-24 15:00:00',
            'holofoil_price': 110.00,
            'volume': 2
        }
    ]


@pytest.fixture
def sample_v2_price_history():
    """Sample price history data in v2.0 format for TCGPlayer tests"""
    return [
        {
            'period_start_date': '2025-07-16',
            'period_end_date': '2025-07-18',
            'timestamp': '2025-07-24 15:00:00',
            'holofoil_price': 1200.00,
            'volume': 0
        },
        {
            'period_start_date': '2025-07-13',
            'period_end_date': '2025-07-15',
            'timestamp': '2025-07-24 15:00:00',
            'holofoil_price': 1150.00,
            'volume': 1
        },
        {
            'period_start_date': '2025-07-10',
            'period_end_date': '2025-07-12',
            'timestamp': '2025-07-24 15:00:00',
            'holofoil_price': 1100.00,
            'volume': 2
        }
    ]


@pytest.fixture
def sample_v2_single_record():
    """Single v2.0 format record for testing"""
    return {
        'set': 'SV08.5',
        'type': 'Card',
        'period': '3M',
        'name': 'Test Card',
        'period_start_date': '2025-01-01',
        'period_end_date': '2025-01-03',
        'timestamp': '2025-07-24 15:00:00',
        'holofoil_price': 100.00,
        'volume': 0
    }


@pytest.fixture
def sample_tcg_url_data():
    """Sample data with real TCGPlayer URL for processor tests"""
    return [{
        'set': 'SV08.5',
        'type': 'Card',
        'period': '3M',
        'name': 'Umbreon ex 161',
        'url': 'https://r.jina.ai/https://www.tcgplayer.com/product/610516/pokemon-sv-prismatic-evolutions-umbreon-ex-161-131?page=1&Language=English'
    }]


@pytest.fixture
def default_timestamp():
    """Standard timestamp for test data consistency"""
    return '2025-07-24 15:00:00'


@pytest.fixture
def csv_processor():
    # Initialize logging for tests
    logger = AppLogger()
    logger.setup_logging(verbose=True, log_file="test.log")
    return CsvProcessor()


@pytest.fixture
def web_client():
    return WebClient()


@pytest.fixture
def markdown_parser():
    return MarkdownParser()


@pytest.fixture
def csv_writer():
    return CsvWriter()


@pytest.fixture
def runner():
    """Simple test runner using subprocess for CLI testing"""
    class TestRunner:
        def invoke(self, main_func, args):
            """Mock invoke method for testing CLI commands"""
            import sys
            import io
            from contextlib import redirect_stdout, redirect_stderr

            # Capture stdout and stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            # Mock sys.argv
            original_argv = sys.argv
            sys.argv = ['main.py'] + args

            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    main_func()
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code
            except Exception as e:
                stderr_capture.write(str(e))
                exit_code = 1
            finally:
                sys.argv = original_argv

            # Create mock result
            class MockResult:
                def __init__(self, exit_code, stdout, stderr):
                    self.exit_code = exit_code
                    self.stdout = stdout
                    self.stderr = stderr

            return MockResult(exit_code, stdout_capture.getvalue(), stderr_capture.getvalue())

    return TestRunner()


@pytest.fixture
def mock_requests():
    import requests.exceptions
    with requests_mock.Mocker() as m:
        # Mock TCGPlayer URLs with sample content
        m.get('https://r.jina.ai/https://www.tcgplayer.com/product/610516/pokemon-sv-prismatic-evolutions-umbreon-ex-161-131?page=1&Language=English', text=SAMPLE_MARKDOWN)
        m.get('https://r.jina.ai/https://www.tcgplayer.com/product/590027/pokemon-sv08-surging-sparks-pikachu-ex-238-191?page=1&Language=English', status_code=404)
        m.get('https://r.jina.ai/https://www.tcgplayer.com/product/567429/pokemon-sv07-stellar-crown-squirtle?page=1&Language=English', exc=requests.exceptions.ConnectTimeout())
        yield m


# Coverage Analyzer Test Fixtures

@pytest.fixture
def sv_card_filter_config():
    """Standard SV* Card filter configuration"""
    return {"sets": "SV*", "types": "Card", "period": "3M"}


# Configuration Manager Test Fixtures

@pytest.fixture
def config_temp_file():
    """Temporary configuration file for ConfigurationManager tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def config_manager(config_temp_file):
    """ConfigurationManager instance with temporary file"""
    from common.configuration_manager import ConfigurationManager
    return ConfigurationManager(config_temp_file)


@pytest.fixture
def sample_filter_config():
    """Sample filter configuration for testing"""
    return {"sets": "SV*", "types": "Card", "period": "3M"}


@pytest.fixture
def sample_validation_metadata():
    """Sample validation metadata for configuration testing"""
    return {
        "coverage_percentage": 1.0,
        "signatures_found": 13,
        "signatures_total": 13,
        "optimal_start_date": "2025-04-28",
        "records_aligned": 1209,
        "time_series_points": 93
    }


@pytest.fixture
def existing_usage_stats():
    """Sample existing usage statistics for testing updates"""
    return {
        "created_at": "2025-07-29T10:00:00Z",
        "last_used": "2025-07-30T10:00:00Z",
        "use_count": 5
    }


@pytest.fixture
def mixed_generation_filter_config():
    """Mixed generation filter configuration for failure scenarios"""
    return {"sets": "SWSH*,SV*", "types": "Card", "period": "3M"}


@pytest.fixture
def invalid_filter_config():
    """Invalid filter configuration for testing edge cases"""
    return {"sets": "invalid", "types": "invalid", "period": "3M"}


@pytest.fixture
def successful_coverage_result_data():
    """Complete coverage result data (100% success scenario)"""
    return {
        "coverage_percentage": 1.0,
        "signatures_found": 13,
        "signatures_total": 13,
        "optimal_start_date": "2025-04-28",
        "records_before_start": 57,
        "records_aligned": 1209,
        "time_series_points": 93,
        "gap_fills_required": 50,
        "missing_signatures": [],
        "fallback_required": False,
        "quality_score": 1.0
    }


@pytest.fixture
def failed_coverage_result_data():
    """Failed coverage result data (0% coverage scenario)"""
    return {
        "coverage_percentage": 0.0,
        "signatures_found": 0,
        "signatures_total": 20,
        "optimal_start_date": None,
        "records_before_start": 0,
        "records_aligned": 0,
        "time_series_points": 0,
        "gap_fills_required": 0,
        "missing_signatures": ["SWSH06_Charizard_Card", "SV01_Pikachu_Card"],
        "fallback_required": False,
        "quality_score": 0.0
    }


@pytest.fixture
def partial_coverage_result_data():
    """Partial coverage result data (95% with fallback scenario)"""
    return {
        "coverage_percentage": 0.95,
        "signatures_found": 19,
        "signatures_total": 20,
        "optimal_start_date": "2025-04-28",
        "records_before_start": 67,
        "records_aligned": 1859,
        "time_series_points": 93,
        "gap_fills_required": 212,
        "missing_signatures": ["SWSH06_Charizard_Card"],
        "fallback_required": True,
        "quality_score": 0.85
    }


@pytest.fixture
def standard_coverage_result_data():
    """Standard coverage result data for general testing"""
    return {
        "coverage_percentage": 0.9,
        "signatures_found": 10,
        "signatures_total": 11,
        "optimal_start_date": "2025-04-28",
        "records_before_start": 50,
        "records_aligned": 1000,
        "time_series_points": 90,
        "gap_fills_required": 25,
        "missing_signatures": ["SV10_Missing_Card"],
        "fallback_required": False,
        "quality_score": 0.88
    }


@pytest.fixture
def alternative_suggestion_result_data():
    """Coverage result data for alternative suggestion scenarios"""
    return {
        "coverage_percentage": 0.92,
        "signatures_found": 12,
        "signatures_total": 13,
        "optimal_start_date": "2025-04-28",
        "records_before_start": 43,
        "records_aligned": 1156,
        "time_series_points": 93,
        "gap_fills_required": 74,
        "missing_signatures": ["SV10_MissingCard_Card"],
        "fallback_required": False,
        "quality_score": 0.89
    }


@pytest.fixture
def successful_coverage_result(sv_card_filter_config, successful_coverage_result_data):
    """Complete CoverageResult fixture for successful analysis"""
    from common.coverage_analyzer import CoverageResult
    return CoverageResult(
        filter_config=sv_card_filter_config,
        **successful_coverage_result_data
    )


@pytest.fixture
def failed_coverage_result(mixed_generation_filter_config, failed_coverage_result_data):
    """Complete CoverageResult fixture for failed analysis"""
    from common.coverage_analyzer import CoverageResult
    return CoverageResult(
        filter_config=mixed_generation_filter_config,
        **failed_coverage_result_data
    )


@pytest.fixture
def partial_coverage_result(mixed_generation_filter_config, partial_coverage_result_data):
    """Complete CoverageResult fixture for partial coverage analysis"""
    from common.coverage_analyzer import CoverageResult
    return CoverageResult(
        filter_config=mixed_generation_filter_config,
        **partial_coverage_result_data
    )


@pytest.fixture
def standard_coverage_result(sv_card_filter_config, standard_coverage_result_data):
    """Complete CoverageResult fixture for standard testing"""
    from common.coverage_analyzer import CoverageResult
    return CoverageResult(
        filter_config=sv_card_filter_config,
        **standard_coverage_result_data
    )


@pytest.fixture
def successful_recommendation_result(sv_card_filter_config, successful_coverage_result):
    """Complete RecommendationResult fixture for successful recommendation"""
    from common.coverage_analyzer import RecommendationResult
    return RecommendationResult(
        rank=1,
        filter_config=sv_card_filter_config,
        coverage_result=successful_coverage_result,
        description="SV Cards (Complete)",
        command_string='--sets "SV*" --types "Card" --period "3M"',
        estimated_records=1209
    )


@pytest.fixture
def fallback_recommendation_result(mixed_generation_filter_config, partial_coverage_result):
    """Complete RecommendationResult fixture for fallback recommendation"""
    from common.coverage_analyzer import RecommendationResult
    return RecommendationResult(
        rank=2,
        filter_config=mixed_generation_filter_config,
        coverage_result=partial_coverage_result,
        description="SWSH/SV Cards (Excellent)",
        command_string='--sets "SWSH*,SV*" --types "Card" --period "3M" --allow-fallback',
        estimated_records=1859
    )


@pytest.fixture
def coverage_analyzer_dependencies():
    """Mock dependencies for CoverageAnalyzer testing"""
    from chart.index_aggregator import IndexAggregator, FilterValidator
    from common.time_series_aligner import TimeSeriesAligner

    return {
        "aggregator": IndexAggregator(),
        "aligner": TimeSeriesAligner(),
        "validator": FilterValidator()
    }