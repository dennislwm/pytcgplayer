import csv
from pathlib import Path
from typing import Dict, List

from common.logger import AppLogger


class CsvWriter:
    def __init__(self):
        self.logger = AppLogger.get_logger(__name__)
    
    def write(self, data: List[Dict], output_file: Path) -> None:
        self.logger.info(f"Writing {len(data)} rows to {output_file}")
        
        if not data:
            self.logger.warning("No data to write")
            return
        
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(data)
        
        self.logger.info(f"Successfully wrote CSV file: {output_file}")