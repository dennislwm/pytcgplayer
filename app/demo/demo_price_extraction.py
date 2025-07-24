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
import re


def extract_price_table_flexible(content: str):
    """Extract price table looking for both 'Date | Holofoil' and 'Date | Normal' formats"""
    # Try original format first (Date | Holofoil)
    holofoil_pattern = r'\|\s*Date\s*\|\s*Holofoil\s*\|.*?(?=\n\n|\n(?!\|)|\Z)'
    match = re.search(holofoil_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(0).strip(), 'holofoil'
    
    # Try alternative format (Date | Normal)
    normal_pattern = r'\|\s*Date\s*\|\s*Normal\s*\|.*?(?=\n\n|\n(?!\|)|\Z)'
    match = re.search(normal_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(0).strip(), 'normal'
    
    return None, None


def parse_price_data_flexible(table_content: str, table_type: str):
    """Parse price data from table content, handling both holofoil and normal formats"""
    data_rows = []
    lines = table_content.split('\n')
    
    # Skip header and separator lines
    data_lines = [line.strip() for line in lines[2:] if line.strip() and line.strip().startswith('|')]
    
    for line in data_lines:
        # Split by | and clean up
        parts = [part.strip() for part in line.split('|')]
        if len(parts) >= 4:  # | Date | Price | Volume |
            date = parts[1].strip()
            price = parts[2].strip()
            volume = parts[3].strip() if len(parts) > 3 else ""
            
            # Create consistent format regardless of table type
            row = {
                'date': date,
                'holofoil': price,  # Always use 'holofoil' key for consistency
                'price': volume     # Volume goes in 'price' field for consistency
            }
            data_rows.append(row)
    
    return data_rows


def main():
    # Setup logging
    logger = AppLogger()
    logger.setup_logging(verbose=True, log_file="demo.log")
    log = AppLogger.get_logger(__name__)
    
    log.info("Starting TCGPlayer price history extraction demo")
    
    # Get response file from command line argument or use default
    response_filename = sys.argv[1] if len(sys.argv) > 1 else "response_01.md"
    response_file = Path(response_filename)
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
    
    # Extract price history table using flexible approach
    print("\n1. Extracting price history table...")
    table_content, table_type = extract_price_table_flexible(content)
    
    if table_content:
        print(f"✓ Successfully extracted table with {len(table_content.split())} lines")
        print(f"  Table format detected: 'Date | {table_type.title()}'")
        
        # Show first few lines
        lines = table_content.split('\n')
        print("\nFirst 5 lines of extracted table:")
        for i, line in enumerate(lines[:5]):
            print(f"  {line}")
        
        if len(lines) > 5:
            print(f"  ... and {len(lines) - 5} more lines")
    else:
        print("✗ No price history table found (tried both 'Date | Holofoil' and 'Date | Normal' formats)")
        return 1
    
    # Parse into structured data using flexible parser
    print("\n2. Parsing structured data...")
    data_rows = parse_price_data_flexible(table_content, table_type)
    
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