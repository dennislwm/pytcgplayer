import requests
import time
from typing import Optional

from common.logger import AppLogger
from common.helpers import RetryHelper


class WebClient:
    def __init__(self, timeout: int = 30, max_retries: int = 3, base_delay: float = 1.0):
        self.logger = AppLogger.get_logger(__name__)
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CSVProcessor/1.0'
        })
    
    def fetch(self, url: str) -> str:
        self.logger.debug(f"Fetching URL: {url}")
        
        @RetryHelper.with_exponential_backoff(self.max_retries, self.base_delay)
        def _fetch_with_retry():
            # Always add base delay between requests to respect rate limits
            time.sleep(self.base_delay)
            response = self.session.get(url, timeout=self.timeout)
            
            # Handle rate limiting specifically
            if response.status_code == 429:
                self.logger.warning("Rate limited (429), retrying...")
                raise requests.exceptions.HTTPError("Rate limited", response=response)
            
            response.raise_for_status()
            return response.text
        
        try:
            content = _fetch_with_retry()
            self.logger.debug(f"Fetched {len(content)} characters from {url}")
            return content
        except Exception as e:
            self.logger.error(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")
            raise