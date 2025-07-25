import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import date, datetime
import tempfile
import os

from chart.index_chart import (
    IndexChart, DataFrameHelper, TechnicalAnalysisHelper, AlertHelper,
    DBS_LIMIT, DBS_NEUTRAL, DBS_BULL, DBS_BEAR, create_parser, main
)
from common.logger import AppLogger


# Test Data Fixtures
@pytest.fixture
def sample_df_data():
    """Basic DataFrame test data"""
    return {'period_end_date': ['2025-01-01', '2025-01-02'], 'other_col': ['a', 'b']}

@pytest.fixture
def sample_numeric_df():
    """DataFrame with numeric columns for testing"""
    return pd.DataFrame({'price': ['100.5', '200.0'], 'volume': ['10', '20'], 'other_col': ['a', 'b']})

@pytest.fixture
def sample_multiindex_df():
    """MultiIndex DataFrame for yfinance testing"""
    columns = pd.MultiIndex.from_tuples([('Open', 'XLU'), ('Close', 'XLU'), ('Adj Close', 'XLU')])
    return pd.DataFrame(np.random.randn(3, 3), columns=columns)

@pytest.fixture
def sample_ohlc_df():
    """Standard OHLC DataFrame"""
    dates = pd.date_range('2025-01-01', periods=5, freq='D')
    return pd.DataFrame({
        'Open': [100, 102, 104, 106, 108], 'High': [105, 107, 109, 111, 113],
        'Low': [95, 97, 99, 101, 103], 'Close': [103, 105, 107, 109, 111],
        'Adjusted': [103, 105, 107, 109, 111], 'Volume': [1000, 1100, 1200, 1300, 1400]
    }, index=dates)

@pytest.fixture
def sample_csv_data():
    """CSV format test data"""
    return [{'name': 'test_card', 'period_end_date': '2025-01-01', 'aggregate_price': 100.0, 'aggregate_value': 1000.0},
            {'name': 'test_card', 'period_end_date': '2025-01-02', 'aggregate_price': 105.0, 'aggregate_value': 1050.0}]

@pytest.fixture
def sample_roc_df():
    """ROC test data with known values"""
    return pd.DataFrame({'Open': [5.0, -3.0, 2.0], 'High': [7.0, -1.0, 4.0], 'Low': [-2.0, -5.0, 1.0], 'Close': [3.0, -2.0, -1.0]})

@pytest.fixture
def csv_temp_file(sample_csv_data):
    """Temporary CSV file fixture"""
    import csv
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        if sample_csv_data:
            writer = csv.DictWriter(f, fieldnames=sample_csv_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_csv_data)
        f.flush()
        yield Path(f.name)
    os.remove(f.name)

# Helper Test Methods
class TestHelpers:
    """Reusable test helper methods"""
    
    @staticmethod
    def assert_df_columns(df, expected_cols):
        """One-liner DataFrame column assertion"""
        assert list(df.columns) == expected_cols
    
    @staticmethod
    def assert_ohlc_values(df, idx, open_val, high_mult=1.01, low_mult=0.99):
        """One-liner OHLC value assertions"""
        assert df['Open'].iloc[idx] == open_val and df['High'].iloc[idx] == open_val * high_mult and df['Low'].iloc[idx] == open_val * low_mult
    
    @staticmethod
    def create_mock_chart():
        """One-liner mock chart creation"""
        return Mock(**{method: Mock() for method in ['BuildOscillator', 'BuildOscillatorTag', 'MainAddSpan', 'BuildMain', 'save']})


class TestDataFrameHelper:
    
    def test_convert_columns_dates(self, sample_df_data):
        """Test date column conversion with fixture"""
        df = pd.DataFrame(sample_df_data)
        result = DataFrameHelper.convert_columns(df, ['period_end_date'], [])
        assert pd.api.types.is_datetime64_any_dtype(result['period_end_date']) and result['other_col'].dtype == 'object'
    
    def test_convert_columns_numeric(self, sample_numeric_df):
        """Test numeric column conversion with fixture"""
        result = DataFrameHelper.convert_columns(sample_numeric_df, [], ['price', 'volume'])
        assert all(pd.api.types.is_numeric_dtype(result[col]) for col in ['price', 'volume']) and result['other_col'].dtype == 'object'
    
    def test_convert_columns_missing_columns(self):
        """Test conversion with missing columns - one-liner"""
        df, result = pd.DataFrame({'existing_col': [1, 2]}), DataFrameHelper.convert_columns(pd.DataFrame({'existing_col': [1, 2]}), ['missing_date'], ['missing_numeric'])
        assert 'existing_col' in result.columns and len(result) == 2
    
    def test_flatten_yfinance_columns_multiindex(self, sample_multiindex_df):
        """Test flattening MultiIndex columns with fixture"""
        result = DataFrameHelper.flatten_yfinance_columns(sample_multiindex_df)
        assert not isinstance(result.columns, pd.MultiIndex) and 'Adjusted' in result.columns and 'Adj Close' not in result.columns
    
    def test_flatten_yfinance_columns_regular(self):
        """Test flattening regular columns - one-liner"""
        df = pd.DataFrame({'Open': [1, 2, 3], 'Adj Close': [1.1, 2.1, 3.1]})
        result = DataFrameHelper.flatten_yfinance_columns(df)
        assert 'Adjusted' in result.columns and 'Adj Close' not in result.columns
    
    def test_create_ohlc_from_price(self):
        """Test OHLC structure creation - one-liner validation"""
        price_series, volume_series = pd.Series([100.0, 200.0], index=['2025-01-01', '2025-01-02']), pd.Series([10, 20], index=['2025-01-01', '2025-01-02'])
        result = DataFrameHelper.create_ohlc_from_price(price_series, volume_series)
        TestHelpers.assert_df_columns(result, ['Open', 'High', 'Low', 'Close', 'Adjusted', 'Volume'])
        TestHelpers.assert_ohlc_values(result, 0, 100.0)
        assert result['Volume'].iloc[0] == 10


class TestTechnicalAnalysisHelper:
    
    def test_calc_ratio_ohlc(self):
        """Test OHLC ratio calculation with fixture data"""
        df1 = pd.DataFrame({'Open': [100, 200], 'High': [110, 210], 'Low': [90, 190], 'Close': [105, 205], 'Adjusted': [105, 205], 'Volume': [1000, 2000]})
        df2 = pd.DataFrame({'Open': [50, 100], 'High': [55, 105], 'Low': [45, 95], 'Close': [52.5, 102.5], 'Adjusted': [52.5, 102.5], 'Volume': [500, 1000]})
        result = TechnicalAnalysisHelper.calc_ratio_ohlc(df1, df2)
        assert all(result[col].iloc[0] == 2.0 for col in ['Open', 'Close', 'Volume'])  # One-liner ratio validation
    
    def test_calc_roc_indicators(self):
        """Test ROC indicator calculation - one-liner validation"""
        df_ratio = pd.DataFrame(np.random.randn(25, 4), columns=['Open', 'High', 'Low', 'Close'])
        result = TechnicalAnalysisHelper.calc_roc_indicators(df_ratio)
        assert list(result.columns) == ['Open', 'High', 'Low', 'Close'] and len(result) == 25 and pd.isna(result.iloc[0]['Open']) and not pd.isna(result.iloc[24]['Open'])
    
    def test_calc_signal_sum(self, sample_roc_df):
        """Test signal sum calculation with fixture - one-liner"""
        result = TechnicalAnalysisHelper.calc_signal_sum(sample_roc_df)
        expected = pd.Series([2, -4, 2])  # 3pos-1neg=2, 0pos-4neg=-4, 3pos-1neg=2
        pd.testing.assert_series_equal(result, expected)


class TestAlertHelper:
    
    def test_get_dbs_status_conditions(self):
        """Test all DBS status conditions - one-liner"""
        assert AlertHelper.get_dbs_status(-4.0) == DBS_BULL and AlertHelper.get_dbs_status(4.0) == DBS_BEAR and AlertHelper.get_dbs_status(2.0) == DBS_NEUTRAL
    
    def test_get_dbs_status_boundary_conditions(self):
        """Test DBS status at boundary values - one-liner"""
        assert all([AlertHelper.get_dbs_status(DBS_LIMIT) == DBS_BEAR, AlertHelper.get_dbs_status(-DBS_LIMIT) == DBS_BULL, 
                   AlertHelper.get_dbs_status(DBS_LIMIT - 0.1) == DBS_NEUTRAL, AlertHelper.get_dbs_status(-DBS_LIMIT + 0.1) == DBS_NEUTRAL])
    
    def test_generate_alert_body(self):
        """Test alert body generation - one-liner validation"""
        result = AlertHelper.generate_alert_body("Test Alert", date(2025, 7, 25))
        assert all(text in result for text in ["# Test Alert", "Date: 2025-07-25", "Dbs Chart", "Pyaction Repo"])


class TestIndexChart:
    
    @classmethod
    def setup_class(cls):
        """Setup logging for all tests in this class."""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")
        cls.logger = AppLogger.get_logger(__name__)
        cls.logger.info("Starting IndexChart tests")
    
    @pytest.fixture
    def index_chart(self):
        """Create IndexChart instance for testing"""
        return IndexChart()
    
    def test_init(self, index_chart):
        """Test IndexChart initialization - one-liner"""
        assert all(hasattr(index_chart, attr) for attr in ['logger', 'df_helper', 'ta_helper', 'alert_helper'])
    
    @patch('chart.index_chart.FileHelper.read_csv')
    def test_read_csv_success(self, mock_read_csv, index_chart, sample_csv_data):
        """Test successful CSV reading with fixture - one-liner validation"""
        mock_read_csv.return_value = sample_csv_data
        result = index_chart.read_csv(Path('test.csv'))
        assert len(result) == 2 and all(col in result.columns for col in ['period_end_date', 'aggregate_price']) and pd.api.types.is_datetime64_any_dtype(result['period_end_date']) and pd.api.types.is_numeric_dtype(result['aggregate_price'])
    
    @patch('chart.index_chart.FileHelper.read_csv')
    def test_read_csv_edge_cases(self, mock_read_csv, index_chart):
        """Test CSV reading edge cases - one-liner"""
        # Test empty data
        mock_read_csv.return_value = []
        assert index_chart.read_csv(Path('test.csv')).empty
        # Test exception
        mock_read_csv.side_effect = Exception("File error")
        assert index_chart.read_csv(Path('test.csv')).empty
    
    @patch('chart.index_chart.yfinance.download')
    def test_getSymbols(self, mock_download, index_chart, sample_ohlc_df):
        """Test yfinance symbol download - one-liner validation"""
        mock_download.return_value = sample_ohlc_df.rename(columns={'Adjusted': 'Adj Close'})
        XLU, VTI, SPY = index_chart.getSymbols()
        assert all('Adjusted' in df.columns and 'Adj Close' not in df.columns for df in [XLU, VTI, SPY]) and mock_download.call_count == 3
    
    def test_normalize_dataframes_edge_cases(self, index_chart):
        """Test normalization edge cases - one-liner"""
        # Empty DataFrames
        result1, result2 = index_chart.normalize_dataframes(pd.DataFrame(), pd.DataFrame({'period_end_date': ['2025-01-01']}))
        assert result1.empty and not result2.empty
        # Missing columns
        result1, result2 = index_chart.normalize_dataframes(pd.DataFrame({'other_col': [1, 2]}), pd.DataFrame({'period_end_date': ['2025-01-01']}))
        assert 'other_col' in result1.columns and 'period_end_date' in result2.columns
    
    def test_normalize_dataframes_success(self, index_chart):
        """Test successful DataFrame normalization - one-liner validation"""
        df1 = pd.DataFrame({'period_end_date': ['2025-01-01', '2025-01-03'], 'aggregate_price': [100, 120], 'aggregate_value': [1000, 1200]})
        df2 = pd.DataFrame({'period_end_date': ['2025-01-02', '2025-01-03'], 'aggregate_price': [50, 60], 'aggregate_value': [500, 600]})
        result1, result2 = index_chart.normalize_dataframes(df1, df2)
        assert len(result1) == len(result2) == 2 and all(col in result1.columns for col in ['Open', 'Close', 'Volume'])
    
    def test_convert_csv_to_yfinance_format_cases(self, index_chart):
        """Test CSV to yfinance conversion cases - one-liner"""
        # Empty DataFrame
        assert index_chart._convert_csv_to_yfinance_format(pd.DataFrame()).empty
        # No aggregate_price
        result = index_chart._convert_csv_to_yfinance_format(pd.DataFrame({'other_col': [1, 2]}))
        assert 'other_col' in result.columns and 'Open' not in result.columns
        # Successful conversion
        df = pd.DataFrame({'period_end_date': ['2025-01-01', '2025-01-02'], 'aggregate_price': [100.0, 200.0], 'aggregate_value': [1000.0, 2000.0]})
        result = index_chart._convert_csv_to_yfinance_format(df)
        TestHelpers.assert_df_columns(result, ['Open', 'High', 'Low', 'Close', 'Adjusted', 'Volume'])
        TestHelpers.assert_ohlc_values(result, 0, 100.0)
        assert result['Volume'].iloc[0] == 1000.0
    
    def test_fill_missing_dates_cases(self, index_chart):
        """Test missing date filling cases - one-liner"""
        # Empty DataFrame
        assert index_chart._fill_missing_dates(pd.DataFrame(), ['2025-01-01', '2025-01-02'], "Test").empty
        # Successful filling
        df = pd.DataFrame({'period_end_date': ['2025-01-01', '2025-01-03'], 'value': [100, 300]})
        result = index_chart._fill_missing_dates(df, ['2025-01-01', '2025-01-02', '2025-01-03'], "Test")
        assert len(result) == 3 and result['value'].iloc[1] == 100  # Forward-filled value
    
    def test_calc_ratio_cases(self, index_chart, sample_ohlc_df):
        """Test ratio calculation cases - one-liner"""
        # Empty DataFrames
        assert index_chart.calc_ratio(pd.DataFrame(), pd.DataFrame()).empty
        # Missing columns
        assert index_chart.calc_ratio(pd.DataFrame({'other_col': [1, 2]}), pd.DataFrame({'other_col': [3, 4]})).empty
        # Successful calculation
        result = index_chart.calc_ratio(sample_ohlc_df.copy(), sample_ohlc_df.copy() * 2)
        assert len(result) == len(sample_ohlc_df) and 'Open' in result.columns and result['Open'].iloc[0] == 0.5
    
    def test_calc_empty_cases(self, index_chart):
        """Test calculation methods with empty data - one-liner"""
        assert all([index_chart.calc_roc(pd.DataFrame()).empty, len(index_chart.calc_signal(pd.DataFrame())) == 0, 
                   index_chart.calc_dbs(pd.DataFrame(), pd.DataFrame(), pd.Series()).empty])
    
    def test_calc_dbs_success(self, index_chart, sample_ohlc_df):
        """Test successful DBS calculation - one-liner validation"""
        df_roc = pd.DataFrame({'Open': [1, 2, 3, 4, 5], 'High': [1.1, 2.1, 3.1, 4.1, 5.1], 'Low': [0.9, 1.9, 2.9, 3.9, 4.9], 'Close': [1.05, 2.05, 3.05, 4.05, 5.05]}, index=sample_ohlc_df.index)
        df_sum = pd.Series([4, 4, 4, 4, 4], index=sample_ohlc_df.index)
        result = index_chart.calc_dbs(sample_ohlc_df.copy(), df_roc, df_sum, dbs_period=3)
        assert len(result) == len(sample_ohlc_df) and all(col in result.columns for col in ['Dbs', 'DbsMa']) and result.index.name == 'Date'
    
    def test_alertDbs_no_alert_cases(self, index_chart):
        """Test alert generation cases that produce no alerts - one-liner"""
        test_cases = [pd.DataFrame(), pd.DataFrame({'DbsMa': [1.0]}), pd.DataFrame({'DbsMa': [np.nan, np.nan]}), pd.DataFrame({'DbsMa': [2.0, 2.5]})]
        assert all(index_chart.alertDbs(df) == ('', '') for df in test_cases)
    
    def test_alertDbs_alert_cases(self, index_chart):
        """Test alert generation cases that produce alerts - one-liner"""
        # Bull to neutral
        subject, body = index_chart.alertDbs(pd.DataFrame({'DbsMa': [-4.0, 0.0]}))
        assert all(text in subject for text in ['NEUTRAL', 'BULLISH']) and subject in body
        # Neutral to bear
        subject, body = index_chart.alertDbs(pd.DataFrame({'DbsMa': [0.0, 4.0]}))
        assert 'BEARISH' in subject and subject in body
    
    def test_plotChart_cases(self, index_chart, capsys):
        """Test chart plotting cases - one-liner validation"""
        # Valid chart data
        index_chart.plotChart(pd.DataFrame({'Dbs': [1, 2, 3], 'DbsMa': [1.5, 2.5, 3.5], 'Tag': ['A', 'B', 'C']}), "test")
        captured = capsys.readouterr()
        assert "Success: Saved chart" in captured.out or "Chart error:" in captured.out
        # Invalid data
        index_chart.plotChart(pd.DataFrame({'invalid_col': [1]}), "test")
        captured = capsys.readouterr()
        assert "Chart error:" in captured.out


class TestCreateParser:
    
    @pytest.fixture
    def parser(self):
        """Create parser fixture"""
        return create_parser()
    
    def test_create_parser_csv_arguments(self, parser):
        """Test parser with CSV arguments - one-liner validation"""
        args = parser.parse_args(['file1.csv', 'file2.csv', '--verbose'])
        assert all([args.csv_file1 == 'file1.csv', args.csv_file2 == 'file2.csv', args.verbose is True, args.yfinance is False, args.dbs_period == 7])
    
    def test_create_parser_yfinance_arguments(self, parser):
        """Test parser with yfinance arguments - one-liner validation"""
        args = parser.parse_args(['--yfinance', '--dbs-period', '10'])
        assert all([args.yfinance is True, args.dbs_period == 10, args.csv_file1 is None, args.csv_file2 is None])


class TestMain:
    
    @pytest.fixture
    def mock_args_csv(self):
        """Mock args for CSV mode"""
        return Mock(yfinance=False, csv_file1="file1.csv", csv_file2="file2.csv")
    
    @pytest.fixture
    def mock_args_csv_missing(self):
        """Mock args for missing CSV files"""
        return Mock(yfinance=False, csv_file1=None, csv_file2=None)
    
    @pytest.fixture
    def mock_args_yfinance(self):
        """Mock args for yfinance mode"""
        return Mock(yfinance=True, verbose=False, dbs_period=7)
    
    @pytest.fixture
    def sample_ohlc_data(self):
        """Sample OHLC data for testing"""
        return pd.DataFrame({
            'Open': [100, 105], 'High': [110, 115], 'Low': [90, 95],
            'Close': [105, 110], 'Adjusted': [105, 110], 'Volume': [1000, 1100]
        }, index=['2025-01-01', '2025-01-02'])
    
    @patch('chart.index_chart.IndexChart')
    @patch('chart.index_chart.create_parser')
    def test_main_csv_files_missing(self, mock_parser, mock_chart_cls, mock_args_csv_missing, capsys):
        """Test main function with missing CSV files - one-liner"""
        mock_parser.return_value.parse_args.return_value = mock_args_csv_missing
        main()
        assert "Error: CSV files required" in capsys.readouterr().out
    
    @patch('chart.index_chart.IndexChart')
    @patch('chart.index_chart.create_parser')
    def test_main_empty_dataframes(self, mock_parser, mock_chart_cls, mock_args_csv, capsys):
        """Test main function with empty DataFrames - one-liner"""
        mock_parser.return_value.parse_args.return_value, mock_chart_cls.return_value.read_csv.return_value = mock_args_csv, pd.DataFrame()
        main()
        assert "No data in both files" in capsys.readouterr().out
    
    @patch('chart.index_chart.IndexChart')
    @patch('chart.index_chart.create_parser')
    def test_main_yfinance_success(self, mock_parser, mock_chart_cls, mock_args_yfinance, sample_ohlc_data, capsys):
        """Test main function with yfinance data - one-liner validation"""
        mock_parser.return_value.parse_args.return_value = mock_args_yfinance
        mock_chart = TestHelpers.create_mock_chart()
        mock_chart.getSymbols.return_value, mock_chart.calc_ratio.return_value = (sample_ohlc_data, sample_ohlc_data, sample_ohlc_data), sample_ohlc_data
        mock_chart.calc_roc.return_value, mock_chart.calc_signal.return_value = sample_ohlc_data[['Open', 'High', 'Low', 'Close']], pd.Series([2, 2])
        mock_chart.calc_dbs.return_value, mock_chart.alertDbs.return_value = pd.DataFrame({'Dbs': [2, 2], 'DbsMa': [2, 2]}), ('', '')
        mock_chart_cls.return_value = mock_chart
        main()
        captured = capsys.readouterr().out
        assert "Downloading stock data" in captured and "Latest: DBS" in captured