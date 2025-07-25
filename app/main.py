#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from common.processor import CsvProcessor
from common.csv_writer import CsvWriter
from common.logger import AppLogger




def main() -> None:
    """Main entry point with one-liner argument setup"""
    parser = argparse.ArgumentParser(description='Process CSV data with web requests and markdown parsing')
    # One-liner argument configuration
    args_config = [('input_file', {'type': Path, 'help': 'Input CSV file path'}), ('output_file', {'type': Path, 'help': 'Output CSV file path'}), ('--verbose', {'action': 'store_true', 'help': 'Enable verbose output'}), ('-v', {'action': 'store_true', 'dest': 'verbose', 'help': 'Enable verbose output (short form)'})]
    [parser.add_argument(name, **kwargs) for name, kwargs in args_config]
    
    args = parser.parse_args()
    
    # One-liner logging setup and file validation
    app_logger = AppLogger()
    app_logger.setup_logging(verbose=args.verbose, log_file="app.log")
    logger = AppLogger.get_logger(__name__)
    
    if not args.input_file.exists():
        logger.error(f"Input file '{args.input_file}' does not exist")
        sys.exit(1)
    
    # One-liner processing workflow
    processor, writer = CsvProcessor(), CsvWriter()
    
    try:
        results = processor.process(args.input_file)
        writer.write_unique(results, args.output_file)
        logger.info(f"Processing complete. Output saved to: {args.output_file}")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()