import re
from typing import Dict, Any, List, Optional

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
    
    def extract_price_history_table(self, content: str) -> Optional[str]:
        """Extract TCGPlayer price history table from markdown content"""
        self.logger.debug("Extracting price history table from content")
        
        if not content.strip():
            return None
        
        # Pattern to match table starting with Date | Holofoil header
        table_pattern = r'\|\s*Date\s*\|\s*Holofoil\s*\|.*?(?=\n\n|\n(?!\|)|\Z)'
        
        match = re.search(table_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not match:
            self.logger.debug("No price history table found")
            return None
        
        table_content = match.group(0).strip()
        
        # Clean up the table formatting
        lines = table_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and line.startswith('|') and line.endswith('|'):
                cleaned_lines.append(line)
        
        if len(cleaned_lines) < 3:  # Header + separator + at least one data row
            self.logger.debug("Table too small - needs header, separator, and data rows")
            return None
        
        result = '\n'.join(cleaned_lines)
        self.logger.info(f"Extracted price history table with {len(cleaned_lines)} rows")
        
        return result
    
    def parse_price_history_data(self, content: str) -> List[Dict[str, str]]:
        """Parse price history table into structured data"""
        self.logger.debug("Parsing price history table into structured data")
        
        table_content = self.extract_price_history_table(content)
        if not table_content:
            return []
        
        lines = table_content.split('\n')
        data_rows = []
        
        # Skip header (first line) and separator (second line)
        for line in lines[2:]:
            line = line.strip()
            if not line or not line.startswith('|'):
                continue
            
            # Split by | and clean up
            cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
            
            if len(cells) >= 2:
                row_data = {
                    'date': cells[0].strip(),
                    'holofoil': cells[1].strip() if len(cells) > 1 else '',
                    'price': cells[2].strip() if len(cells) > 2 else ''
                }
                data_rows.append(row_data)
        
        self.logger.info(f"Parsed {len(data_rows)} price history records")
        return data_rows