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

        # Validate input schema
        self._validate_input_schema(input_file)

        rows = self._read_csv(input_file)
        self.results = self._process_rows(rows)

        # Validate output matches v2.0 schema (only for TCGPlayer price data)
        if self.results and 'period_start_date' in self.results[0]:
            self._validate_output_schema(self.results)

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

                # Extract price history from TCGPlayer URLs
                if self._is_tcgplayer_url(row['url']):
                    price_data = self.markdown_parser.parse_price_history_data(markdown_content)
                    if price_data:
                        self.logger.info(f"Extracted {len(price_data)} price history records for row {i}")
                        # One-liner normalized row creation for each price record (v2.0 format)
                        processed_rows.extend([{**{k: row.get(k, '') for k in ['set', 'type', 'period', 'name']}, **price_record} for price_record in price_data])
                    else:
                        self.logger.warning(f"No price history found for TCGPlayer URL in row {i}, skipping")
                else:
                    self.logger.warning(f"Non-TCGPlayer URL in row {i}, skipping: {row['url']}")

                self.logger.debug(f"Successfully processed row {i}")

            except Exception as e:
                self.logger.error(f"Failed to process row {i}: {e}")
                # One-liner normalized error row creation (v2.0 format)
                processed_rows.append({**{k: row.get(k, '') for k in ['set', 'type', 'period', 'name']}, **{'period_start_date': '', 'period_end_date': '', 'timestamp': DataProcessor.get_current_timestamp(), 'holofoil_price': 0.0, 'volume': 0}})

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
            # One-liner price extraction and conversion using DataProcessor
            first_price = DataProcessor.convert_currency_to_float(price_data[-1]['holofoil']) if price_data else 0.0
            last_price = DataProcessor.convert_currency_to_float(price_data[0]['holofoil']) if price_data else 0.0

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

    def _validate_input_schema(self, input_file: Path) -> None:
        """Validate input CSV schema and raise error if invalid"""
        schema_path = Path(__file__).parent.parent / 'schema' / 'input_v1.json'
        is_valid, errors = FileHelper.validate_csv_schema(input_file, schema_path)

        if not is_valid:
            error_msg = f"Input schema validation failed: {errors}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info("Input schema validation passed")

    def _validate_output_schema(self, output_data: List[Dict]) -> None:
        """Validate output data matches v2.0 schema format"""
        if not output_data:
            return

        expected_fields = [
            'set', 'type', 'period', 'name',
            'period_start_date', 'period_end_date', 'timestamp',
            'holofoil_price', 'volume'
        ]

        # One-liner field validation
        missing_fields = [field for field in expected_fields if field not in output_data[0]]
        if missing_fields:
            error_msg = f"Output data missing required v2.0 fields: {missing_fields}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info("Output data matches v2.0 schema format")