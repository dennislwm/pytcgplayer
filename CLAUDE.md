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
$ PYTHONPATH=. pipenv run python main.py data/input.csv data/output.csv --verbose
2025-07-20 18:28:00 - common.processor - INFO - [processor.py:18] - Processing file: data/input.csv
2025-07-20 18:28:00 - common.processor - INFO - [processor.py:26] - Reading CSV file: data/input.csv
2025-07-20 18:28:00 - common.processor - INFO - [processor.py:40] - Read 1 rows
2025-07-20 18:28:00 - common.processor - INFO - [processor.py:44] - Processing rows...
2025-07-20 18:28:00 - common.processor - INFO - [processor.py:62] - Extracted 30 price history records for row 1
2025-07-20 18:28:00 - common.processor - INFO - [processor.py:94] - Processed 30 rows
2025-07-20 18:28:00 - common.csv_writer - INFO - [csv_writer.py:30] - Writing 30 rows to data/output.csv (checking for duplicates)
2025-07-20 18:28:00 - common.csv_writer - INFO - [csv_writer.py:62] - Filtered out 0 duplicates, writing 30 new records
2025-07-20 18:28:00 - common.csv_writer - INFO - [csv_writer.py:76] - Successfully wrote 30 total rows (30 new) to data/output.csv
2025-07-20 18:28:00 - __main__ - INFO - [main.py:52] - Processing complete. Output saved to: data/output.csv
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

# 3. Run comprehensive test suite (74 tests)
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
make test             # Verify all tests pass (74/74)
make demo             # Run demonstration scripts
```

**Command Categories:**

1. **Environment Management**: `pipenv_new`, `install_deps`, `pipenv_shell`
2. **Application Execution**: `run`, `run_verbose`, `help_app`, `sample`  
3. **Testing & Quality**: `test`, `test_verbose`
4. **Demo & Examples**: `demo`, `demo_clean`
5. **Utilities**: `pipenv_freeze`, `check_json`, `pipenv_venv`, `help`

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
    │   ├── csv_writer.py        # CsvWriter class for CSV output with duplicate handling
    │   ├── web_client.py        # WebClient class for HTTP requests with rate limiting
    │   ├── markdown_parser.py   # MarkdownParser class for markdown content processing
    │   └── logger.py            # AppLogger class for centralized logging
    ├── tests/                   # Unit tests with pytest
    │   ├── conftest.py          # Test fixtures and configuration
    │   ├── csv_processor_test.py    # Tests for CsvProcessor
    │   ├── csv_writer_test.py       # Tests for CsvWriter
    │   ├── web_client_test.py       # Tests for WebClient
    │   ├── markdown_parser_test.py  # Tests for MarkdownParser
    │   └── main_test.py             # Tests for CLI main function
    ├── demo/                    # Demo scripts and sample files
    │   ├── README.md            # Demo documentation and usage instructions
    │   ├── demo_price_extraction.py    # Price history extraction demonstration
    │   ├── demo_idempotent.py          # Idempotent functionality demonstration
    │   ├── response_01.md              # Sample TCGPlayer response data
    │   └── *.csv                       # Demo output files and test data
    ├── data/                    # Application input and output files  
    │   ├── input.csv            # Input CSV with TCGPlayer URLs and metadata
    │   ├── output.csv           # Normalized price history data (generated)
    │   └── *.csv                # Other generated CSV files
    └── logs/                    # Generated log files (created automatically)
        ├── app.log              # Application execution logs
        └── test.log             # Test execution logs
```

### Key Files and Directories
- **Root Level**: Project documentation and configuration
- **app/**: All application code and development tools
- **app/common/**: Reusable modules following single responsibility principle
- **app/tests/**: Comprehensive unit tests matching the 13pyledger pattern
- **app/demo/**: Demonstration scripts and sample files with documentation
- **app/data/**: Application output and generated CSV files
- **logs/**: Auto-generated directory for centralized logging output

### Testing Requirements
- **Test Suite**: 74 comprehensive unit tests with 100% pass rate
- **Coverage**: All modules tested (CsvProcessor, WebClient, MarkdownParser, CsvWriter, Main CLI)
- **Environment**: Requires `TCGPLAYER_API_TOKEN` environment variable
- **Framework**: pytest with centralized logging via AppLogger
- **Execution**: `PYTHONPATH=.` set for proper module imports
- **Logging**: Test logs written to `logs/test.log` with DEBUG level
- **Setup**: Each test class initializes logging in `setup_class()` method
- **Mocking**: Uses `requests-mock` for HTTP request testing
- **Data Format**: Tests updated to expect `volume` column with integer values instead of `additional_price` currency strings

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

## Demo Scripts and Examples

The `app/demo/` directory contains comprehensive demonstrations of the application's capabilities:

### Available Demos

1. **Price History Extraction (`demo_price_extraction.py`)**
   - Demonstrates TCGPlayer price history table extraction
   - Shows normalized CSV output format
   - Uses real sample data from `response_01.md`
   
2. **Idempotent Functionality (`demo_idempotent.py`)**
   - Proves application can be run multiple times safely
   - Shows duplicate detection and prevention
   - Demonstrates automated workflow compatibility

### Running Demos

```bash
# Navigate to demo directory
cd app/demo

# Run price extraction demo
python3 demo_price_extraction.py

# Run idempotent functionality demo  
python3 demo_idempotent.py
```

### Demo Features

**Price Extraction Demo:**
- Extracts 30+ price history records from sample TCGPlayer data
- Generates normalized CSV with metadata (set, type, period, name, date, prices)
- Shows complete end-to-end extraction process with logging

**Idempotent Demo:**
- **Run 1**: Creates 30 new records from `data/input.csv` to demo output file
- **Run 2**: Detects all 30 as duplicates, writes 0 new records
- **Run 3**: Confirms consistent behavior, still 0 new records
- Proves safe automation for scheduled/recurring tasks

### Sample Data

- **`response_01.md`**: Real TCGPlayer product page content (Umbreon ex card)
- **Output files**: Various `.csv` files showing different output formats
- **Complete documentation**: See `app/demo/README.md` for detailed usage

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

## Performance Analysis and Future Optimizations

The application currently performs well for its intended use case, but several optimization opportunities exist for future enhancement if higher throughput or larger datasets become requirements:

### **Performance Bottlenecks Identified**

#### **1. Synchronous HTTP Requests (Highest Impact)**
**Current State**: Sequential processing with 1-second delays between requests
- Processing 13 URLs requires ~13+ seconds minimum
- Each request blocks the entire application thread
- Rate limiting delays are necessary but limit throughput

**Optimization Opportunity**: Async/await implementation
```python
# Potential async implementation
async def _process_rows_concurrent(self, rows: List[Dict]) -> List[Dict]:
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(3)  # Control concurrency
        tasks = [self._process_single_row(session, semaphore, row) for row in rows]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```
**Expected Impact**: Reduce processing time from ~13+ seconds to ~2-3 seconds

#### **2. CSV File I/O Inefficiency (High Impact for Large Datasets)**
**Current State**: Reads entire CSV file on every write operation
- O(n) complexity that grows with dataset size
- Currently manageable with 390+ rows but will scale poorly

**Optimization Opportunity**: Append-only or indexed approach
```python
# Potential optimized approach
def write_unique_streaming(self, data: List[Dict], output_file: Path):
    # Use SQLite index or file-based key tracking
    # Only read metadata, not full data
    pass
```
**Expected Impact**: Constant-time writes regardless of file size

#### **3. Markdown Processing (Medium Impact)**
**Current State**: Multiple regex operations scan entire content
- Sequential string processing for large TCGPlayer responses
- Multiple O(n) operations on same content

**Optimization Opportunity**: Combined regex patterns
```python
# Potential optimization
COMBINED_PATTERN = re.compile(r'(```.*?```)|(^#{1,6}\s*)|(`[^`]*`)', re.DOTALL | re.MULTILINE)
def _extract_text_optimized(self, content: str) -> str:
    return COMBINED_PATTERN.sub('', content)  # Single pass
```
**Expected Impact**: 30-50% reduction in markdown processing time

#### **4. Memory Usage (Future Scalability)**
**Current State**: Loads entire datasets into memory
- All CSV data stored in memory during processing
- Works fine for current dataset sizes

**Optimization Opportunity**: Streaming/generator approach
```python
# Potential streaming implementation
def process_streaming(self, input_file: Path):
    with open(input_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield self._process_single_row(row)
```
**Expected Impact**: Constant memory usage regardless of dataset size

### **Optimization Priority Roadmap**

**Phase 1 - Concurrency (10x+ Performance Gain)**
- Implement async/await for HTTP requests
- Add semaphore-controlled concurrency 
- Maintain rate limiting within async context
- **Target**: Process 13 URLs in ~2-3 seconds vs current ~13+ seconds

**Phase 2 - I/O Optimization (Scalability)**
- Implement append-only CSV writing with indexing
- Add streaming data processing capabilities
- **Target**: Handle 10,000+ records without performance degradation

**Phase 3 - Processing Efficiency (Polish)**
- Combine regex operations in markdown parser
- Optimize string currency conversion
- Cache redundant computations
- **Target**: 20-30% reduction in CPU usage

### **Implementation Considerations**

**When to Optimize:**
- Processing >50 URLs regularly (async HTTP becomes critical)
- Output CSV files >10,000 rows (I/O optimization needed)
- Memory constraints or resource limitations (streaming required)
- High-frequency automated processing (all optimizations beneficial)

**Current Performance Profile:**
- **Suitable for**: Manual runs, small-medium datasets, development workflows
- **Limitations**: Large batch processing, high-frequency automation
- **Strengths**: Reliable, well-tested, clear error handling

## Large Codebase Analysis

When analyzing large codebases or multiple files that might exceed context limits, use the llm CLI command:

```bash
# From app directory (cd app/)
# Analyze codebase architecture using file content injection
llm "Here is Python code: $(cat main.py common/processor.py common/csv_writer.py | head -300)

Summarize the architecture of this code base"

# Analyze specific patterns or functionality  
llm "Here are test files: $(cat tests/*_test.py | head -200)

Analyze the testing patterns and coverage in this codebase"

# Review configuration and setup files
llm "Here are config files: $(cat Makefile make.sh ../CLAUDE.md | head -100)

Review the project configuration and setup"

# Performance analysis
llm "Here is the codebase: $(cat common/*.py | head -500)

Identify potential performance bottlenecks across the codebase"

# With specific model that supports attachments (like Claude or GPT-4)
llm "Analyze code architecture and design patterns" -m claude-3-5-sonnet-20241022 -a main.py -a common/processor.py

# Process files individually for detailed analysis
llm "Here is a Python module: $(cat common/processor.py)

Analyze this processor module for performance bottlenecks"

# Using system prompts for focused analysis
llm "Here is web client code: $(cat common/web_client.py)

Analyze this code for performance issues" -s "You are a performance expert. Focus on identifying bottlenecks and optimization opportunities."
```

This approach is particularly useful for:
- Understanding complex multi-file architectures
- Analyzing large test suites
- Reviewing configuration across multiple files
- Getting high-level summaries without hitting context limits
- Identifying optimization opportunities

### **Example Analysis Output**

The llm CLI provides comprehensive analysis similar to senior developer code reviews. For example, when analyzing project configuration:

**Strengths Identified:**
- ✅ **Modern tooling**: pipenv for dependency management with consistent environments
- ✅ **Organized workflow**: Logical grouping of Makefile commands into clear categories
- ✅ **Self-documenting**: Built-in help system with detailed command descriptions
- ✅ **Environment validation**: Automated checks for required tools and variables

**Improvement Opportunities:**
- 🔄 **Dependency simplification**: Consider streamlining pipenv + pipreqs approach
- 🔄 **Error handling**: Add confirmations for destructive operations
- 🔄 **CI/CD integration**: Automate testing and deployment workflows
- 📝 **Documentation enhancement**: Central README to complement Makefile documentation

This demonstrates the llm CLI's effectiveness for **architectural assessment**, **configuration review**, and **development workflow analysis**, providing actionable insights for project improvement.

## **Git Commit Message Generation**

Use the llm CLI to generate conventional commit messages based on actual code changes:

```bash
# Generate commit message from git diff (for unstaged changes)
llm "Generate a conventional commit message in one line for the following git changes: $(git diff HEAD -- app/common/csv_writer.py app/common/processor.py app/tests/csv_processor_test.py)"

# For staged changes only  
llm "Generate a conventional commit message in one line for the following git changes: $(git diff --cached)"

# For all changes (staged and unstaged)
llm "Generate a conventional commit message in one line for the following git changes: $(git diff HEAD)"

# With file-specific focus
llm "Generate a conventional commit message in one line for these specific changes: $(git diff HEAD -- filename.py)"
```

**Example Workflow:**
```bash
# 1. Make code changes to fix CSV sorting and error handling
# 2. Generate commit message from changes
llm "Generate a conventional commit message in one line for the following git changes: $(git diff HEAD -- app/common/csv_writer.py app/common/processor.py app/tests/csv_processor_test.py)"

# Output: fix: sort data before writing to CSV and normalize error rows in processor

# 3. Stage and commit with generated message
git add app/common/csv_writer.py app/common/processor.py app/tests/csv_processor_test.py
git commit -m "fix: sort data before writing to CSV and normalize error rows in processor"
```

**Standard Output Format:**
- **Type**: fix, feat, docs, style, refactor, test, chore
- **Scope**: Optional - component or module affected  
- **Description**: Concise summary of changes in imperative mood

This approach ensures commit messages are:
- ✅ **Contextually accurate** based on actual code changes
- ✅ **Conventionally formatted** following standard commit message patterns  
- ✅ **Descriptive** of the specific modifications made
- ✅ **Consistent** with project standards and best practices