# CLAUDE.md

Python CLI for TCGPlayer price data processing with time series alignment and technical analysis.

## Project Overview

Processes TCGPlayer URLs → fetches price history → outputs normalized CSV (schema v2.0) with numeric types for analysis/charting.

## Quick Start & Commands

**Setup**: `make pipenv_new && make install_deps && make sample && make run_verbose && make test`

| Category | Commands |
|----------|----------|
| **Environment** | `pipenv_new`, `install_deps`, `pipenv_shell` |
| **Application** | `run`, `run_verbose`, `run_ci`, `sample`, `help_app` |
| **Testing** | `test`, `test_verbose` |
| **Schema** | `convert_schema` |
| **Charts** | `chart`, `chart_yfinance`, `chart_help` |
| **Workbench** | `workbench_discover`, `workbench_analyze`, `workbench_save`, `workbench_list`, `workbench_run` |

**Data Flow**: Input URLs → Price History → Schema v2.0 (numeric types: `holofoil_price`, `volume`)

## Technical Analysis

**DBS System**: Dual oscillators, ratio analysis, 20-period ROC, Bull/Neutral/Bear alerts (±3.75 thresholds)
**Charts**: `make chart` (CSV data), `make chart_yfinance` (stock comparison), outputs `_ChartC_0.1_TCG_DBS.png`
**Helpers**: `DataFrameHelper`, `TechnicalAnalysisHelper`, `AlertHelper` for one-liner implementations

## Code Standards

**CRITICAL: Prioritize code size reduction and reusability**
**Helpers**: Use `FileHelper`, `RetryHelper`, `DataProcessor` from `common/helpers.py`
**Style**: One-liners, list comprehensions, `snake_case` files/functions, `PascalCase` classes
**Achievement**: ~120 lines reduction (15%) through helper classes

## Schema & Data

**Input v1.0**: `set,type,period,name,url` (TCGPlayer URLs)
**Output v2.0**: Adds `period_start_date,period_end_date,timestamp,holofoil_price,volume` (numeric types)
**Migration**: `make convert_schema` - converts currency strings to decimals, dates to YYYY-MM-DD
**Validation**: Auto-validation with error messages, tests in `tests/schema_test.py`

## Development

**Structure**: `app/` → `main.py`, `common/`, `tests/`, `demo/`, `data/`, `logs/`
**Testing**: 165+ tests, 100% pass rate, pytest + AppLogger, `PYTHONPATH=.` required
**Dependencies**: Core (`requests`, `pytest`, `typer`), Analysis (`numpy`, `pandas`), Charts (`pyfxgit`, `ta`, `yfinance`)
**Windows**: Run from `app/` directory, use `PIPENV_VERBOSITY=-1` to suppress warnings

**Logging**: `AppLogger.get_logger(__name__)` - dual output to console + `logs/app.log`/`logs/test.log`
**Tools**: `gh`, `python`, `pipenv`, `shellcheck` required
**Automation**: Daily workflow 6AM UTC (`make run_ci`), manual trigger via `gh workflow run`
**Demo**: `app/demo/` for extraction demos, `make sample` creates test data, idempotent processing

## Features

**Rate Limiting**: 5s base delay, exponential backoff (5s→20s→80s), 429 detection, 3 retries
**Table Formats**: Auto-detects `| Date | Holofoil |` (cards) and `| Date | Normal |` (boxes) 
**CSV Updates**: Updates existing records by fingerprint `(set,type,period,name,date)`, logs update/new counts

## Performance

**Current**: ~1s per URL, sequential HTTP, suitable for manual runs
**Optimizations**: ~120 lines reduced (15%) via helper classes and one-liners
**Future**: Async HTTP, streaming CSV I/O, additional helper consolidation

## Storage

**Current**: CSV format, ~82 bytes/record, 10MB in ~22 years at current rate
**Future**: SQLite migration when >100 records/day (40-60 bytes/record, indexed queries)
**Alternatives**: Parquet (70-82% savings), CSV+gzip (66% savings)

## Interactive Workbench

**Status**: ✅ Production-ready (21/21 tests passing)
**Purpose**: Transforms 15-30 min trial-and-error alignment → 2-5 min guided discovery
**Core**: `CoverageAnalyzer` class with `discover`, `analyze`, `save`, `list`, `run` commands
**Performance**: 544x caching speed improvement, 100% SV coverage, 4-strategy failure recovery
**Architecture**: Zero-modification wrapper, dependency injection, comprehensive testing

## Reference

**Codebase Analysis**: Use `llm` CLI for large codebases: `llm "Analyze: $(cat main.py | head -300)"`
**Commit Messages**: `type: description` format, mention code size reductions (-X lines)
**Examples**: `refactor: consolidate CSV operations into FileHelper class (-50 lines)`