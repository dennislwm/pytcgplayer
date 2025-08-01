import csv
import json
import re
import time
import random
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Callable, Any, Optional
from functools import wraps

import pandas as pd
import numpy as np

from common.logger import AppLogger


class ConfigurationTestHelper:
    """Helper class for Configuration Manager test utilities"""
    
    @staticmethod
    def assert_config_equality(config, expected_name: str, expected_filters: Dict, expected_validation: Dict = None):
        """One-liner configuration assertion"""
        assert all([
            config.name == expected_name,
            config.filters == expected_filters,
            not expected_validation or config.validation_metadata.get("coverage_percentage") == expected_validation.get("coverage_percentage")
        ])
    
    @staticmethod
    def create_test_config(name: str = "test_config", filters: Dict = None, validation: Dict = None) -> Dict:
        """One-liner test configuration creation"""
        return {
            "name": name,
            "display_name": f"Test {name.replace('_', ' ').title()}",
            "description": f"Test description for {name}",
            "filters": filters or {"sets": "SV*", "types": "Card", "period": "3M"},
            "validation_metadata": validation or {"coverage_percentage": 1.0, "signatures_found": 10},
            "usage_statistics": {"created_at": "2025-07-30T10:00:00Z", "last_used": None, "use_count": 0},
            "system_metadata": {"created_by_version": "workbench-v1.0", "dataset_fingerprint": "abc123"}
        }
    
    @staticmethod
    def validate_usage_update(config, expected_count: int = 1):
        """One-liner usage statistics validation"""
        assert config.usage_statistics["use_count"] == expected_count and config.usage_statistics["last_used"] is not None


class FileHelper:
    """Utility class for common file operations"""

    @staticmethod
    def load_schema(schema_path: Path) -> Optional[Dict]:
        """Load JSON schema file"""
        try:
            with open(schema_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger = AppLogger.get_logger(__name__)
            logger.warning(f"Failed to load schema {schema_path}: {e}")
            return None

    @staticmethod
    def validate_csv_schema(csv_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
        """Validate CSV headers against schema, return (is_valid, errors)"""
        logger = AppLogger.get_logger(__name__)

        schema = FileHelper.load_schema(schema_path)
        if not schema:
            return False, [f"Could not load schema from {schema_path}"]

        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = next(reader, [])
        except FileNotFoundError:
            return False, [f"CSV file not found: {csv_path}"]
        except Exception as e:
            return False, [f"Error reading CSV: {e}"]

        expected_headers = schema.get('header_order', [])
        errors = []

        # One-liner header validation
        missing, extra = set(expected_headers) - set(headers), set(headers) - set(expected_headers)
        if missing: errors.append(f"Missing headers: {list(missing)}")
        if extra: errors.append(f"Extra headers: {list(extra)}")
        if headers != expected_headers: errors.append(f"Header order mismatch. Expected: {expected_headers}, Got: {headers}")

        # One-liner validation result logging
        is_valid = len(errors) == 0
        (logger.warning(f"Schema validation failed for {csv_path}: {errors}") if not is_valid else logger.info(f"Schema validation passed for {csv_path}"))

        return is_valid, errors

    @staticmethod
    def read_csv(path: Path) -> List[Dict]:
        """Read CSV file and return list of dictionaries"""
        try:
            with open(path, 'r', newline='', encoding='utf-8') as file:
                content = file.read().strip()
                if not content:
                    return []
                file.seek(0)
                return list(csv.DictReader(file))
        except FileNotFoundError:
            raise  # Re-raise FileNotFoundError for test compatibility
        except Exception:
            return []

    @staticmethod
    def write_csv(data: List[Dict], path: Path) -> None:
        """Write data to CSV file"""
        if not data:
            return
        with open(path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


class RetryHelper:
    """Utility class for retry logic with exponential backoff"""

    @staticmethod
    def with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0):
        """Decorator for exponential backoff retry logic"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                logger = AppLogger.get_logger(__name__)

                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            delay = base_delay * (4 ** attempt) + random.uniform(0, 3)
                            logger.info(f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        logger.warning(f"Attempt {attempt + 1} failed: {e}")
                return None
            return wrapper
        return decorator


class DataProcessor:
    """Mixin class for common data processing operations"""

    def create_key(self, row: Dict, columns: List[str]) -> Tuple:
        """Create a unique key tuple from specified columns"""
        return tuple(row.get(col, '') for col in columns)

    def normalize_row(self, source: Dict, schema: Dict[str, str]) -> Dict:
        """Normalize row data according to schema mapping"""
        return {target_key: source.get(source_key, '') for target_key, source_key in schema.items()}

    def create_key_index(self, data: List[Dict], key_columns: List[str]) -> Dict[Tuple, int]:
        """Create mapping from unique keys to their index in data list"""
        return {self.create_key(row, key_columns): idx for idx, row in enumerate(data)}

    @staticmethod
    def convert_currency_to_int(currency_str: str) -> int:
        """One-liner currency to integer conversion"""
        return int(DataProcessor.convert_currency_to_float(currency_str))

    @staticmethod
    def convert_currency_to_float(currency_str: str) -> float:
        """One-liner currency string to float conversion"""
        try:
            cleaned = currency_str.replace('$', '').replace(',', '')
            return float(cleaned) if cleaned.replace('.', '').isdigit() else 0.0
        except (ValueError, AttributeError):
            return 0.0

    @staticmethod
    def parse_date_range(date_str: str) -> Tuple[str, str]:
        """
        Parse date range string like "4/20 to 4/22" into start and end dates

        Args:
            date_str: Date range string (e.g., "4/20 to 4/22")

        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        current_year = datetime.now().year
        pattern = r'(\d{1,2})/(\d{1,2})\s+to\s+(\d{1,2})/(\d{1,2})'
        match = re.match(pattern, date_str.strip())

        if not match:
            return "", ""

        start_month, start_day, end_month, end_day = match.groups()

        # Convert to YYYY-MM-DD format
        start_date = f"{current_year}-{int(start_month):02d}-{int(start_day):02d}"
        end_date = f"{current_year}-{int(end_month):02d}-{int(end_day):02d}"

        # Handle year rollover (if end month < start month, assume next year)
        if int(end_month) < int(start_month):
            end_date = f"{current_year + 1}-{int(end_month):02d}-{int(end_day):02d}"

        return start_date, end_date

    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp in YYYY-MM-DD HH:MM:SS format"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class CoverageResultFactory:
    """Factory class for creating CoverageResult objects with common patterns"""

    @staticmethod
    def create_empty(filter_config: Dict[str, str]):
        """One-liner empty coverage result creation"""
        from common.coverage_analyzer import CoverageResult  # Import here to avoid circular dependency
        return CoverageResult(filter_config=filter_config, coverage_percentage=0.0, signatures_found=0,
                            signatures_total=0, optimal_start_date=None, records_before_start=0,
                            records_aligned=0, time_series_points=0, gap_fills_required=0,
                            missing_signatures=[], fallback_required=False, quality_score=0.0)

    @staticmethod
    def create_from_metrics(filter_config: Dict[str, str], metrics: Dict[str, Any]):
        """One-liner coverage result from alignment metrics"""
        from common.coverage_analyzer import CoverageResult
        return CoverageResult(filter_config=filter_config, **{k: metrics[k] for k in
                            ['coverage_percentage', 'signatures_found', 'signatures_total', 'optimal_start_date',
                             'records_before_start', 'records_aligned', 'time_series_points', 'gap_fills_required',
                             'missing_signatures', 'fallback_required', 'quality_score']})


class FilterValidationHelper:
    """One-liner filter validation utilities for coverage analysis"""

    @staticmethod
    def is_valid_filter_combination(sets: str, types: str) -> bool:
        """One-liner validation check for filter combinations"""
        from chart.index_aggregator import FilterValidator
        return bool(FilterValidator.expand_set_pattern(sets) and FilterValidator.expand_type_pattern(types))

    @staticmethod
    def get_default_configurations() -> List[Dict[str, str]]:
        """One-liner default configuration patterns for fallback recommendations"""
        return [{"sets": "SV*", "types": "Card", "period": "3M", "description": "SV Cards (Recommended)"},
                {"sets": "SV*", "types": "*Box", "period": "3M", "description": "SV Boxes (Alternative)"},
                {"sets": "SWSH*", "types": "Card", "period": "3M", "description": "SWSH Cards (Alternative)"}]

    @staticmethod
    def generate_description(combo: Dict[str, str], coverage_percentage: float) -> str:
        """One-liner description generation for filter combinations"""
        set_desc, type_desc = (combo["sets"].replace("*", "").replace(",", "/") if combo["sets"] != "*" else "All",
                               combo["types"].replace("*", "").replace(",", "/") if combo["types"] != "*" else "All Types")
        quality = "Complete" if coverage_percentage == 1.0 else "Excellent" if coverage_percentage >= 0.95 else "High Quality" if coverage_percentage >= 0.90 else "Good"
        return f"{set_desc} {type_desc} ({quality})"


class PerformanceHelper:
    """Performance monitoring and logging utilities"""

    @staticmethod
    def create_performance_decorator(method_name: str):
        """One-liner performance logging decorator factory"""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                start_time, result = time.time(), func(self, *args, **kwargs)
                self.logger.info(f"{method_name} completed in {time.time() - start_time:.2f}s")
                return result
            return wrapper
        return decorator


class JsonConfigHelper:
    """JSON configuration file operations with atomic writes and error handling"""
    
    @staticmethod
    def load_json_config(file_path: Path, default_factory: Callable[[], Dict]) -> Dict[str, Any]:
        """One-liner JSON config loading with fallback"""
        try:
            return json.load(open(file_path, 'r', encoding='utf-8')) if file_path.exists() else default_factory()
        except (json.JSONDecodeError, Exception):
            return default_factory()
    
    @staticmethod
    def save_json_atomic(file_path: Path, data: Dict[str, Any]) -> bool:
        """One-liner atomic JSON save with temp file"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_file = file_path.with_suffix('.tmp')
            json.dump(data, open(temp_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            temp_file.replace(file_path)
            return True
        except Exception:
            temp_file.unlink(missing_ok=True) if 'temp_file' in locals() else None
            return False


class ConfigurationFactory:
    """Factory for FilterConfiguration objects with one-liner creation"""
    
    @staticmethod
    def from_dict(config_data: Dict[str, Any]):
        """One-liner FilterConfiguration creation from dictionary"""
        from common.configuration_manager import FilterConfiguration
        return FilterConfiguration(**{k: config_data[k] for k in 
                                   ['name', 'display_name', 'description', 'filters', 
                                    'validation_metadata', 'usage_statistics', 'system_metadata']})
    
    @staticmethod
    def create_config_entry(name: str, display_name: str, filters: Dict, validation_metadata: Dict, 
                          description: str, updating_existing: bool, existing_usage: Dict = None) -> Dict:
        """One-liner config entry creation with usage preservation"""
        now = datetime.now(timezone.utc).isoformat()
        return {
            "name": name, "display_name": display_name, "description": description,
            "filters": filters, "validation_metadata": validation_metadata,
            "usage_statistics": {
                "created_at": existing_usage.get("created_at", now) if updating_existing and existing_usage else now,
                "last_used": existing_usage.get("last_used") if updating_existing and existing_usage else None,
                "use_count": existing_usage.get("use_count", 0) if updating_existing and existing_usage else 0,
                "last_validation": now
            },
            "system_metadata": {
                "created_by_version": "workbench-v1.0",
                "dataset_fingerprint": f"sha256:{hashlib.sha256(open('data/output.csv', 'rb').read()).hexdigest()[:16]}" if Path("data/output.csv").exists() else "",
                "validation_dataset_size": validation_metadata.get("signatures_total", 0)
            }
        }


class ConfigurationManagerHelper:
    """Helper methods for configuration management operations"""
    
    @staticmethod
    def update_usage_stats(config: Dict, action: str = "use") -> Dict:
        """One-liner usage statistics update"""
        now = datetime.now(timezone.utc).isoformat()
        if action == "use":
            config["usage_statistics"].update({"last_used": now, "use_count": config["usage_statistics"].get("use_count", 0) + 1})
        elif action == "validate":
            config["usage_statistics"]["last_validation"] = now
        return config
    
    @staticmethod
    def validate_and_log(name: str, validation_func: Callable, logger) -> bool:
        """One-liner validation with error logging"""
        is_valid, errors = validation_func()
        if not is_valid: 
            logger.error(f"Validation failed for {name}: {errors}")
        return is_valid


def resilient_config_operation(operation_name: str):
    """Decorator for consistent error handling in configuration operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Failed to {operation_name}: {e}")
                return False if func.__name__.startswith(('save', 'delete', 'update')) else None
        return wrapper
    return decorator


class ChartDataProcessor(DataProcessor):
    """Helper class for chart data processing operations with one-liner implementations"""
    
    @staticmethod
    def load_and_convert_time_series(csv_file: str) -> pd.DataFrame:
        """One-liner time series loading with OHLC conversion and technical indicators"""
        try:
            # Load and convert time series data in one pipeline
            df = (pd.read_csv(csv_file)
                  .pipe(lambda x: x.set_index(pd.to_datetime(x['period_end_date'])).sort_index())
                  .pipe(ChartDataProcessor._create_ohlc_format)
                  .pipe(ChartDataProcessor._calculate_dbs_indicators)
                  .dropna())
            return df
        except Exception as e:
            raise FileNotFoundError(f"Error loading {csv_file}: {e}")
    
    @staticmethod
    def _create_ohlc_format(df: pd.DataFrame) -> pd.DataFrame:
        """Convert time series data to OHLC format for charting"""
        # Use aggregate_price as Close, create realistic OHLC with small variations
        df['Close'] = df['aggregate_price']
        df['Open'] = df['Close'].shift(1).fillna(df['Close'].iloc[0])
        
        # Add controlled variations for High/Low (within 2% of Close)
        np.random.seed(42)  # Reproducible results
        variation = 0.02
        df['High'] = df['Close'] * (1 + np.random.uniform(0, variation, len(df)))
        df['Low'] = df['Close'] * (1 - np.random.uniform(0, variation, len(df)))
        
        # Ensure proper OHLC relationships
        df['High'] = np.maximum(df['High'], np.maximum(df['Close'], df['Open']))
        df['Low'] = np.minimum(df['Low'], np.minimum(df['Close'], df['Open']))
        
        # Use aggregate_value as Volume
        df['Volume'] = df['aggregate_value']
        df['Adjusted'] = df['Close']
        
        return df
    
    @staticmethod
    def _calculate_dbs_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate DBS technical indicators using one-liner assignments"""
        return df.assign(
            Dbs=lambda x: ((x['Close'] / x['Close'].shift(20) - 1) * 100).rolling(5).mean(),
            DbsMa=lambda x: x['Dbs'].rolling(7).mean()
        )
    
    @staticmethod
    def create_chart_with_indicators(df: pd.DataFrame, title_suffix: str, save_name: str) -> str:
        """One-liner chart creation with standard DBS indicators"""
        from pyfxgit.ChartCls import ChartCls
        
        chart = ChartCls(df, intSub=2)
        chart.BuildOscillator(1, df['Dbs'], intUpper=3, intLower=-3, strTitle="Dbs")
        chart.BuildOscillator(0, df['DbsMa'], intUpper=3.75, intLower=-3.75, strTitle="DbsMa")
        
        lstTag = chart.BuildOscillatorTag(df, 'DbsMa', 3.75)
        chart.MainAddSpan(df['Tag'], lstTag[lstTag>0], 0.2, 'red')
        chart.MainAddSpan(df['Tag'], lstTag[lstTag<0], 0.2, 'green')
        
        chart.BuildMain(strTitle=f"TCGPlayer Time Series - {title_suffix}")
        chart.save(save_name)
        
        return f"_ChartC_0.1_{save_name}.png"