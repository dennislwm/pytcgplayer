import csv
from pathlib import Path
from typing import Dict, List

from common.web_client import WebClient
from common.markdown_parser import MarkdownParser
from common.logger import AppLogger


class CsvProcessor:
    def __init__(self):
        self.logger = AppLogger.get_logger(__name__)
        self.web_client = WebClient()
        self.markdown_parser = MarkdownParser()
        self.results = []
    
    def process(self, input_file: Path) -> List[Dict]:
        self.logger.info(f"Processing file: {input_file}")
        
        rows = self._read_csv(input_file)
        self.results = self._process_rows(rows)
        
        return self.results
    
    def _read_csv(self, file_path: Path) -> List[Dict]:
        self.logger.info(f"Reading CSV file: {file_path}")
        
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                raise ValueError(f"CSV file '{file_path}' is empty")
            
            file.seek(0)  # Reset file pointer
            reader = csv.DictReader(file)
            rows = list(reader)
            
            if not rows:
                raise ValueError(f"CSV file '{file_path}' contains no data rows")
        
        self.logger.info(f"Read {len(rows)} rows")
        return rows
    
    def _process_rows(self, rows: List[Dict]) -> List[Dict]:
        self.logger.info("Processing rows...")
        processed_rows = []
        
        for i, row in enumerate(rows, 1):
            self.logger.debug(f"Processing row {i}/{len(rows)}")
            
            if 'url' not in row:
                self.logger.warning(f"Row {i} missing 'url' column, skipping")
                continue
            
            try:
                markdown_content = self.web_client.fetch(row['url'])
                parsed_content = self.markdown_parser.parse(markdown_content)
                
                row['content'] = parsed_content
                processed_rows.append(row)
                
                self.logger.debug(f"Successfully processed row {i}")
                
            except Exception as e:
                self.logger.error(f"Failed to process row {i}: {e}")
                row['content'] = ''
                processed_rows.append(row)
        
        self.logger.info(f"Processed {len(processed_rows)} rows")
        return processed_rows