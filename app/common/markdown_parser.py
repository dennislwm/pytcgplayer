import re
from typing import Dict, Any

from common.logger import AppLogger


class MarkdownParser:
    def __init__(self):
        self.logger = AppLogger.get_logger(__name__)
    
    def parse(self, content: str) -> str:
        self.logger.debug(f"Parsing {len(content)} characters of markdown")
        
        if not content.strip():
            return ""
        
        # Basic markdown parsing - extract text content
        parsed = self._extract_text(content)
        
        self.logger.debug(f"Parsed to {len(parsed)} characters")
        return parsed
    
    def _extract_text(self, content: str) -> str:
        # Remove code blocks
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        
        # Remove inline code
        content = re.sub(r'`[^`]*`', '', content)
        
        # Remove headers (keep text)
        content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)
        
        # Remove links (keep text)
        content = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', content)
        
        # Remove bold/italic markers
        content = re.sub(r'\*{1,2}([^*]*)\*{1,2}', r'\1', content)
        content = re.sub(r'_{1,2}([^_]*)_{1,2}', r'\1', content)
        
        # Clean up excessive whitespace but preserve paragraph breaks
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Multiple blank lines -> double newline
        content = content.strip()
        
        return content