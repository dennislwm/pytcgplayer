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