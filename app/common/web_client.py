import requests
import time
import random
from typing import Optional

from common.logger import AppLogger


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
        
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff with jitter for retries
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    self.logger.info(f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    # Always add base delay between requests to respect rate limits
                    time.sleep(self.base_delay)
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                content = response.text
                self.logger.debug(f"Fetched {len(content)} characters from {url}")
                
                return content
                
            except requests.exceptions.HTTPError as e:
                # Check if it's a 429 rate limit error and we have retries left
                if (hasattr(e, 'response') and e.response is not None and 
                    e.response.status_code == 429 and attempt < self.max_retries - 1):
                    self.logger.warning(f"Rate limited (429), retrying... (attempt {attempt + 1})")
                    continue
                else:
                    self.logger.error(f"Failed to fetch {url}: {e}")
                    raise
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Request failed, retrying... (attempt {attempt + 1}): {e}")
                    continue
                else:
                    self.logger.error(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")
                    raise