#!/usr/bin/env python3
"""
Demo script showing the full aggregation workflow
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chart.index_aggregator import IndexAggregator
from common.logger import AppLogger

def main():
    # Setup logging
    logger = AppLogger()
    logger.setup_logging(verbose=True, log_file="demo.log")

    # Create aggregator
    aggregator = IndexAggregator()

    # Path to the main data file
    input_file = Path('data/output.csv')

    print("🔍 Creating time-series aligned subset...")

    # Create subset with SV cards only
    subset_df = aggregator.create_subset(
        input_file,
        sets='S*',      # All Scarlet & Violet sets
        types='*Box',    # Individual cards only
        period='3M'      # 3-month period
    )

    print(f"📊 Subset created: {len(subset_df)} records")
    
    if not subset_df.empty:
        print(f"   Sets: {sorted(subset_df['set'].unique())}")
        print(f"   Products: {subset_df['name'].nunique()} unique products")
        print(f"   Date range: {len(subset_df['period_end_date'].unique())} common periods")
    else:
        print("   No data matches the filters or alignment requirements - exiting")
        return

    print("\n📈 Aggregating into time series...")

    # Aggregate into time series
    ts_df = aggregator.aggregate_time_series(subset_df, "SV_Box_Demo")

    print(f"✅ Time series created: {len(ts_df)} data points")
    print("\nTime Series Preview:")
    print("=" * 75)
    print(f"{'Name':<12} {'Date':<12} {'Avg Price':<12} {'Avg Value':<12}")
    print("-" * 75)

    for _, row in ts_df.head().iterrows():
        date_str = row['period_end_date'].strftime('%Y-%m-%d')
        price = row['aggregate_price']
        value = row['aggregate_value']
        name = row['name']
        print(f"{name:<12} {date_str:<12} ${price:<11.2f} ${value:<11.2f}")

    print("=" * 75)
    print(f"Total periods: {len(ts_df)}")

    # Save the time series
    output_file = Path('data/SV_Box_Demo_time_series.csv')
    aggregator.write_csv(ts_df, output_file)
    print(f"\n💾 Time series saved to: {output_file}")

if __name__ == "__main__":
    main()