# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI application for processing CSV data with web requests and markdown parsing. The application reads URLs from CSV files, fetches markdown content from those URLs, parses the content, and outputs the results to a new CSV file.

## Development Setup

### Environment Management
```bash
# Create new pipenv environment with Python 3.13
make pipenv_new

# Install dependencies (automatically installs requests and pytest)
pipenv install requests pytest

# Activate virtual environment (may fail in non-interactive environments)
make pipenv_shell

# Alternative: Run commands in virtual environment
pipenv run <command>

# Show virtual environment path
make pipenv_venv
```

### Common Commands

```bash
# Environment setup
make pipenv_new          # Create Python 3.13 environment
make install_deps        # Install current dependencies  
make pipenv_shell        # Activate environment (default target)
make                     # Same as pipenv_shell

# Development workflow
make sample              # Create sample.csv for testing
make run                 # Run app with sample data
make run_verbose         # Run app with debug logging
make help_app           # Show CLI help

# Testing (requires TCGPLAYER_API_TOKEN environment variable)
make test               # Run all 50 unit tests
make test_verbose       # Run tests with detailed output

# Utilities
make pipenv_freeze      # Generate requirements.txt with current versions
make check_json         # Validate JSON schemas (when config files exist)
make pipenv_venv        # Show virtual environment path
```

### Running the Application

```bash
# Show CLI help
pipenv run python main.py --help

# Process CSV file with web requests and markdown parsing
pipenv run python main.py input.csv output.csv

# Enable verbose logging (shows DEBUG level messages)
pipenv run python main.py input.csv output.csv --verbose

# Example with test data
pipenv run python main.py sample.csv output.csv --verbose
```

### Sample Usage and Output

**Input CSV format:**
```csv
url,name
https://httpbin.org/json,Test JSON API
https://httpbin.org/html,Test HTML Page
```

**Command execution:**
```bash
$ pipenv run python main.py sample.csv output.csv --verbose
2025-07-20 11:50:26 - common.processor - INFO - [processor.py:18] - Processing file: sample.csv
2025-07-20 11:50:26 - common.processor - INFO - [processor.py:26] - Reading CSV file: sample.csv
2025-07-20 11:50:26 - common.processor - INFO - [processor.py:32] - Read 2 rows
2025-07-20 11:50:26 - common.processor - INFO - [processor.py:36] - Processing rows...
2025-07-20 11:50:27 - common.csv_writer - INFO - [csv_writer.py:26] - Successfully wrote CSV file: output.csv
2025-07-20 11:50:27 - __main__ - INFO - [main.py:52] - Processing complete. Output saved to: output.csv
```

**Output CSV format:**
```csv
url,name,content
https://httpbin.org/json,Test JSON API,"{ ""slideshow"": { ""author"": ""Yours Truly"", ... }}"
https://httpbin.org/html,Test HTML Page,"<html><head><title>Herman Melville - Moby-Dick</title>..."
```

### Make Commands Workflow

**Quick Start Workflow:**
```bash
# 1. Setup environment and dependencies
make pipenv_new && make install_deps

# 2. Create test data and run application  
make sample && make run_verbose

# 3. Run comprehensive test suite
make test

# 4. View application help
make help_app
```

**Development Workflow:**
```bash
# Daily development cycle
make                    # Activate environment
make sample            # Create fresh test data
make run_verbose       # Test application with logging
make test             # Verify all tests pass (50/50)
```

**Command Categories:**

1. **Environment Management**: `pipenv_new`, `install_deps`, `pipenv_shell`
2. **Application Execution**: `run`, `run_verbose`, `help_app`, `sample`  
3. **Testing & Quality**: `test`, `test_verbose`
4. **Utilities**: `pipenv_freeze`, `check_json`, `pipenv_venv`

## Development Patterns

Based on analysis of similar projects in the workspace (`13pynlb`, `13pyledger`, `13pyviki`):

### Project Structure
```
13pytcgplayer/
├── CLAUDE.md                    # Project documentation and instructions
├── README.md                    # Project overview
└── app/                         # Main application directory
    ├── Makefile                 # Development commands
    ├── make.sh                  # Environment validation script
    ├── main.py                  # CLI entry point
    ├── common/                  # Shared modules and utilities
    │   ├── __init__.py          # Common package initializer
    │   ├── processor.py         # CsvProcessor class for processing CSV data
    │   ├── csv_writer.py        # CsvWriter class for CSV output
    │   ├── web_client.py        # WebClient class for HTTP requests
    │   ├── markdown_parser.py   # MarkdownParser class for markdown content processing
    │   └── logger.py            # AppLogger class for centralized logging
    ├── tests/                   # Unit tests with pytest
    │   ├── conftest.py          # Test fixtures and configuration
    │   ├── csv_processor_test.py    # Tests for CsvProcessor
    │   ├── csv_writer_test.py       # Tests for CsvWriter
    │   ├── web_client_test.py       # Tests for WebClient
    │   ├── markdown_parser_test.py  # Tests for MarkdownParser
    │   └── main_test.py             # Tests for CLI main function
    └── logs/                    # Generated log files (created automatically)
        ├── app.log              # Application execution logs
        └── test.log             # Test execution logs
```

### Key Files and Directories
- **Root Level**: Project documentation and configuration
- **app/**: All application code and development tools
- **app/common/**: Reusable modules following single responsibility principle
- **app/tests/**: Comprehensive unit tests matching the 13pyledger pattern
- **logs/**: Auto-generated directory for centralized logging output

### Testing Requirements
- **Test Suite**: 50 comprehensive unit tests with 100% pass rate
- **Coverage**: All modules tested (CsvProcessor, WebClient, MarkdownParser, CsvWriter, Main CLI)
- **Environment**: Requires `TCGPLAYER_API_TOKEN` environment variable
- **Framework**: pytest with centralized logging via AppLogger
- **Execution**: `PYTHONPATH=.` set for proper module imports
- **Logging**: Test logs written to `logs/test.log` with DEBUG level
- **Setup**: Each test class initializes logging in `setup_class()` method
- **Mocking**: Uses `requests-mock` for HTTP request testing

### Dependencies
Current dependencies (automatically managed by pipenv):
- `requests==2.32.4` for HTTP requests
- `pytest==8.4.1` for testing framework
- `requests-mock==1.12.1` for HTTP request mocking in tests
- `typer==0.16.0` for CLI development (future enhancement)
- Additional dependencies for future features:
  - `check-jsonschema==0.23.0` for config validation  
  - `pyyaml==6.0.1` for YAML configuration handling

**Installation**: Use `make install_deps` or `pipenv install requests pytest requests-mock typer`

## Python Naming Standards

Follow these naming conventions for scalable code:

### Files and Modules
- Use `snake_case` for file names: `markdown_parser.py`, `csv_writer.py`

### Classes
- Use `PascalCase` for class names: `CsvProcessor`, `MarkdownParser`, `WebClient`

### Variables and Functions
- Use `snake_case` for variables and functions: `input_file`, `process_rows()`, `markdown_parser`

### Constants
- Use `UPPER_SNAKE_CASE` for constants: `DEFAULT_TIMEOUT`, `API_BASE_URL`

## Centralized Logging

The application uses a centralized logging system via the `AppLogger` class:

### Implementation
- **Singleton Pattern**: Single `AppLogger` instance manages all logging across modules
- **Dual Output**: Console (respects verbosity) and file (always DEBUG level)
- **Common Log Files**: 
  - `logs/app.log` for application execution
  - `logs/test.log` for test execution
- **Structured Format**: `timestamp - module - level - [file:line] - message`

### Usage in Code
```python
from common.logger import AppLogger

# Initialize logging (typically in main.py or test setup)
logger = AppLogger()
logger.setup_logging(verbose=True, log_file="app.log")

# Get logger for module
class MyClass:
    def __init__(self):
        self.logger = AppLogger.get_logger(__name__)
        self.logger.info("Class initialized")
```

### Usage in Tests
```python
class TestMyClass:
    @classmethod
    def setup_class(cls):
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")
        cls.logger = AppLogger.get_logger(__name__)
```

## Environment Variables

The application requires:
- `TCGPLAYER_API_TOKEN` environment variable for API access
- Use `source make.sh && check_env` to validate all required environment variables and CLI tools

## Large Codebase Analysis

When analyzing large codebases or multiple files that might exceed context limits, use the Gemini CLI command:

```bash
# Analyze codebase architecture
gemini -p "@src/ Summarize the architecture of this code base"

# Analyze specific patterns or functionality
gemini -p "@app/ @tests/ Analyze the testing patterns and coverage"

# Review configuration and setup files
gemini -p "@*.yml @*.json @Makefile Review the project configuration"
```

This approach is particularly useful for:
- Understanding complex multi-file architectures
- Analyzing large test suites
- Reviewing configuration across multiple files
- Getting high-level summaries without hitting context limits