import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple

from common.logger import AppLogger
from common.helpers import FileHelper, DataProcessor


class CsvWriter(DataProcessor):
    def __init__(self):
        self.logger = AppLogger.get_logger(__name__)

    def write(self, data: List[Dict], output_file: Path) -> None:
        self.logger.info(f"Writing {len(data)} rows to {output_file}")
        FileHelper.write_csv(data, output_file)
        self.logger.info(f"Successfully wrote CSV file: {output_file}")

    def write_unique(self, data: List[Dict], output_file: Path, key_columns: List[str] = None) -> None:
        """Write data to CSV, updating duplicates based on key columns"""
        self.logger.info(f"Writing {len(data)} rows to {output_file} (checking for duplicates)")

        if not data:
            self.logger.warning("No data to write")
            return

        # Default key columns for TCGPlayer data (v2.0 schema)
        if key_columns is None:
            key_columns = ['set', 'type', 'period', 'name', 'period_start_date', 'period_end_date']

        # Read existing data if file exists
        existing_data = []
        existing_key_to_index = {}

        if output_file.exists():
            self.logger.debug(f"Reading existing data from {output_file}")
            existing_data = FileHelper.read_csv(output_file)
            existing_key_to_index = self.create_key_index(existing_data, key_columns)
            self.logger.info(f"Found {len(existing_data)} existing records")

        # Process new data - add new records or update existing ones
        new_data = []
        updated_count = 0
        added_count = 0
        processed_keys = set()

        for row in data:
            row_key = self.create_key(row, key_columns)

            # Skip if we've already processed this key in the current dataset
            if row_key in processed_keys:
                continue
            processed_keys.add(row_key)

            if row_key in existing_key_to_index:
                # Update existing record
                existing_index = existing_key_to_index[row_key]
                old_holofoil = existing_data[existing_index].get('holofoil_price', '')
                old_volume = existing_data[existing_index].get('volume', '')

                existing_data[existing_index]['holofoil_price'] = row.get('holofoil_price', '')
                existing_data[existing_index]['volume'] = row.get('volume', '')

                self.logger.debug(f"Updated record {row_key}: holofoil {old_holofoil} → {row.get('holofoil_price', '')}, volume {old_volume} → {row.get('volume', '')}")
                updated_count += 1
            else:
                # Add new record
                new_data.append(row)
                added_count += 1

        self.logger.info(f"Updated {updated_count} existing records, adding {added_count} new records")

        # Combine existing and new data
        all_data = existing_data + new_data

        if all_data:
            # Sort all data by fingerprint for consistent output order
            all_data_sorted = sorted(all_data, key=lambda row: self.create_key(row, key_columns))
            FileHelper.write_csv(all_data_sorted, output_file)

            self.logger.info(f"Successfully wrote {len(all_data)} total rows ({added_count} new, {updated_count} updated) to {output_file}")
        else:
            self.logger.warning("No data to write after processing")




