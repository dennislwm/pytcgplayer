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


SAMPLE_CSV = """url,name
https://example.com/test1.md,Test Document 1
https://example.com/test2.md,Test Document 2
https://example.com/test3.md,Test Document 3"""

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
        {'url': 'https://example.com/test1.md', 'name': 'Test Document 1'},
        {'url': 'https://example.com/test2.md', 'name': 'Test Document 2'},
        {'url': 'https://example.com/test3.md', 'name': 'Test Document 3'}
    ]


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
        m.get('https://example.com/test1.md', text=SAMPLE_MARKDOWN)
        m.get('https://example.com/test2.md', status_code=404)
        m.get('https://example.com/test3.md', exc=requests.exceptions.ConnectTimeout())
        yield m