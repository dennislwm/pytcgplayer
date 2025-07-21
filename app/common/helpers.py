import csv
import time
import random
from pathlib import Path
from typing import Dict, List, Tuple, Callable, Any
from functools import wraps

from common.logger import AppLogger


class FileHelper:
    """Utility class for common file operations"""
    
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
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
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