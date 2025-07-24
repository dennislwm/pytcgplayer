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

        # Check for missing headers
        missing = set(expected_headers) - set(headers)
        if missing:
            errors.append(f"Missing headers: {list(missing)}")

        # Check for extra headers
        extra = set(headers) - set(expected_headers)
        if extra:
            errors.append(f"Extra headers: {list(extra)}")

        # Check header order
        if headers != expected_headers:
            errors.append(f"Header order mismatch. Expected: {expected_headers}, Got: {headers}")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Schema validation failed for {csv_path}: {errors}")
        else:
            logger.info(f"Schema validation passed for {csv_path}")

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
        """Convert currency string like '$1.00' to integer like 1"""
        try:
            cleaned = currency_str.replace('$', '').replace(',', '')
            return int(float(cleaned)) if cleaned.replace('.', '').isdigit() else 0
        except (ValueError, AttributeError):
            return 0

    @staticmethod
    def convert_currency_to_float(currency_str: str) -> float:
        """Convert currency string like '$49.73' to float like 49.73"""
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