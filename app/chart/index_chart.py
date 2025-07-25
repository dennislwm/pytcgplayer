#!/usr/bin/env python3
"""
Index Chart for TCGPlayer Price Data

Compares and charts time series data from two CSV files.
Usage: python chart/index_chart.py file1.csv file2.csv [options]
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
from ta.momentum import ROCIndicator
from datetime import date, timedelta
import yfinance

# DBS constants from pymonitor
DBS_LIMIT = 3.75
DBS_PERIOD = 7   # consider 7-12
DBS_NEUTRAL = 'NEUTRAL'
DBS_BULL = 'BULLISH'
DBS_BEAR = 'BEARISH'

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.helpers import FileHelper, DataProcessor
from common.logger import AppLogger


class DataFrameHelper:
    """Helper class for DataFrame operations and transformations"""
    
    @staticmethod
    def convert_columns(df: pd.DataFrame, date_cols: list, numeric_cols: list) -> pd.DataFrame:
        """One-liner column conversion for dates and numeric values"""
        for col in date_cols: df[col] = pd.to_datetime(df[col], errors='coerce') if col in df.columns else None
        for col in numeric_cols: df[col] = pd.to_numeric(df[col], errors='coerce') if col in df.columns else None
        return df
    
    @staticmethod
    def flatten_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
        """One-liner to flatten MultiIndex columns and rename Adj Close"""
        return (df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df).rename(columns={'Adj Close': 'Adjusted'})
    
    @staticmethod
    def create_ohlc_from_price(price_series: pd.Series, volume_series: pd.Series) -> pd.DataFrame:
        """One-liner OHLC structure creation from single price series"""
        return pd.DataFrame({'Open': price_series, 'High': price_series * 1.01, 'Low': price_series * 0.99, 
                           'Close': price_series, 'Adjusted': price_series, 'Volume': volume_series}, index=price_series.index)


class TechnicalAnalysisHelper:
    """Helper class for technical analysis calculations"""
    
    @staticmethod
    def calc_ratio_ohlc(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """One-liner ratio calculation for OHLC data"""
        return pd.DataFrame({col: df1[col] / df2[col] for col in ['Open', 'High', 'Low', 'Close', 'Adjusted', 'Volume']}, index=df1.index)
    
    @staticmethod
    def calc_roc_indicators(df_ratio: pd.DataFrame) -> pd.DataFrame:
        """One-liner ROC calculation for all OHLC columns"""
        roc_data = {col: ROCIndicator(close=df_ratio[col], n=20).roc() for col in ['Open', 'High', 'Low', 'Close']}
        return pd.DataFrame(roc_data)
    
    @staticmethod
    def calc_signal_sum(df_roc: pd.DataFrame) -> pd.Series:
        """One-liner signal calculation as sum of boolean indicators"""
        return sum((df_roc[col] >= 0).astype(int) - (df_roc[col] < 0).astype(int) for col in df_roc.columns)


class AlertHelper:
    """Helper class for alert generation"""
    
    @staticmethod
    def get_dbs_status(value: float) -> str:
        """One-liner DBS status determination"""
        return DBS_BEAR if value >= DBS_LIMIT else DBS_BULL if value <= -DBS_LIMIT else DBS_NEUTRAL
    
    @staticmethod
    def generate_alert_body(subject: str, today: date) -> str:
        """One-liner alert body generation"""
        return f"# {subject}\n\nDate: {today}\n\n[Dbs Chart](https://github.com/dennislwm/pyaction/blob/master/_ChartC_0.1_Dbs.png)\n\n[Pyaction Repo](https://github.com/dennislwm/pyaction)"


class IndexChart:
    """Charts and compares time series data from two CSV files using pandas"""

    def __init__(self):
        self.logger = AppLogger.get_logger(__name__)
        self.df_helper = DataFrameHelper()
        self.ta_helper = TechnicalAnalysisHelper()
        self.alert_helper = AlertHelper()

    def read_csv(self, input_path: Path) -> pd.DataFrame:
        """Read CSV file into pandas DataFrame with automatic type conversion"""
        self.logger.info(f"Reading CSV from {input_path}")
        try:
            data = FileHelper.read_csv(input_path)
            if not data: return self.logger.error(f"No data found in {input_path}") or pd.DataFrame()
            
            df = self.df_helper.convert_columns(
                pd.DataFrame(data),
                ['period_start_date', 'period_end_date', 'timestamp'],
                ['holofoil_price', 'volume', 'aggregate_price', 'aggregate_value']
            )
            
            self.logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
            return df
        except Exception as e:
            return self.logger.error(f"Error reading CSV: {e}") or pd.DataFrame()

    def getSymbols(self):
        """Download data from yfinance with automatic column flattening"""
        today = date.today()
        start_date = today - timedelta(weeks=52)
        symbols = ['XLU', 'VTI', 'SPY']
        
        return tuple(self.df_helper.flatten_yfinance_columns(
            yfinance.download(symbol, auto_adjust=False, start=start_date, end=today)
        ) for symbol in symbols)

    def normalize_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Normalize DataFrames with date alignment and OHLC conversion"""
        if df1.empty or df2.empty or 'period_end_date' not in df1.columns or 'period_end_date' not in df2.columns:
            return (self.logger.warning("Empty DataFrames or missing period_end_date") or (df1, df2))
        
        # One-liner sorting and common date calculation
        df1_sorted, df2_sorted = [df.sort_values('period_end_date').reset_index(drop=True) for df in [df1, df2]]
        common_start_date = max(df1_sorted['period_end_date'].min(), df2_sorted['period_end_date'].min())
        
        self.logger.info(f"Common start date: {common_start_date}")
        
        # One-liner trimming and date union
        df1_trimmed, df2_trimmed = [df[df['period_end_date'] >= common_start_date].copy() for df in [df1_sorted, df2_sorted]]
        all_dates = sorted(set(df1_trimmed['period_end_date'].unique()) | set(df2_trimmed['period_end_date'].unique()))
        
        self.logger.info(f"Total unique dates to align: {len(all_dates)}")
        
        # Fill missing dates and convert to OHLC format
        df1_norm, df2_norm = [self._convert_csv_to_yfinance_format(self._fill_missing_dates(df, all_dates, f"DataFrame {i}")) 
                             for i, df in enumerate([df1_trimmed, df2_trimmed], 1)]
        
        self.logger.info(f"Normalized: {len(df1_norm)} and {len(df2_norm)} records")
        return df1_norm, df2_norm
    
    def _convert_csv_to_yfinance_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert CSV format to yfinance-compatible OHLC format"""
        if df.empty or 'aggregate_price' not in df.columns: return df
        
        self.logger.info("Converting CSV format to yfinance-compatible OHLC format")
        df_indexed = df.set_index('period_end_date')
        
        return self.df_helper.create_ohlc_from_price(
            df_indexed['aggregate_price'], 
            df_indexed.get('aggregate_value', 0)
        )
    
    def _fill_missing_dates(self, df: pd.DataFrame, all_dates: list, df_name: str) -> pd.DataFrame:
        """Fill missing dates using forward-fill"""
        if df.empty: return df
        
        # One-liner merge and forward-fill
        merged_df = pd.DataFrame({'period_end_date': all_dates}).merge(df, on='period_end_date', how='left').ffill()
        filled_count = len(merged_df) - len(df)
        
        if filled_count > 0: self.logger.info(f"{df_name}: filled {filled_count} missing dates")
        return merged_df

    def calc_ratio(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """Calculate ratio between two DataFrames using helper class"""
        self.logger.info("Calculating ratio between DataFrames")
        
        if df1.empty or df2.empty or 'Close' not in df1.columns or 'Close' not in df2.columns:
            return self.logger.error("Empty DataFrames or missing OHLC columns") or pd.DataFrame()
        
        df_ratio = self.ta_helper.calc_ratio_ohlc(df1, df2)
        self.logger.info(f"Calculated ratio DataFrame with {len(df_ratio)} records")
        return df_ratio
    
    def calc_roc(self, df_ratio: pd.DataFrame) -> pd.DataFrame:
        """Calculate rate of change using helper class"""
        self.logger.info("Calculating rate of change indicators")
        if df_ratio.empty: return pd.DataFrame()
        
        df_roc = self.ta_helper.calc_roc_indicators(df_ratio)
        self.logger.info(f"Calculated ROC DataFrame with {len(df_roc)} records")
        return df_roc
    
    def calc_signal(self, df_roc: pd.DataFrame) -> pd.Series:
        """Calculate trading signals using helper class"""
        self.logger.info("Calculating trading signals")
        if df_roc.empty: return pd.Series()
        
        df_sum = self.ta_helper.calc_signal_sum(df_roc)
        self.logger.info(f"Calculated signal series with {len(df_sum)} records")
        return df_sum
    
    def calc_dbs(self, spy_df: pd.DataFrame, df_roc: pd.DataFrame, df_sum: pd.Series, dbs_period: int = 7) -> pd.DataFrame:
        """Create combined DBS DataFrame with moving average"""
        self.logger.info("Creating combined DBS DataFrame")
        if spy_df.empty: return pd.DataFrame()
        
        # One-liner DBS DataFrame creation
        df_ret = pd.concat([spy_df[['Open', 'High', 'Low', 'Close', 'Adjusted', 'Volume']], df_roc, df_sum], axis=1)
        df_ret.index.name, df_ret.columns = 'Date', ['Open', 'High', 'Low', 'Close', 'Adjusted', 'Volume', 'ROC.Open', 'ROC.High', 'ROC.Low', 'ROC.Close', 'Dbs']
        df_ret['DbsMa'] = df_ret['Dbs'].rolling(dbs_period).mean()
        
        self.logger.info(f"Created DBS DataFrame with {len(df_ret)} records")
        return df_ret

    def alertDbs(self, dfRet: pd.DataFrame) -> tuple[str, str]:
        """Generate DBS alerts using helper class"""
        if dfRet.empty or len(dfRet) < 2: return '', ''
        
        # One-liner to get previous and current DBS MA values
        dblPrev, dblCurr = dfRet['DbsMa'].tail(2).values
        if pd.isna(dblPrev) or pd.isna(dblCurr): return '', ''
        
        # One-liner status comparison
        strPrev, strCurr = [self.alert_helper.get_dbs_status(val) for val in [dblPrev, dblCurr]]
        if strPrev == strCurr: return '', ''
        
        # One-liner alert generation
        subject = f'Dbs trend shift to NEUTRAL (bias to {strPrev})' if strCurr == DBS_NEUTRAL else f'Dbs trend shift to {strCurr}'
        body = self.alert_helper.generate_alert_body(subject, date.today())
        
        return subject, body

    def plotChart(self, dfRet: pd.DataFrame, strSuffix: str):
        """Plot and save chart with error handling"""
        try:
            from pyfxgit.ChartCls import ChartCls
            chart = ChartCls(dfRet, intSub=2)
            chart.BuildOscillator(1, dfRet['Dbs'], intUpper=3, intLower=-3, strTitle="Dbs")
            chart.BuildOscillator(0, dfRet['DbsMa'], intUpper=DBS_LIMIT, intLower=-DBS_LIMIT, strTitle="DbsMa")
            lstTag = chart.BuildOscillatorTag(dfRet, 'DbsMa', DBS_LIMIT)
            chart.MainAddSpan(dfRet['Tag'], lstTag[lstTag>0], 0.2, 'red')
            chart.MainAddSpan(dfRet['Tag'], lstTag[lstTag<0], 0.2, 'green')
            chart.BuildMain(strTitle="TCGPlayer Price Analysis")
            chart.save(strSuffix)
            print("Success: Saved chart")
        except (ImportError, Exception) as e:
            print(f"Chart error: {e}")


def create_parser():
    """Create command-line argument parser with one-liner configuration"""
    parser = argparse.ArgumentParser(description='TCGPlayer Price Data Index Chart Comparison', 
                                   formatter_class=argparse.RawDescriptionHelpFormatter,
                                   epilog="Examples:\n  python chart/index_chart.py data/file1.csv data/file2.csv\n  python chart/index_chart.py --yfinance")
    
    # One-liner argument setup
    args_config = [('csv_file1', {'nargs': '?', 'help': 'First CSV file'}), ('csv_file2', {'nargs': '?', 'help': 'Second CSV file'}),
                  ('--yfinance', {'action': 'store_true', 'help': 'Use yfinance data'}), ('--verbose', {'action': 'store_true', 'help': 'Verbose logging'}),
                  ('--dbs-period', {'type': int, 'default': 7, 'help': 'DBS MA period'})]
    [parser.add_argument(name, **kwargs) for name, kwargs in args_config]
    
    return parser


def main():
    """Main entry point with streamlined data processing"""
    args = create_parser().parse_args()
    chart = IndexChart()
    
    # One-liner data source selection
    if args.yfinance:
        print("Downloading stock data from yfinance...")
        df1, df2, spy_data = chart.getSymbols()  # XLU, VTI, SPY
        print(f"Downloaded: XLU({len(df1)}), VTI({len(df2)}), SPY({len(spy_data)}) records")
    else:
        if not args.csv_file1 or not args.csv_file2: return print("Error: CSV files required")
        df1, df2 = [chart.read_csv(Path(f)) for f in [args.csv_file1, args.csv_file2]]
        spy_data = df1.copy()
    
    if not df1.empty and not df2.empty:
        print(f"Loaded: File1({len(df1)}), File2({len(df2)}) records")
        
        # One-liner normalization decision
        df1_norm, df2_norm = (df1, df2) if args.yfinance else chart.normalize_dataframes(df1, df2)
        print(f"{'Using yfinance' if args.yfinance else 'Normalized'}: File1({len(df1_norm)}), File2({len(df2_norm)}) records")
        
        if not df1_norm.empty and not df2_norm.empty:
            print(f"Aligned dates: {df1_norm.index[0]} to {df2_norm.index[0]}")
            
            # One-liner technical analysis pipeline
            print("\\nCalculating technical indicators...")
            df_ratio = chart.calc_ratio(df1_norm, df2_norm)
            df_roc = chart.calc_roc(df_ratio)
            df_sum = chart.calc_signal(df_roc)
            spy_for_dbs = spy_data if args.yfinance else df1_norm
            df_dbs = chart.calc_dbs(spy_for_dbs, df_roc, df_sum, args.dbs_period)
            
            # One-liner debug output
            if args.verbose:
                debug_data = [("ratio", df_ratio), ("roc", df_roc), ("sum", df_sum), ("dbs", df_dbs)]
                [print(f"\\n🔍 {name}: {df.shape}\\n{df.head()}\\n{df.describe() if hasattr(df, 'describe') else 'N/A'}") 
                 for name, df in debug_data if not df.empty]
            
            # One-liner results summary
            results = [len(df) for df in [df_ratio, df_roc, df_sum, df_dbs]]
            print(f"\\nResults: Ratio({results[0]}), ROC({results[1]}), Signals({results[2]}), DBS({results[3]}) records")
            
            if not df_dbs.empty:
                # One-liner latest indicators
                latest_dbs, latest_dbs_ma = df_dbs[['Dbs', 'DbsMa']].iloc[-1].values
                print(f"Latest: DBS({latest_dbs:.2f}), MA({latest_dbs_ma:.2f})")
                
                # One-liner chart and alert
                print("\\nGenerating chart and alerts...")
                chart.plotChart(df_dbs, "TCG_DBS")
                subject, body = chart.alertDbs(df_dbs)
                print(f"Alert: {subject[:50]}..." if subject else "No alerts")
        
    else:
        # One-liner error handling
        error_msg = "No data in both files" if df1.empty and df2.empty else f"No data in {'first' if df1.empty else 'second'} file"
        print(error_msg)


if __name__ == "__main__":
    main()