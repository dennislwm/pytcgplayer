#!/usr/bin/env python3
"""
Index Aggregator for TCGPlayer Price Data

Aggregates price data from output.csv into time series analysis.
Usage: python chart/index_aggregator.py data/output.csv --name output_name [options]
Output: data/{name}_time_series.csv
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
from typing import Set
import fnmatch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.helpers import FileHelper
from common.logger import AppLogger
from common.time_series_aligner import TimeSeriesAligner


class FilterValidator:
    """Validates and processes filter patterns"""

    # Known values from data analysis
    VALID_SETS = {
        'SV01', 'SV02', 'SV03', 'SV03.5', 'SV04', 'SV04.5', 'SV05', 'SV06', 'SV06.5',
        'SV07', 'SV08', 'SV08.5', 'SV09', 'SV10', 'SWSH06', 'SWSH07', 'SWSH07.5',
        'SWSH08', 'SWSH09', 'SWSH10', 'SWSH11', 'SWSH12', 'SWSH12.5'
    }
    VALID_TYPES = {'Card', 'Booster Box', 'Elite Trainer Box'}
    VALID_PERIODS = {'3M'}  # Currently only 3M available

    @classmethod
    def _expand_pattern(cls, pattern: str, valid_values: Set[str]) -> Set[str]:
        """One-liner pattern expansion helper for sets and types"""
        return valid_values if pattern == '*' else set().union(*[fnmatch.filter(valid_values, p.strip()) if '*' in p.strip() else {p.strip()} & valid_values for p in pattern.split(',')])

    @classmethod
    def expand_set_pattern(cls, pattern: str) -> Set[str]:
        """Expand set pattern (e.g., 'SV*' -> all SV sets)"""
        return cls._expand_pattern(pattern, cls.VALID_SETS)

    @classmethod
    def expand_type_pattern(cls, pattern: str) -> Set[str]:
        """Expand type pattern (e.g., '*Box' -> both box types)"""
        return cls._expand_pattern(pattern, cls.VALID_TYPES)

    @classmethod
    def validate_period(cls, period: str) -> bool:
        """Validate period value"""
        return period in cls.VALID_PERIODS


class IndexAggregator:
    """Aggregates price data into time series metrics using pandas"""

    def __init__(self):
        self.logger = AppLogger.get_logger(__name__)
        self.aligner = TimeSeriesAligner()

    def read_csv(self, input_path: Path) -> pd.DataFrame:
        """
        Read CSV file into pandas DataFrame using existing FileHelper

        Args:
            input_path: Path to input CSV file

        Returns:
            pandas.DataFrame with datetime index and numeric types
        """
        self.logger.info(f"Reading CSV from {input_path}")

        try:
            # Use existing FileHelper to read CSV as List[Dict]
            data = FileHelper.read_csv(input_path)

            if not data:
                self.logger.error(f"No data found in {input_path}")
                return pd.DataFrame()

            # Convert to pandas DataFrame
            df = pd.DataFrame(data)

            # Use DataFrameHelper for consistent column conversion
            from chart.index_chart import DataFrameHelper
            df = DataFrameHelper.convert_columns(df, ['period_start_date', 'period_end_date', 'timestamp'], ['holofoil_price', 'volume'])

            # Ensure volume is integer
            if 'volume' in df.columns:
                df['volume'] = df['volume'].fillna(0).astype(int)

            self.logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
            return df

        except Exception as e:
            self.logger.error(f"Error reading CSV: {e}")
            return pd.DataFrame()

    def write_csv(self, df: pd.DataFrame, output_path: Path) -> None:
        """
        Write pandas DataFrame to CSV file using existing FileHelper

        Args:
            df: pandas.DataFrame to write
            output_path: Path to output CSV file
        """
        self.logger.info(f"Writing {len(df)} records to {output_path}")

        try:
            # Convert DataFrame to List[Dict] for FileHelper
            data = df.to_dict('records')

            # Use existing FileHelper to write CSV
            FileHelper.write_csv(data, output_path)

            self.logger.info(f"Successfully wrote data to {output_path}")
        except Exception as e:
            self.logger.error(f"Error writing CSV: {e}")

    def apply_filters(self, df: pd.DataFrame, sets: str = '*', types: str = '*', period: str = '3M') -> pd.DataFrame:
        """
        Apply filters to DataFrame

        Args:
            df: Input DataFrame
            sets: Set filter pattern (e.g., 'SV*', 'SV01,SV02', '*')
            types: Type filter pattern (e.g., '*Box', 'Card', '*')
            period: Period filter (currently only '3M')

        Returns:
            Filtered DataFrame
        """
        self.logger.info(f"Applying filters - sets: {sets}, types: {types}, period: {period}")

        # Validate and expand filters with error logging
        valid_sets = FilterValidator.expand_set_pattern(sets)
        valid_types = FilterValidator.expand_type_pattern(types)

        if not valid_sets:
            self.logger.error(f"No valid sets found for pattern: {sets}")
        if not valid_types:
            self.logger.error(f"No valid types found for pattern: {types}")

        if not FilterValidator.validate_period(period):
            self.logger.warning(f"Invalid period: {period}, using default '3M'")
            period = '3M'

        # Apply filters
        filtered_df = df[
            (df['set'].isin(valid_sets)) &
            (df['type'].isin(valid_types)) &
            (df['period'] == period)
        ].copy()

        self.logger.info(f"Filtered from {len(df)} to {len(filtered_df)} records")
        self.logger.info(f"Selected sets: {sorted(valid_sets)}")
        self.logger.info(f"Selected types: {sorted(valid_types)}")

        return filtered_df

    def create_subset(self, input_path: Path, sets: str = '*', types: str = '*', period: str = '3M', allow_fallback: bool = False) -> pd.DataFrame:
        """
        Create a subset of the main dataset using user input filters with completeness-only time series alignment

        Args:
            input_path: Path to input CSV file
            sets: Set filter pattern (e.g., 'SV*', 'SV01,SV02', '*')
            types: Type filter pattern (e.g., '*Box', 'Card', '*')
            period: Period filter (currently only '3M')
            allow_fallback: If True, use date with maximum coverage when 100% not available

        Returns:
            pandas.DataFrame containing the filtered subset with complete time series alignment
            Uses 2-step completeness-only alignment process:
            - Step 1: Find first date with 100% signature coverage (or maximum if fallback enabled)
            - Step 2: Fill signature gaps after optimal start date using forward-fill
            Result: All signatures included with temporal completeness, or empty DataFrame if no suitable alignment
        """
        # Read the dataset using existing method
        df = self.read_csv(input_path)

        if df.empty:
            return pd.DataFrame()

        # Apply filters using existing method
        subset_df = self.apply_filters(df, sets, types, period)

        if subset_df.empty:
            return pd.DataFrame()

        # Use TimeSeriesAligner for completeness-only alignment (Steps 1-2)
        return self.aligner.align_complete(subset_df, allow_fallback)

    def create_complete_subset(self, input_path: Path, sets: str = '*', types: str = '*', period: str = '3M') -> pd.DataFrame:
        """
        Create a subset with only dates that have complete coverage across ALL signatures.

        Unlike create_subset which uses most common date count, this method only includes
        dates where every signature is present (100% coverage).

        Args:
            input_path: Path to input CSV file
            sets: Set filter pattern (e.g., 'SV*', 'SV01,SV02', '*')
            types: Type filter pattern (e.g., '*Box', 'Card', '*')
            period: Period filter (currently only '3M')

        Returns:
            pandas.DataFrame with only dates having complete signature coverage
        """
        self.logger.info(f"Creating complete subset with complete coverage only")

        # Load and apply filters
        df = self.read_csv(input_path)
        subset_df = self.apply_filters(df, sets, types, period)

        if subset_df.empty:
            return pd.DataFrame()

        # Get all unique signatures
        signatures = subset_df.groupby(['set', 'type', 'period', 'name']).ngroups
        total_signatures = len(subset_df.groupby(['set', 'type', 'period', 'name']).groups)

        # Find dates with complete coverage (all signatures present)
        date_coverage = subset_df.groupby('period_end_date').size()
        complete_dates = date_coverage[date_coverage == total_signatures].index

        if len(complete_dates) == 0:
            self.logger.warning("No dates found with complete signature coverage")
            return pd.DataFrame()

        # Return only records for dates with complete coverage
        result_df = subset_df[subset_df['period_end_date'].isin(complete_dates)].copy()
        result_df = result_df.sort_values(['period_end_date', 'set', 'name']).reset_index(drop=True)

        self.logger.info(f"Complete subset: {len(result_df)} records across {len(complete_dates)} complete dates")
        return result_df

    def aggregate_time_series(self, subset_df: pd.DataFrame, name: str = None) -> pd.DataFrame:
        """
        Aggregate filtered subset into time series with aggregate price and value

        Args:
            subset_df: Filtered DataFrame from create_subset
            name: User-provided name to include as additional column

        Returns:
            pandas.DataFrame with columns: period_end_date, aggregate_price, aggregate_value, name (if provided)
            - aggregate_price: sum of holofoil_price for each unique period_end_date
            - aggregate_value: sum of market value (holofoil_price * volume) for each unique period_end_date
            - name: user-provided string value for all rows
        """
        if subset_df.empty:
            return pd.DataFrame(columns=['period_end_date', 'aggregate_price', 'aggregate_value'])

        # One-liner market value calculation using DataProcessor pattern
        subset_df_copy = subset_df.copy()
        subset_df_copy['market_value'] = subset_df_copy['holofoil_price'] * subset_df_copy['volume']

        # Group by period_end_date and calculate aggregates
        aggregated = subset_df_copy.groupby('period_end_date').agg({
            'holofoil_price': 'sum',   # aggregate_price
            'market_value': 'sum'      # aggregate_value
        }).reset_index()

        # Rename columns to match specification
        aggregated = aggregated.rename(columns={
            'holofoil_price': 'aggregate_price',
            'market_value': 'aggregate_value'
        })

        # Add name column as first column if provided
        if name:
            aggregated.insert(0, 'name', name)

        # Sort by period_end_date for time series consistency
        aggregated = aggregated.sort_values('period_end_date')

        self.logger.info(f"Aggregated {len(subset_df)} records into {len(aggregated)} time series points")

        return aggregated


def create_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description='TCGPlayer Price Data Index Aggregator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Filter Examples:
  --sets "SV*"              # All Scarlet & Violet sets
  --sets "SWSH*"            # All Sword & Shield sets
  --sets "SV01,SV02"        # Specific sets
  --types "*Box"            # Both box types
  --types "Card"            # Individual cards only
  --types "Booster Box,Card" # Multiple types

Available Sets:
  Scarlet & Violet: SV01, SV02, SV03, SV03.5, SV04, SV04.5, SV05, SV06, SV06.5, SV07, SV08, SV08.5, SV09, SV10
  Sword & Shield: SWSH06, SWSH07, SWSH07.5, SWSH08, SWSH09, SWSH10, SWSH11, SWSH12, SWSH12.5

Available Types: Card, Booster Box, Elite Trainer Box
Available Periods: 3M
        """
    )

    parser.add_argument('input_csv', nargs='?', default='data/output.csv', help='Input CSV file (default: data/output.csv)')
    parser.add_argument('--name', required=True,
                       help='Name for the time series (e.g., SV_Box). Used as column value and saved to data/NAME_time_series.csv')
    parser.add_argument('--sets', default='*',
                       help='Sets filter (default: * for all sets)')
    parser.add_argument('--types', default='*',
                       help='Types filter (default: * for all types)')
    parser.add_argument('--period', default='3M',
                       help='Period filter (default: 3M)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--allow-fallback', action='store_true',
                       help='Enable fallback mode: use date with maximum coverage when 100%% not available')

    return parser


def main() -> None:
    """Main entry point with data directory creation"""
    parser = create_parser()
    args = parser.parse_args()

    input_file = Path(args.input_csv)
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)  # Ensure data directory exists
    output_file = data_dir / f"{args.name}_time_series.csv"
    raw_output_file = data_dir / f"{args.name}_time_series_raw.csv"

    aggregator = IndexAggregator()
    df = aggregator.read_csv(input_file)

    if not df.empty:
        # Create subset with time series alignment
        subset_df = aggregator.create_subset(input_file, args.sets, args.types, args.period, args.allow_fallback)

        if not subset_df.empty:
            # Save the filtered raw subset data, ordered by period_end_date and set
            grouped_subset_df = subset_df.sort_values(['period_end_date', 'set'])
            aggregator.write_csv(grouped_subset_df, raw_output_file)
            print(f"Filtered raw data saved to: {raw_output_file}")

            # Aggregate into time series
            ts_df = aggregator.aggregate_time_series(subset_df, args.name)

            if not ts_df.empty:
                aggregator.write_csv(ts_df, output_file)
                print(f"Time series saved to: {output_file}")
            else:
                print("No time series data could be aggregated")
        else:
            print("No data matches the specified filters")
    else:
        print("No data found in input file")


if __name__ == "__main__":
    main()