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
make run_ci              # Run app for CI/workflows (no env checks)
make help_app           # Show CLI help

# Testing
make test               # Run all unit tests
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
$ PYTHONPATH=. pipenv run python main.py data/input.csv data/output.csv --verbose
# Processes 30 price history records, outputs to data/output.csv
```

**Input CSV format (TCGPlayer data):**
```csv
set,type,period,name,url
SV08.5,Card,3M,Umbreon ex 161,https://r.jina.ai/https://www.tcgplayer.com/product/610516/pokemon-sv-prismatic-evolutions-umbreon-ex-161-131?page=1&Language=English
```

**Output CSV format (Normalized price history):**
```csv
set,type,period,name,date,holofoil_price,volume
SV08.5,Card,3M,Umbreon ex 161,4/20 to 4/22,"$1,451.66",0
SV08.5,Card,3M,Umbreon ex 161,4/23 to 4/25,"$1,451.66",0
SV08.5,Card,3M,Umbreon ex 161,4/26 to 4/28,"$1,451.66",0
...
```

### Make Commands Workflow

**Quick Start Workflow:**
```bash
# 1. Setup environment and dependencies
make pipenv_new && make install_deps

# 2. Create input data and run application with verbose output
make sample && make run_verbose

# 3. Run comprehensive test suite
make test

# 4. Run demo scripts to see full functionality
make demo

# 5. View all available commands
make help
```

**Development Workflow:**
```bash
# Daily development cycle
make                    # Activate environment
make sample            # Create fresh input data (data/input.csv)
make run_verbose       # Test application with logging (outputs to data/output.csv)
make test             # Verify all tests pass
make demo             # Run demonstration scripts
```

**Command Categories:**

1. **Environment Management**: `pipenv_new`, `install_deps`, `pipenv_shell`
2. **Application Execution**: `run`, `run_verbose`, `help_app`, `sample`  
3. **Testing & Quality**: `test`, `test_verbose`
4. **Demo & Examples**: `demo`, `demo_clean`
5. **Utilities**: `pipenv_freeze`, `check_json`, `pipenv_venv`, `help`

## Code Quality Standards

**CRITICAL: Always prioritize code size reduction and reusability when making any code changes or implementing new features.**

### Code Size Reduction Requirements

**Before implementing any new code or making changes:**

1. **Check for existing helpers in `common/helpers.py`**:
   - `FileHelper` for CSV file operations
   - `RetryHelper` for exponential backoff retry logic
   - `DataProcessor` mixin for common data processing methods

2. **Always prefer one-liners and concise implementations**:
   - Combine argument parser declarations
   - Use list comprehensions over loops where possible
   - Leverage lambda functions for simple transformations
   - Consolidate regex operations

3. **Create reusable helper classes for repeated patterns**:
   - Extract common functionality into mixins
   - Use decorators for cross-cutting concerns (retry, logging)
   - Centralize file operations and data processing logic

4. **Inheritance and composition over duplication**:
   - Inherit from `DataProcessor` for data manipulation classes
   - Use helper classes instead of duplicating methods
   - Share common patterns across modules

**Code size reduction achieved**: ~120 lines (15% reduction) through systematic refactoring.

### Mandatory Code Review Checklist

Before any code submission:
- [ ] Checked if functionality exists in helper classes
- [ ] Eliminated duplicate methods/logic
- [ ] Used one-liners where appropriate
- [ ] Created reusable helpers for new patterns
- [ ] Maintained or reduced total line count
- [ ] All tests pass

## CSV Schema Management

The application includes comprehensive CSV schema validation and tracking:

### Schema Files
- `app/schema/input_v1.json` - Input CSV schema definition
- `app/schema/output_v1.json` - Output CSV schema definition

### Input Schema (v1.0)
```csv
set,type,period,name,url
```
- **set**: Trading card set identifier (e.g., SV01, SWSH06)
- **type**: Card type classification  
- **period**: Time period for price data (e.g., 3M)
- **name**: Card name and identifier
- **url**: TCGPlayer URL via Jina.ai markdown service

### Output Schema (v1.0)
```csv
set,type,period,name,date,holofoil_price,volume
```
- Inherits: set, type, period, name from input
- **date**: Date range for price data (e.g., "4/20 to 4/22")
- **holofoil_price**: Price in currency format (e.g., "$49.73")
- **volume**: Trading volume as integer (converted from currency strings)

### Schema Validation
- **Automatic validation**: Input files validated against schema on processing
- **Error handling**: Processing fails with clear error message if schema invalid
- **Change detection**: Logs warnings for schema mismatches (missing, extra, reordered headers)
- **Version tracking**: Schema versions tracked in JSON with changelog

### Testing Coverage
- Schema validation tests in `tests/schema_test.py`
- Tests cover valid schemas, missing headers, extra headers, wrong order
- Integration tests with CsvProcessor validation

## Development Patterns

Based on analysis of similar projects in the workspace (`13pynlb`, `13pyledger`, `13pyviki`):

### Project Structure
```
app/
├── main.py                  # CLI entry point
├── common/                  # Core modules (processor, web_client, csv_writer, etc.)
├── tests/                   # Unit tests
├── demo/                    # Demo scripts and sample files
├── data/                    # Input/output CSV files
└── logs/                    # Generated log files
```

### Testing Requirements
- **Test Suite**: Comprehensive unit tests with 100% pass rate
- **Coverage**: All modules tested (CsvProcessor, WebClient, MarkdownParser, CsvWriter, Main CLI)
- **Framework**: pytest with centralized logging via AppLogger
- **Execution**: `PYTHONPATH=.` set for proper module imports
- **Logging**: Test logs written to `logs/test.log` with DEBUG level
- **Setup**: Each test class initializes logging in `setup_class()` method
- **Mocking**: Uses `requests-mock` for HTTP request testing
- **Data Format**: Tests updated to expect `volume` column with integer values instead of `additional_price` currency strings

### Windows Testing Notes
- **Directory Navigation**: Tests must run from `pytcgplayer/app` directory due to Windows path handling
- **Command Execution**: Use `cd pytcgplayer/app && PYTHONPATH=. pipenv run pytest tests/` for manual test runs
- **Pipenv Warnings**: Windows may show pipenv virtual environment warnings (can be suppressed with `PIPENV_VERBOSITY=-1`)
- **Path Separators**: Test output shows Windows backslash paths (`tests\csv_processor_test.py`) which is normal
- **Make Commands**: All `make test` commands work correctly on Windows when run from project root

### Dependencies
Current dependencies (automatically managed by pipenv):
- `requests==2.32.4` for HTTP requests with rate limiting and retry logic
- `pytest==8.4.1` for testing framework
- `requests-mock==1.12.1` for HTTP request mocking in tests
- `typer==0.16.0` for CLI development (future enhancement)
- Additional dependencies for future features:
  - `check-jsonschema==0.23.0` for config validation  
  - `pyyaml==6.0.1` for YAML configuration handling

**Installation**: Use `make install_deps` or `pipenv install requests pytest requests-mock typer`

### Helper Classes Architecture

The codebase includes reusable helper classes in `common/helpers.py`:

**FileHelper**:
- `read_csv(path)` - Read CSV files with error handling
- `write_csv(data, path)` - Write CSV files with proper formatting

**RetryHelper**:
- `@with_exponential_backoff(max_retries, base_delay)` - Decorator for retry logic with exponential backoff and jitter

**DataProcessor** (Mixin):
- `create_key(row, columns)` - Generate unique keys from row data
- `create_key_index(data, key_columns)` - Create index mapping for efficient lookups  
- `normalize_row(source, schema)` - Transform row data according to schema
- `convert_currency_to_int(currency_str)` - Parse currency strings to integers

**Usage Example**:
```python
from common.helpers import FileHelper, RetryHelper, DataProcessor

class MyProcessor(DataProcessor):
    @RetryHelper.with_exponential_backoff(max_retries=3)
    def process_data(self):
        data = FileHelper.read_csv(self.input_path)
        # Process using inherited DataProcessor methods
        return self.normalize_row(data[0], schema)
```

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

Use `source make.sh && check_env` to validate all required CLI tools:
- `gh` - GitHub CLI for repository and workflow management
- `python` - Python 3.13 interpreter
- `pipenv` - Python dependency management
- `shellcheck` - Shell script linting

## GitHub CLI Integration

The project includes GitHub CLI (`gh`) for repository management and automation:

### Common GitHub CLI Commands

```bash
# Repository management
gh repo view                    # View current repository details
gh repo clone <repo>           # Clone a repository
gh repo create <name>          # Create new repository

# Workflow management  
gh workflow list               # List all workflows
gh workflow view <workflow>    # View workflow details
gh workflow run <workflow>     # Trigger workflow manually
gh run list                    # List recent workflow runs
gh run view <run-id>          # View specific run details

# Pull request management
gh pr create                   # Create new pull request
gh pr list                     # List pull requests
gh pr view <number>           # View PR details
gh pr checkout <number>       # Checkout PR locally

# Issue management
gh issue create               # Create new issue
gh issue list                 # List issues
gh issue view <number>        # View issue details

# Authentication
gh auth login                 # Login to GitHub
gh auth status               # Check authentication status
```

### Workflow Integration

The project includes automated workflows in `.github/workflows/`:

**Daily TCG Data Collection** (`daily-tcg-data.yml`):
- Runs daily at 6:00 AM UTC via cron schedule
- Executes `make run_ci` to collect price data (bypasses environment checks for CI)
- Commits and pushes only if `app/data/output.csv` changes
- Manual trigger available via `gh workflow run "Daily TCG Data Collection"`

**Manual workflow execution**:
```bash
# Trigger daily data collection manually
gh workflow run "Daily TCG Data Collection"

# View recent runs
gh run list --workflow="Daily TCG Data Collection"

# View specific run details
gh run view <run-id> --log
```

## Demo Scripts and Examples

The `app/demo/` directory contains demonstrations:

1. **Price History Extraction** - Extracts 30+ price records from TCGPlayer data
2. **Idempotent Functionality** - Proves safe repeated execution with duplicate detection

```bash
cd app/demo
python3 demo_price_extraction.py
python3 demo_idempotent.py
```

### Data Organization

The application now uses a centralized data directory structure:

**Input Data (`data/input.csv`):**
- Contains TCGPlayer URLs with metadata (set, type, period, name)
- Created automatically with `make sample`
- Tracks multiple trading cards or products

**Output Data (`data/output.csv`):**
- Normalized price history with one row per price record
- Includes all original metadata plus extracted price data
- `volume` column contains integer values (converted from currency strings like "$1.00" → 1)
- Generated with idempotent duplicate prevention
- Safe for repeated processing and automation

**Data Workflow:**
```bash
# Create fresh input data
make sample                     # Creates data/input.csv

# Process and generate output  
make run_verbose               # Processes data/input.csv → data/output.csv

# Verify idempotent behavior
make run                       # Re-running detects duplicates, no new data added
```

## Rate Limiting and Error Handling

The application includes robust rate limiting and retry logic to handle API limitations:

### **WebClient Rate Limiting Features**

**Built-in Rate Limiting:**
- **Base Delay**: 1-second delay between all requests to respect API limits
- **429 Error Detection**: Automatically detects rate limiting responses
- **Exponential Backoff**: Progressive delays (1s → 2s → 4s) with random jitter
- **Configurable Retries**: Default 3 attempts, customizable via constructor

**Usage and Configuration:**
```python
# Default configuration (recommended)
client = WebClient()  # 30s timeout, 3 retries, 1s base delay

# Custom configuration for high-volume processing
client = WebClient(
    timeout=60,          # Longer timeout for slow responses
    max_retries=5,       # More retry attempts
    base_delay=2.0       # Longer delay between requests
)
```

**Retry Behavior:**
- **Normal Request**: 1s delay → make request → return result
- **429 Rate Limited**: 1s delay → 429 error → wait 2s → retry → wait 4s → retry → fail if still limited
- **Network Errors**: Same exponential backoff for connection issues
- **Other HTTP Errors**: Immediate failure (no retries for 404, 500, etc.)

**Logging Output:**
```
2025-07-20 19:53:27 - common.web_client - WARNING - Rate limited (429), retrying... (attempt 1)
2025-07-20 19:53:27 - common.web_client - INFO - Retrying in 2.3s (attempt 2/3)
```

### **CSV Writer Update Behavior**

**Duplicate Handling Strategy:**
- **Before**: Skip duplicate records entirely
- **Now**: Update existing records with new price data
- **Benefits**: Perfect for continuous price monitoring and data refreshing

**Update Logic:**
- Identifies duplicates using fingerprint: `(set, type, period, name, date)`
- Updates only `holofoil_price` and `volume` fields
- Preserves all metadata and historical structure
- Logs both update count and new record count

**Example Behavior:**
```bash
# First run
Updated 0 existing records, adding 390 new records

# Subsequent run with updated prices
Updated 390 existing records, adding 0 new records

# Mixed scenario (some new dates, some updated prices)  
Updated 350 existing records, adding 40 new records
```

## Performance Notes

Current performance characteristics:
- **Sequential HTTP**: ~1 second per URL with rate limiting
- **Suitable for**: Manual runs, small-medium datasets
- **Limitations**: Large batch processing
- **Code Size**: ~120 lines reduced (15% reduction) through helper classes and one-liners

**Code optimization achievements**:
1. **FileHelper class**: Eliminated duplicate CSV operations across modules
2. **RetryHelper decorator**: Consolidated retry logic with exponential backoff
3. **DataProcessor mixin**: Shared common data processing methods
4. **One-liner implementations**: Streamlined argument parsing and simple operations

**Future optimization opportunities**:
1. Async HTTP requests for concurrent processing
2. Streaming CSV I/O for large datasets
3. Further code consolidation through additional helper classes

## Codebase Analysis with llm CLI

For analyzing large codebases that exceed context limits:

```bash
# Analyze architecture
llm "Here is Python code: $(cat main.py common/processor.py | head -300)
Summarize the architecture"

# Review configuration
llm "Here are config files: $(cat Makefile make.sh ../CLAUDE.md | head -100)
Review the project setup"

# Performance analysis
llm "Here is the codebase: $(cat common/*.py | head -500)
Identify performance bottlenecks"
```

## Git Commit Message Generation

Generate conventional commit messages using llm CLI:

```bash
# Generate from unstaged changes
llm "Generate a conventional commit message in one line for: $(git diff HEAD)"

# Generate from staged changes
llm "Generate a conventional commit message in one line for: $(git diff --cached)"
```

Standard format: `type: description` (fix, feat, docs, style, refactor, test, chore)

**IMPORTANT**: When committing code changes, always mention code size reduction efforts in commit messages. Examples:
- `refactor: consolidate CSV operations into FileHelper class (-50 lines)`
- `feat: add retry decorator helper class for reusable retry logic`
- `style: convert multi-line argument parser to one-liners (-15 lines)`