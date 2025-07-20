import requests
from typing import Optional

from common.logger import AppLogger


class WebClient:
    def __init__(self, timeout: int = 30):
        self.logger = AppLogger.get_logger(__name__)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CSVProcessor/1.0'
        })
    
    def fetch(self, url: str) -> str:
        self.logger.debug(f"Fetching URL: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            content = response.text
            self.logger.debug(f"Fetched {len(content)} characters from {url}")
            
            return content
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            raise