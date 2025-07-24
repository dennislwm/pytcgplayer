# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI application for processing TCGPlayer trading card price data. The application reads TCGPlayer URLs from CSV files, fetches price history data from those URLs, parses markdown price tables, and outputs normalized price data to CSV files in schema v2.0 format with numeric types for efficient analysis and time series charting.

## Development Setup

### Quick Start
```bash
make pipenv_new && make install_deps  # Setup environment
make sample && make run_verbose       # Create test data and run
make test                             # Run all tests
make convert_schema                   # Convert v1.0 to v2.0 format
```

### Key Commands
```bash
# Environment: pipenv_new, install_deps, pipenv_shell
# Application: run, run_verbose, run_ci, sample, help_app
# Testing: test, test_verbose
# Schema: convert_schema
# Utilities: pipenv_freeze, check_json, help
```

### Sample Usage and Output

**Input CSV format (TCGPlayer URLs only):**
```csv
set,type,period,name,url
SV08.5,Card,3M,Umbreon ex 161,https://r.jina.ai/https://www.tcgplayer.com/product/610516/pokemon-sv-prismatic-evolutions-umbreon-ex-161-131?page=1&Language=English
```

**Command execution:**
```bash
$ PYTHONPATH=. pipenv run python main.py data/input.csv data/output.csv --verbose
# Processes 30 price history records, outputs to data/output.csv
```

**Output CSV format (Schema v2.0 - Normalized price history):**
```csv
set,type,period,name,period_start_date,period_end_date,timestamp,holofoil_price,volume
SV08.5,Card,3M,Umbreon ex 161,2025-04-20,2025-04-22,2025-07-24 15:00:00,1451.66,0
SV08.5,Card,3M,Umbreon ex 161,2025-04-23,2025-04-25,2025-07-24 15:00:00,1451.66,0
SV08.5,Card,3M,Umbreon ex 161,2025-04-26,2025-04-28,2025-07-24 15:00:00,1451.66,0
...
```

## Code Quality Standards

**CRITICAL: Always prioritize code size reduction and reusability.**

Use existing helpers in `common/helpers.py`: `FileHelper`, `RetryHelper`, `DataProcessor`. Prefer one-liners, list comprehensions, and reusable classes. Achieved ~120 lines reduction (15%) through systematic refactoring.

## CSV Schema Management

The application uses schema v2.0 format with numeric types for efficient analysis and time series charting:

### Schema Files
- `app/schema/input_v1.json` - Input CSV schema definition
- `app/schema/output_v2.json` - Output CSV schema definition (v2.0 format)

### Input Schema (v1.0)
```csv
set,type,period,name,url
```
- **set**: Trading card set identifier (e.g., SV01, SWSH06)
- **type**: Card type classification
- **period**: Time period for price data (e.g., 3M)
- **name**: Card name and identifier
- **url**: TCGPlayer URL via Jina.ai markdown service

### Output Schema (v2.0) - Current Format
```csv
set,type,period,name,period_start_date,period_end_date,timestamp,holofoil_price,volume
```
- Inherits: set, type, period, name from input
- **period_start_date**: Start date in YYYY-MM-DD format (e.g., "2025-04-20")
- **period_end_date**: End date in YYYY-MM-DD format (e.g., "2025-04-22")
- **timestamp**: Data collection timestamp in YYYY-MM-DD HH:MM:SS format
- **holofoil_price**: Price as numeric decimal (e.g., 49.73) for calculations
- **volume**: Trading volume as integer (e.g., 12) for aggregations

### Schema Migration
```bash
# Convert existing v1.0 data to v2.0 format
make convert_schema
```
The schema converter automatically:
- Parses date ranges ("4/20 to 4/22") into separate start/end dates
- Converts currency strings ("$49.73") to numeric values (49.73)
- Converts volume strings ("12") to integers (12)
- Adds collection timestamps for data tracking

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

### Helper Classes

`common/helpers.py` includes: `FileHelper` (CSV I/O), `RetryHelper` (exponential backoff), `DataProcessor` (currency conversion, date parsing, key generation). Use `snake_case` for files/functions, `PascalCase` for classes.

## Centralized Logging

Singleton `AppLogger` class: dual output (console + file), logs to `logs/app.log` and `logs/test.log`. Use `AppLogger.get_logger(__name__)` in classes.

## Environment & GitHub Integration

Required tools: `gh`, `python`, `pipenv`, `shellcheck`. Daily workflow runs `make run_ci` at 6AM UTC for automated data collection. Use `gh workflow run "Daily TCG Data Collection"` for manual triggers.

## Data & Demo

`app/demo/` contains price extraction and idempotent demos. `data/input.csv` has TCGPlayer URLs (created via `make sample`), `data/output.csv` stores normalized price history with duplicate prevention. Safe for repeated processing.

## Rate Limiting and Error Handling

The application includes robust rate limiting and retry logic to handle API limitations:

### **Flexible Table Format Support**

**Multiple Table Format Detection:**
- **Primary Format**: `| Date | Holofoil |` - Standard TCGPlayer format for individual cards
- **Alternative Format**: `| Date | Normal |` - Format used for booster boxes and some products
- **Automatic Fallback**: MarkdownParser tries Holofoil format first, then Normal format
- **Consistent Processing**: Both formats parsed into identical v2.0 schema output

**Detection Logic:**
```python
# Try original format first (Date | Holofoil)
holofoil_pattern = r'\|\s*Date\s*\|\s*Holofoil\s*\|.*?(?=\n\n|\n(?!\|)|\Z)'
# Fallback to alternative format (Date | Normal)
normal_pattern = r'\|\s*Date\s*\|\s*Normal\s*\|.*?(?=\n\n|\n(?!\|)|\Z)'
```

**Logging Output:**
```
Found 'Date | Holofoil' format table    # Individual cards
Found 'Date | Normal' format table      # Booster boxes
```

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

## Storage Scalability and Future Enhancements

### Current Storage Analysis

The application currently uses CSV format for data storage with the following characteristics:
- **Current growth rate**: ~15.5 records/day (1,266 bytes/day)
- **File size**: 115KB for 93 days of data (1,437 records)
- **Record size**: ~82 bytes per record
- **Projected growth**: 10MB in ~22.4 years at current rate

### SQLite Migration for High-Volume Data

**Target Scenario**: 300 records/day (19.4x current growth rate)
- **Timeline to 10MB**: ~1.2 years (vs 22.4 years with CSV)
- **Timeline to 100MB**: ~11.7 years (vs 226.5 years with CSV)

**Recommended Enhancement: SQLite + Compression**

**Benefits**:
- **Storage efficiency**: 40-60 bytes/record (27-51% space savings vs CSV)
- **Query performance**: Fast date range queries with indexed columns
- **Data integrity**: ACID transactions and constraint validation
- **Concurrent access**: Multiple readers, single writer support
- **Built-in compression**: SQLite VACUUM and page compression
- **No external dependencies**: Uses Python's built-in `sqlite3` module

**Implementation Strategy**:
```python
# Database schema design
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name TEXT NOT NULL,
    card_type TEXT NOT NULL,
    period TEXT NOT NULL,
    name TEXT NOT NULL,
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    timestamp DATETIME NOT NULL,
    holofoil_price DECIMAL(10,2) NOT NULL,
    volume INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

# Indexes for fast queries
CREATE INDEX idx_date_range ON price_history(period_start_date, period_end_date);
CREATE INDEX idx_card_lookup ON price_history(set_name, name, period);
CREATE INDEX idx_timestamp ON price_history(timestamp);
```

**Migration Path**:
1. **Phase 1**: Add SQLite writer alongside CSV (dual output)
2. **Phase 2**: Implement SQLite reader with backwards compatibility
3. **Phase 3**: Migrate existing CSV data using conversion utility
4. **Phase 4**: Deprecate CSV format, SQLite becomes primary storage

**Alternative Storage Formats** (for higher volumes):
- **Parquet**: 15-25 bytes/record, excellent for analytics (70-82% savings)
- **CSV + gzip**: 28 bytes/record, minimal changes (66% savings)
- **Time-series databases**: InfluxDB/TimescaleDB for enterprise scale

**Trigger Conditions for Migration**:
- Data collection exceeds 100 records/day consistently
- File size approaches 5-10MB
- Need for complex date range queries increases
- Multiple concurrent data access patterns emerge

This enhancement maintains the current CSV simplicity while providing a clear upgrade path for production workloads.

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