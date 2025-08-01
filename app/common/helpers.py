import csv
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Callable, Any, Optional
from functools import wraps

from common.logger import AppLogger


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