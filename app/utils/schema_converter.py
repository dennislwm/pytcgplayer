#!/usr/bin/env python3
"""
Schema Converter: Convert output.csv from v1.0 to v2.0 format

Converts date ranges like "4/20 to 4/22" to separate period_start_date
and period_end_date fields in YYYY-MM-DD format, and adds timestamp.
"""

import csv
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.logger import AppLogger


class SchemaConverter:
    """Convert CSV data from v1.0 to v2.0 schema format"""

    def __init__(self, verbose: bool = False):
        self.logger = AppLogger.get_logger(__name__)
        self.setup_logging(verbose)
        self.current_year = datetime.now().year

    def setup_logging(self, verbose: bool):
        """Setup logging for conversion process"""
        logger_manager = AppLogger()
        logger_manager.setup_logging(verbose=verbose, log_file="schema_conversion.log")

    def parse_date_range(self, date_str: str) -> Tuple[str, str]:
        """
        Parse date range string like "4/20 to 4/22" into start and end dates

        Args:
            date_str: Date range string (e.g., "4/20 to 4/22")

        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        # Pattern to match "M/D to M/D" format
        pattern = r'(\d{1,2})/(\d{1,2})\s+to\s+(\d{1,2})/(\d{1,2})'
        match = re.match(pattern, date_str.strip())

        if not match:
            self.logger.warning(f"Could not parse date range: {date_str}")
            return "", ""

        start_month, start_day, end_month, end_day = match.groups()

        # Convert to YYYY-MM-DD format
        start_date = f"{self.current_year}-{int(start_month):02d}-{int(start_day):02d}"
        end_date = f"{self.current_year}-{int(end_month):02d}-{int(end_day):02d}"

        # Handle year rollover (if end month < start month, assume next year)
        if int(end_month) < int(start_month):
            end_date = f"{self.current_year + 1}-{int(end_month):02d}-{int(end_day):02d}"

        return start_date, end_date

    def convert_currency_to_float(self, currency_str: str) -> float:
        """Convert currency string using DataProcessor helper"""
        from common.helpers import DataProcessor
        return DataProcessor.convert_currency_to_float(currency_str)

    def convert_row(self, row: Dict, timestamp: str) -> Dict:
        """
        Convert a single row from v1.0 to v2.0 format

        Args:
            row: Input row dictionary with v1.0 schema
            timestamp: Current timestamp for data collection

        Returns:
            Converted row dictionary with v2.0 schema
        """
        # One-liner data conversion using DataProcessor helpers
        from common.helpers import DataProcessor
        start_date, end_date = DataProcessor.parse_date_range(row.get('date', ''))
        holofoil_price = self.convert_currency_to_float(row.get('holofoil_price', ''))
        volume = int(row.get('volume', '0')) if row.get('volume', '0').isdigit() else 0
        
        # One-liner row creation with v2.0 schema
        converted_row = {**{k: row.get(k, '') for k in ['set', 'type', 'period', 'name']}, 
                        **{'period_start_date': start_date, 'period_end_date': end_date, 'timestamp': timestamp, 'holofoil_price': holofoil_price, 'volume': volume}}

        return converted_row

    def convert_csv(self, input_path: Path, output_path: Path) -> None:
        """
        Convert entire CSV file from v1.0 to v2.0 schema

        Args:
            input_path: Path to input CSV file (v1.0 format)
            output_path: Path to output CSV file (v2.0 format)
        """
        self.logger.info(f"Converting {input_path} to {output_path}")

        # Generate timestamp for this conversion
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Read input CSV
            with open(input_path, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                rows = list(reader)

            self.logger.info(f"Read {len(rows)} rows from input file")

            # Convert rows
            converted_rows = []
            for i, row in enumerate(rows, 1):
                converted_row = self.convert_row(row, timestamp)
                converted_rows.append(converted_row)

                if i % 100 == 0:
                    self.logger.info(f"Converted {i}/{len(rows)} rows")

            # Write output CSV with v2.0 headers
            v2_headers = [
                'set', 'type', 'period', 'name',
                'period_start_date', 'period_end_date', 'timestamp',
                'holofoil_price', 'volume'
            ]

            with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=v2_headers)
                writer.writeheader()
                writer.writerows(converted_rows)

            self.logger.info(f"Successfully converted {len(converted_rows)} rows to {output_path}")

        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            raise


def main() -> None:
    """Main function with one-liner argument setup"""
    import argparse

    parser = argparse.ArgumentParser(description='Convert CSV from v1.0 to v2.0 schema')
    # One-liner argument configuration
    args_config = [('input_file', {'help': 'Input CSV file (v1.0 format)'}), ('output_file', {'help': 'Output CSV file (v2.0 format)'}), ('--verbose', {'action': 'store_true', 'help': 'Enable verbose logging'})]
    [parser.add_argument(name, **kwargs) for name, kwargs in args_config]

    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)

    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist")
        sys.exit(1)

    converter = SchemaConverter(verbose=args.verbose)
    converter.convert_csv(input_path, output_path)

    print(f"Conversion complete: {input_path} -> {output_path}")


if __name__ == '__main__':
    main()