#!/usr/bin/env python3
"""
Demo script showing TCGPlayer price history extraction functionality.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from common
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.markdown_parser import MarkdownParser
from common.csv_writer import CsvWriter
from common.logger import AppLogger


def main():
    # Setup logging
    logger = AppLogger()
    logger.setup_logging(verbose=True, log_file="demo.log")
    log = AppLogger.get_logger(__name__)
    
    log.info("Starting TCGPlayer price history extraction demo")
    
    # Check if response file exists
    response_file = Path("response_01.md")
    if not response_file.exists():
        log.error(f"Response file '{response_file}' not found")
        print(f"Error: {response_file} not found in current directory")
        return 1
    
    # Read the TCGPlayer response
    log.info(f"Reading response from {response_file}")
    with open(response_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Read {len(content)} characters from {response_file}")
    
    # Initialize parser
    parser = MarkdownParser()
    
    # Extract price history table
    print("\n1. Extracting price history table...")
    table_content = parser.extract_price_history_table(content)
    
    if table_content:
        print(f"✓ Successfully extracted table with {len(table_content.split())} lines")
        
        # Show first few lines
        lines = table_content.split('\n')
        print("\nFirst 5 lines of extracted table:")
        for i, line in enumerate(lines[:5]):
            print(f"  {line}")
        
        if len(lines) > 5:
            print(f"  ... and {len(lines) - 5} more lines")
    else:
        print("✗ No price history table found")
        return 1
    
    # Parse into structured data
    print("\n2. Parsing structured data...")
    data_rows = parser.parse_price_history_data(content)
    
    if data_rows:
        print(f"✓ Successfully parsed {len(data_rows)} data rows")
        
        # Show first few rows
        print("\nFirst 3 data rows:")
        for i, row in enumerate(data_rows[:3]):
            print(f"  Row {i+1}: Date='{row['date']}', Holofoil='{row['holofoil']}', Price='{row['price']}'")
        
        if len(data_rows) > 3:
            print(f"  ... and {len(data_rows) - 3} more rows")
    else:
        print("✗ No data rows parsed")
        return 1
    
    # Write to CSV file using normalized format  
    print("\n3. Writing to CSV file (normalized format)...")
    output_file = Path("demo_normalized_output.csv")
    
    # Convert data format for CSV writer (normalized format like the app)
    csv_data = []
    for row in data_rows:
        csv_data.append({
            'set': 'SV08.5',  # Sample metadata
            'type': 'Card',
            'period': '3M', 
            'name': 'Umbreon ex 161',
            'date': row['date'],
            'holofoil_price': row['holofoil'],
            'additional_price': row['price']
        })
    
    writer = CsvWriter()
    writer.write(csv_data, output_file)
    
    print(f"✓ Successfully wrote {len(csv_data)} rows to {output_file}")
    
    # Show file stats
    if output_file.exists():
        file_size = output_file.stat().st_size
        print(f"  Output file size: {file_size} bytes")
        
        # Show first few lines of CSV
        with open(output_file, 'r') as f:
            csv_lines = f.readlines()
        print(f"\nFirst 4 lines of CSV output:")
        for i, line in enumerate(csv_lines[:4]):
            print(f"  {line.strip()}")
        
        if len(csv_lines) > 4:
            print(f"  ... and {len(csv_lines) - 4} more lines")
    
    log.info("Demo completed successfully")
    print(f"\n✓ Demo completed successfully!")
    print(f"  - Extracted table: {len(table_content)} characters")
    print(f"  - Parsed data: {len(data_rows)} rows") 
    print(f"  - Normalized CSV output: demo/{output_file}")
    print(f"  - Format: Each price record as separate row with metadata")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())