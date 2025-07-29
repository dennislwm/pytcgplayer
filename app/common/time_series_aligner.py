"""
Time Series Alignment Module

This module provides the TimeSeriesAligner class that handles completeness-only 
time series alignment logic for TCGPlayer price data. It focuses purely on ensuring
complete temporal coverage across all signatures without quality filtering.

The aligner operates on pre-filtered DataFrames and provides:
- Step 1: Find first complete coverage date (optimal temporal starting point)
- Step 2: Fill signature gaps after first complete date (ensure completeness)
- Complete dataset output with all signatures included
"""

import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.logger import AppLogger


class TimeSeriesAligner:
    """
    Handles completeness-only time series alignment for TCGPlayer price data.
    
    This class provides a 2-step alignment process:
    1. Find first complete coverage date (optimal temporal starting point)
    2. Fill signature gaps to ensure complete coverage (all signatures included)
    
    The aligner operates on pre-filtered DataFrames and returns complete datasets
    with all signatures having consistent temporal coverage.
    """
    
    def __init__(self):
        self.logger = AppLogger.get_logger(__name__)
    
    def _1_find_first_complete_coverage_date(self, df: pd.DataFrame, allow_fallback: bool = False) -> tuple[pd.Timestamp, float]:
        """
        Find the first period_end_date where all signatures have complete coverage.
        
        This is the first step in time series alignment - identify the optimal
        starting point where all selected signatures begin to have consistent
        temporal coverage.
        
        Args:
            df: Pre-filtered DataFrame (after user filters applied)
            allow_fallback: If True, use date with maximum coverage when 100% not available
            
        Returns:
            tuple: (optimal_date, coverage_percentage) or (None, 0.0) if no suitable date found
        """
        if df.empty:
            return None, 0.0
        
        # Get all unique signatures directly
        signatures = df.groupby(['set', 'type', 'period', 'name']).size().index.tolist()
        if not signatures:
            return None, 0.0
        
        total_signatures = len(signatures)
        
        # Analyze date coverage across all signatures
        from collections import defaultdict
        date_coverage = defaultdict(list)
        
        # Group by signature to get their date coverage
        grouped = df.groupby(['set', 'type', 'period', 'name'])
        for signature, group in grouped:
            for date in group['period_end_date']:
                date_coverage[date].append(signature)
        
        # Find first date with complete coverage (all signatures present)
        sorted_dates = sorted(date_coverage.keys())
        
        # Look for 100% coverage first
        for date in sorted_dates:
            signatures_on_date = len(date_coverage[date])
            if signatures_on_date == total_signatures:
                coverage_pct = 100.0
                self.logger.info(f"First complete coverage date: {date.strftime('%Y-%m-%d')} with all {total_signatures} signatures ({coverage_pct:.1f}%)")
                return date, coverage_pct
        
        # If no complete coverage found, check fallback behavior
        if allow_fallback:
            # Find date with maximum coverage percentage
            best_date = None
            best_coverage = 0
            best_coverage_pct = 0.0
            
            for date in sorted_dates:
                signatures_on_date = len(date_coverage[date])
                if signatures_on_date > best_coverage:
                    best_date = date
                    best_coverage = signatures_on_date
                    best_coverage_pct = (signatures_on_date / total_signatures) * 100.0
            
            if best_date:
                self.logger.warning(f"No date with 100% coverage found. Using fallback: {best_date.strftime('%Y-%m-%d')} with {best_coverage}/{total_signatures} signatures ({best_coverage_pct:.1f}%)")
                return best_date, best_coverage_pct
        
        # Default: return None for empty DataFrame behavior
        self.logger.warning(f"No date found with complete coverage (100% signatures). Returning empty result.")
        self.logger.info("Use allow_fallback=True to enable maximum coverage fallback mode.")
        return None, 0.0

    def _2_fill_signature_gaps_after_first_complete_date(self, df: pd.DataFrame, first_complete_date: pd.Timestamp, report_coverage: bool = False) -> pd.DataFrame:
        """
        Fill missing signature gaps after the first complete coverage date.
        
        This is the second step in time series alignment - ensure that for each
        period_end_date after the first complete date, there is complete signature
        coverage. Missing signatures are filled with records copied from the most
        recent previous date for that signature.
        
        Args:
            df: Pre-filtered DataFrame (after user filters applied)
            first_complete_date: The first date with complete coverage
            
        Returns:
            DataFrame with gaps filled to ensure complete signature coverage
        """
        if df.empty or first_complete_date is None:
            return df
        
        # Get all unique signatures and dates
        signatures = df.groupby(['set', 'type', 'period', 'name']).size().index.tolist()
        all_dates = sorted(df['period_end_date'].unique())
        
        # Filter dates to only those at or after first complete date
        target_dates = [date for date in all_dates if date >= first_complete_date]
        
        self.logger.info(f"Filling gaps for {len(signatures)} signatures across {len(target_dates)} dates from {first_complete_date.strftime('%Y-%m-%d')}")
        
        # Analyze current coverage
        from collections import defaultdict
        current_coverage = defaultdict(set)
        for _, row in df.iterrows():
            date = row['period_end_date']
            if date >= first_complete_date:
                sig = (row['set'], row['type'], row['period'], row['name'])
                current_coverage[date].add(sig)
        
        # Create list to store gap-fill records
        gap_fill_records = []
        
        # Track the most recent record for each signature (for gap filling)
        signature_latest_record = {}
        
        # Initialize with records from first complete date
        first_date_records = df[df['period_end_date'] == first_complete_date]
        for _, row in first_date_records.iterrows():
            sig = (row['set'], row['type'], row['period'], row['name'])
            signature_latest_record[sig] = row.to_dict()
        
        gaps_filled = 0
        
        # Process each date after first complete date
        for date in target_dates[1:]:  # Skip first date as it's already complete
            missing_signatures = set(signatures) - current_coverage[date]
            
            if missing_signatures:
                self.logger.debug(f"Date {date.strftime('%Y-%m-%d')}: filling {len(missing_signatures)} missing signatures")
                
                for missing_sig in missing_signatures:
                    # Get the most recent record for this signature
                    if missing_sig in signature_latest_record:
                        base_record = signature_latest_record[missing_sig].copy()
                        
                        # Update the date fields for the new record
                        base_record['period_end_date'] = date
                        
                        # Calculate new period_start_date (assuming 3-day periods based on existing data pattern)
                        from datetime import timedelta
                        if 'period_start_date' in base_record:
                            days_diff = (pd.to_datetime(base_record['period_end_date']) - pd.to_datetime(base_record['period_start_date'])).days
                            base_record['period_start_date'] = date - timedelta(days=days_diff)
                        
                        # Update timestamp to indicate this is a gap-filled record
                        base_record['timestamp'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        gap_fill_records.append(base_record)
                        gaps_filled += 1
                        
                        self.logger.debug(f"  Filled gap for {missing_sig[0]} {missing_sig[3][:20]} with price {base_record.get('holofoil_price', 'N/A')}")
            
            # Update latest records with current date data (for next iteration)
            current_date_records = df[df['period_end_date'] == date]
            for _, row in current_date_records.iterrows():
                sig = (row['set'], row['type'], row['period'], row['name'])
                signature_latest_record[sig] = row.to_dict()
        
        # Combine filtered data (from optimal start date) with gap-fill records
        if gap_fill_records:
            gap_fill_df = pd.DataFrame(gap_fill_records)
            # Only include records from optimal start date forward
            filtered_original = df[df['period_end_date'] >= first_complete_date] if first_complete_date else df
            filled_df = pd.concat([filtered_original, gap_fill_df], ignore_index=True)
            self.logger.info(f"Filled {gaps_filled} signature gaps to ensure complete coverage")
            return filled_df.sort_values(['period_end_date', 'set', 'name']).reset_index(drop=True)
        else:
            self.logger.info("No gaps found - complete signature coverage already exists")
            # Return only records from optimal start date forward
            return df[df['period_end_date'] >= first_complete_date] if first_complete_date else df

    def align_permissive(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Legacy method for backward compatibility. 
        Redirects to align_complete for completeness-only alignment.
        """
        return self.align_complete(df)
    
    def align_complete(self, df: pd.DataFrame, allow_fallback: bool = False) -> pd.DataFrame:
        """
        Apply completeness-only time series alignment without quality filtering.
        
        This simplified alignment strategy focuses purely on completeness:
        1. Find first complete coverage date (step 1 - temporal alignment)
        2. Fill signature gaps after first complete date (step 2 - completeness alignment)
        3. Return all signatures with complete coverage (no quality filtering)
        
        Args:
            df: Pre-filtered DataFrame (after user filters applied)
            allow_fallback: If True, use date with maximum coverage when 100% not available
            
        Returns:
            DataFrame with complete time series data, or empty DataFrame if no suitable alignment found
        """
        if df.empty:
            return pd.DataFrame()
        
        # Step 1: Find first complete coverage date for optimal alignment starting point
        first_complete_date, coverage_pct = self._1_find_first_complete_coverage_date(df, allow_fallback)
        if first_complete_date:
            self.logger.info(f"Completeness alignment will use {first_complete_date.strftime('%Y-%m-%d')} as starting reference (coverage: {coverage_pct:.1f}%)")
        
        # Filter input data to start from optimal date before gap filling
        if first_complete_date:
            filtered_df = df[df['period_end_date'] >= first_complete_date].copy()
            removed_count = len(df) - len(filtered_df)
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} records before optimal start date {first_complete_date.strftime('%Y-%m-%d')}")
        else:
            # Default behavior: return empty DataFrame when no suitable alignment found
            self.logger.warning("No suitable alignment date found. Returning empty DataFrame.")
            return pd.DataFrame()
        
        # Step 2: Fill signature gaps after first complete date to ensure completeness
        report_coverage = (coverage_pct < 100.0)  # Report coverage issues when using fallback
        complete_df = self._2_fill_signature_gaps_after_first_complete_date(filtered_df, first_complete_date, report_coverage)
        
        # Log basic completeness metrics and coverage reporting
        if not complete_df.empty:
            signatures = complete_df.groupby(['set', 'type', 'period', 'name']).size()
            total_signatures = len(signatures)
            unique_dates = len(complete_df['period_end_date'].unique())
            total_records = len(complete_df)
            expected_records = total_signatures * unique_dates
            completeness_pct = (total_records / expected_records * 100) if expected_records > 0 else 0
            
            self.logger.info(f"Completeness-only result: {total_records} records, {total_signatures} signatures, {unique_dates} dates")
            self.logger.info(f"Complete dataset coverage: {total_records}/{expected_records} records ({completeness_pct:.1f}%)")
            
            # Report coverage issues for dates that don't meet 100% coverage
            if report_coverage and completeness_pct < 100.0:
                from collections import defaultdict
                date_signature_count = defaultdict(int)
                for _, row in complete_df.iterrows():
                    date_signature_count[row['period_end_date']] += 1
                
                incomplete_dates = []
                for date, count in date_signature_count.items():
                    if count < total_signatures:
                        coverage_pct = (count / total_signatures) * 100.0
                        incomplete_dates.append(f"{date.strftime('%Y-%m-%d')}: {count}/{total_signatures} ({coverage_pct:.1f}%)")
                
                if incomplete_dates:
                    self.logger.warning(f"Dates with incomplete signature coverage: {', '.join(incomplete_dates[:5])}{'...' if len(incomplete_dates) > 5 else ''}")
            
            self.logger.info("All signatures included without quality filtering")
        
        return complete_df