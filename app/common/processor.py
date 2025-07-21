import csv
from pathlib import Path
from typing import Dict, List

from common.web_client import WebClient
from common.markdown_parser import MarkdownParser
from common.logger import AppLogger
from common.helpers import FileHelper, DataProcessor


class CsvProcessor(DataProcessor):
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
        rows = FileHelper.read_csv(file_path)
        if not rows:
            raise ValueError(f"CSV file '{file_path}' is empty or contains no data rows")
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
                
                # Check if this is a TCGPlayer URL and extract price history
                if self._is_tcgplayer_url(row['url']):
                    price_data = self.markdown_parser.parse_price_history_data(markdown_content)
                    if price_data:
                        self.logger.info(f"Extracted {len(price_data)} price history records for row {i}")
                        # Create normalized rows - one for each price record
                        for price_record in price_data:
                            normalized_row = {
                                'set': row.get('set', ''),
                                'type': row.get('type', ''),  
                                'period': row.get('period', ''),
                                'name': row.get('name', ''),
                                'date': price_record['date'],
                                'holofoil_price': price_record['holofoil'],
                                'volume': self.convert_currency_to_int(price_record['price'])
                            }
                            processed_rows.append(normalized_row)
                    else:
                        self.logger.debug(f"No price history found for TCGPlayer URL in row {i}")
                        # Keep original row if no price data
                        row['content'] = parsed_content
                        processed_rows.append(row)
                else:
                    # Non-TCGPlayer URLs get normal processing
                    row['content'] = parsed_content
                    processed_rows.append(row)
                
                self.logger.debug(f"Successfully processed row {i}")
                
            except Exception as e:
                self.logger.error(f"Failed to process row {i}: {e}")
                # Create normalized error row with empty price data
                error_row = {
                    'set': row.get('set', ''),
                    'type': row.get('type', ''),  
                    'period': row.get('period', ''),
                    'name': row.get('name', ''),
                    'date': 'ERROR',
                    'holofoil_price': '$0.00',
                    'volume': 0
                }
                processed_rows.append(error_row)
        
        self.logger.info(f"Processed {len(processed_rows)} rows")
        return processed_rows
    
    def _is_tcgplayer_url(self, url: str) -> bool:
        """Check if URL is a TCGPlayer product page"""
        return 'tcgplayer.com' in url.lower()
    
    
    def _calculate_price_trend(self, price_data: List[Dict]) -> str:
        """Calculate price trend from historical data"""
        if len(price_data) < 2:
            return 'insufficient_data'
        
        try:
            # Get first and last prices, clean the $ and commas
            first_price_str = price_data[-1]['holofoil'].replace('$', '').replace(',', '')
            last_price_str = price_data[0]['holofoil'].replace('$', '').replace(',', '')
            
            first_price = float(first_price_str) if first_price_str else 0.0
            last_price = float(last_price_str) if last_price_str else 0.0
            
            if first_price == 0:
                return 'no_baseline'
            
            change_percent = ((last_price - first_price) / first_price) * 100
            
            if change_percent > 5:
                return f'up_{change_percent:.1f}%'
            elif change_percent < -5:
                return f'down_{abs(change_percent):.1f}%'
            else:
                return f'stable_{change_percent:.1f}%'
                
        except (ValueError, KeyError) as e:
            self.logger.warning(f"Error calculating price trend: {e}")
            return 'calculation_error'