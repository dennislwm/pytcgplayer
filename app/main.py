#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from common.processor import CsvProcessor
from common.csv_writer import CsvWriter
from common.logger import AppLogger




def main():
    parser = argparse.ArgumentParser(
        description='Process CSV data with web requests and markdown parsing'
    )
    parser.add_argument(
        'input_file',
        type=Path,
        help='Input CSV file path'
    )
    parser.add_argument(
        'output_file',
        type=Path,
        help='Output CSV file path'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Initialize centralized logging
    app_logger = AppLogger()
    app_logger.setup_logging(verbose=args.verbose, log_file="app.log")
    logger = AppLogger.get_logger(__name__)
    
    if not args.input_file.exists():
        logger.error(f"Input file '{args.input_file}' does not exist")
        sys.exit(1)
    
    processor = CsvProcessor()
    writer = CsvWriter()
    
    try:
        results = processor.process(args.input_file)
        writer.write(results, args.output_file)
        logger.info(f"Processing complete. Output saved to: {args.output_file}")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()