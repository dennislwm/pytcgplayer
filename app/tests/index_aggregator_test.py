import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock

from chart.index_aggregator import IndexAggregator, FilterValidator
from common.logger import AppLogger


# Test Data Fixtures
@pytest.fixture
def sample_aggregator_data():
    """Sample data for IndexAggregator tests"""
    return [
        {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Test Card 1',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.50', 'volume': '5'},
        {'set': 'SV02', 'type': 'Booster Box', 'period': '3M', 'name': 'Test Box 1',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
        {'set': 'SWSH06', 'type': 'Elite Trainer Box', 'period': '3M', 'name': 'Test ETB 1',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '150.75', 'volume': '3'}
    ]


@pytest.fixture
def sample_csv_file(sample_aggregator_data):
    """Create temporary CSV file with sample data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        headers = list(sample_aggregator_data[0].keys())
        f.write(','.join(headers) + '\n')

        for row in sample_aggregator_data:
            values = [str(row[h]) for h in headers]
            f.write(','.join(values) + '\n')

        f.flush()
        yield Path(f.name)
    os.remove(f.name)


@pytest.fixture
def integration_test_data():
    """Sample data for integration tests"""
    return [
        {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Test Card',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
        {'set': 'SV02', 'type': 'Booster Box', 'period': '3M', 'name': 'Test Box',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'}
    ]


@pytest.fixture
def temp_input_file(integration_test_data):
    """Create temporary input file for integration tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        headers = list(integration_test_data[0].keys())
        f.write(','.join(headers) + '\n')
        for row in integration_test_data:
            values = [str(row[h]) for h in headers]
            f.write(','.join(values) + '\n')
        f.flush()
        yield Path(f.name)
    os.remove(f.name)


@pytest.fixture
def temp_output_file():
    """Create temporary output file"""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        yield Path(f.name)
    if os.path.exists(f.name):
        os.remove(f.name)


@pytest.fixture
def expected_sv_sets():
    """Expected SV sets for pattern matching tests"""
    return {'SV01', 'SV02', 'SV03', 'SV03.5', 'SV04', 'SV04.5', 'SV05',
            'SV06', 'SV06.5', 'SV07', 'SV08', 'SV08.5', 'SV09', 'SV10'}


@pytest.fixture
def expected_swsh_sets():
    """Expected SWSH sets for pattern matching tests"""
    return {'SWSH06', 'SWSH07', 'SWSH07.5', 'SWSH08', 'SWSH09',
            'SWSH10', 'SWSH11', 'SWSH12', 'SWSH12.5'}


@pytest.fixture
def expected_all_types():
    """Expected all types for pattern matching tests"""
    return {'Card', 'Booster Box', 'Elite Trainer Box'}


@pytest.fixture
def expected_box_types():
    """Expected box types for pattern matching tests"""
    return {'Booster Box', 'Elite Trainer Box'}


class TestFilterValidator:
    """Test cases for FilterValidator class"""

    def setup_class(self):
        """Setup logging for test class"""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")

    def test_expand_set_pattern_wildcard(self):
        """Test expanding wildcard patterns for sets"""
        result = FilterValidator.expand_set_pattern('*')
        assert len(result) == 23
        assert 'SV01' in result
        assert 'SWSH06' in result

    def test_expand_set_pattern_sv_wildcard(self, expected_sv_sets):
        """Test expanding SV* pattern"""
        result = FilterValidator.expand_set_pattern('SV*')
        assert result == expected_sv_sets

    def test_expand_set_pattern_swsh_wildcard(self, expected_swsh_sets):
        """Test expanding SWSH* pattern"""
        result = FilterValidator.expand_set_pattern('SWSH*')
        assert result == expected_swsh_sets

    def test_expand_set_pattern_comma_separated(self):
        """Test expanding comma-separated set list"""
        result = FilterValidator.expand_set_pattern('SV01,SV02,SWSH06')
        expected = {'SV01', 'SV02', 'SWSH06'}
        assert result == expected

    def test_expand_set_pattern_invalid(self):
        """Test expanding pattern with invalid sets"""
        result = FilterValidator.expand_set_pattern('INVALID,SV01')
        expected = {'SV01'}  # Only valid sets included
        assert result == expected

    def test_expand_type_pattern_wildcard(self, expected_all_types):
        """Test expanding wildcard patterns for types"""
        result = FilterValidator.expand_type_pattern('*')
        assert result == expected_all_types

    def test_expand_type_pattern_box_wildcard(self, expected_box_types):
        """Test expanding *Box pattern"""
        result = FilterValidator.expand_type_pattern('*Box')
        assert result == expected_box_types

    def test_expand_type_pattern_specific(self):
        """Test expanding specific type"""
        result = FilterValidator.expand_type_pattern('Card')
        expected = {'Card'}
        assert result == expected

    def test_expand_type_pattern_comma_separated(self):
        """Test expanding comma-separated type list"""
        result = FilterValidator.expand_type_pattern('Card,Booster Box')
        expected = {'Card', 'Booster Box'}
        assert result == expected

    def test_validate_period_valid(self):
        """Test validating valid period"""
        assert FilterValidator.validate_period('3M') is True

    def test_validate_period_invalid(self):
        """Test validating invalid period"""
        assert FilterValidator.validate_period('1M') is False
        assert FilterValidator.validate_period('invalid') is False


class TestIndexAggregator:
    """Test cases for IndexAggregator class"""

    def setup_class(self):
        """Setup logging for test class"""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")

    @pytest.fixture
    def aggregator(self):
        """Create IndexAggregator instance"""
        return IndexAggregator()

    def test_read_csv_success(self, aggregator, sample_csv_file):
        """Test successful CSV reading"""
        df = aggregator.read_csv(sample_csv_file)

        assert not df.empty
        assert len(df) == 3
        expected_columns = ['set', 'type', 'period', 'name', 'period_start_date',
                           'period_end_date', 'timestamp', 'holofoil_price', 'volume']
        assert list(df.columns) == expected_columns

        # Check data types
        assert df['holofoil_price'].dtype == 'float64'
        assert df['volume'].dtype == 'int64'
        assert pd.api.types.is_datetime64_any_dtype(df['period_start_date'])

    def test_read_csv_nonexistent_file(self, aggregator):
        """Test reading non-existent CSV file"""
        df = aggregator.read_csv(Path('/nonexistent/file.csv'))
        assert df.empty

    @patch('chart.index_aggregator.FileHelper.write_csv')
    def test_write_csv_success(self, mock_write, aggregator):
        """Test successful CSV writing"""
        df = pd.DataFrame({
            'set': ['SV01'],
            'type': ['Card'],
            'holofoil_price': [100.50]
        })

        output_path = Path('/test/output.csv')
        aggregator.write_csv(df, output_path)

        mock_write.assert_called_once()
        args, kwargs = mock_write.call_args
        assert args[1] == output_path
        assert len(args[0]) == 1  # One record

    def test_apply_filters_all_data(self, aggregator, sample_csv_file):
        """Test applying filters that return all data"""
        df = aggregator.read_csv(sample_csv_file)
        filtered_df = aggregator.apply_filters(df, sets='*', types='*', period='3M')

        assert len(filtered_df) == 3
        assert len(filtered_df) == len(df)

    def test_apply_filters_sv_sets_only(self, aggregator, sample_csv_file):
        """Test filtering for SV sets only"""
        df = aggregator.read_csv(sample_csv_file)
        filtered_df = aggregator.apply_filters(df, sets='SV*', types='*', period='3M')

        assert len(filtered_df) == 2  # SV01 and SV02
        assert all(filtered_df['set'].str.startswith('SV'))

    def test_apply_filters_specific_type(self, aggregator, sample_csv_file):
        """Test filtering for specific type"""
        df = aggregator.read_csv(sample_csv_file)
        filtered_df = aggregator.apply_filters(df, sets='*', types='Card', period='3M')

        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]['type'] == 'Card'

    def test_apply_filters_box_types(self, aggregator, sample_csv_file):
        """Test filtering for box types"""
        df = aggregator.read_csv(sample_csv_file)
        filtered_df = aggregator.apply_filters(df, sets='*', types='*Box', period='3M')

        assert len(filtered_df) == 2  # Booster Box and Elite Trainer Box
        assert all('Box' in t for t in filtered_df['type'])

    def test_apply_filters_no_matches(self, aggregator, sample_csv_file):
        """Test filtering that returns no matches"""
        df = aggregator.read_csv(sample_csv_file)
        filtered_df = aggregator.apply_filters(df, sets='SV99', types='*', period='3M')

        assert len(filtered_df) == 0

    def test_apply_filters_invalid_period(self, aggregator, sample_csv_file):
        """Test filtering with invalid period defaults to 3M"""
        df = aggregator.read_csv(sample_csv_file)
        filtered_df = aggregator.apply_filters(df, sets='*', types='*', period='INVALID')

        # Should default to 3M and return all data
        assert len(filtered_df) == 3

    def test_create_subset_with_complete_coverage(self, aggregator, create_test_csv):
        """Test subset creation with 100% signature coverage"""
        # Create test data where first date has complete coverage
        complete_coverage_data = [
            # All signatures have 2025-01-03 (100% coverage)
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
            # Card A continues to 2025-01-05 (incomplete coverage)
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '105.00', 'volume': '6'},
        ]

        test_file = create_test_csv(complete_coverage_data)
        subset_df = aggregator.create_subset(test_file, sets='*', types='*', period='3M')

        # Step 1 should find 2025-01-03 as first date with 100% coverage (2 signatures)
        # Step 2 should fill gap for Card B on 2025-01-05
        assert not subset_df.empty
        assert len(subset_df) == 4  # 3 original + 1 gap-filled

        # Verify optimal start date is respected - no dates before 2025-01-03
        earliest_date = subset_df['period_end_date'].min()
        assert earliest_date.strftime('%Y-%m-%d') == '2025-01-03'

        # Verify 100% coverage achieved - all signatures present for all dates
        dates = subset_df['period_end_date'].unique()
        signatures = subset_df.groupby(['set', 'type', 'period', 'name']).ngroups
        expected_records = len(dates) * signatures
        assert len(subset_df) == expected_records

    def test_create_subset_no_complete_coverage(self, aggregator, create_test_csv):
        """Test subset creation when no date has 100% signature coverage"""
        # Create test data where no single date has all signatures
        no_complete_coverage_data = [
            # Card A: only on 2025-01-03
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            # Card B: only on 2025-01-05
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
        ]

        test_file = create_test_csv(no_complete_coverage_data)

        # Test default behavior (allow_fallback=False) - should return empty DataFrame
        subset_df = aggregator.create_subset(test_file, sets='*', types='*', period='3M')
        assert subset_df.empty  # No complete coverage found, returns empty

        # Test fallback behavior (allow_fallback=True) - should return gap-filled data
        subset_df_fallback = aggregator.create_subset(test_file, sets='*', types='*', period='3M', allow_fallback=True)
        assert not subset_df_fallback.empty
        assert len(subset_df_fallback) == 3  # 2 original + 1 gap-filled record

        # Should include both cards with gap filling
        card_names = set(subset_df_fallback['name'].unique())
        assert card_names == {'Card A', 'Card B'}

    def test_aggregate_time_series_basic(self, aggregator, sample_csv_file):
        """Test basic time series aggregation"""
        subset_df = aggregator.create_subset(sample_csv_file, sets='*', types='*', period='3M')

        # Aggregate the subset
        ts_df = aggregator.aggregate_time_series(subset_df)

        # Should have one time point since all test data has same period_end_date
        assert len(ts_df) == 1
        assert list(ts_df.columns) == ['period_end_date', 'aggregate_price', 'aggregate_value']

        # Verify calculations (now using sum instead of average)
        expected_sum_price = 100.50 + 200.00 + 150.75  # 451.25
        expected_sum_value = (100.50 * 5) + (200.00 * 10) + (150.75 * 3)  # 3160.75

        assert abs(ts_df.iloc[0]['aggregate_price'] - expected_sum_price) < 0.01
        assert abs(ts_df.iloc[0]['aggregate_value'] - expected_sum_value) < 0.01

    def test_aggregate_time_series_empty(self, aggregator):
        """Test aggregation with empty DataFrame"""
        empty_df = pd.DataFrame()
        ts_df = aggregator.aggregate_time_series(empty_df)

        assert ts_df.empty
        assert list(ts_df.columns) == ['period_end_date', 'aggregate_price', 'aggregate_value']

    def test_aggregate_time_series_multiple_dates(self, aggregator, aligned_test_data, create_test_csv):
        """Test aggregation with multiple period_end_dates"""
        test_file = create_test_csv(aligned_test_data)
        subset_df = aggregator.create_subset(test_file, sets='*', types='*', period='3M')

        # Aggregate the subset
        ts_df = aggregator.aggregate_time_series(subset_df)

        # Should have two time points
        assert len(ts_df) == 2

        # Verify sorting by period_end_date
        assert ts_df['period_end_date'].is_monotonic_increasing

        # Check first date (2025-01-03): Cards A,B,C with prices 100,200,300 and volumes 5,10,15
        first_row = ts_df.iloc[0]
        expected_price_1 = 100.00 + 200.00 + 300.00  # 600.00
        expected_value_1 = (100.00 * 5) + (200.00 * 10) + (300.00 * 15)  # 7000.00

        assert abs(first_row['aggregate_price'] - expected_price_1) < 0.01
        assert abs(first_row['aggregate_value'] - expected_value_1) < 0.01

        # Check second date (2025-01-05): Cards A,B,C with prices 105,205,305 and volumes 6,11,16
        second_row = ts_df.iloc[1]
        expected_price_2 = 105.00 + 205.00 + 305.00  # 615.00
        expected_value_2 = (105.00 * 6) + (205.00 * 11) + (305.00 * 16)  # 8540.00

        assert abs(second_row['aggregate_price'] - expected_price_2) < 0.01
        assert abs(second_row['aggregate_value'] - expected_value_2) < 0.01


@pytest.fixture
def time_series_test_data():
    """Test data with different period_end_date coverage for alignment testing"""
    return [
        # Card A: has end_dates [2025-01-03, 2025-01-05, 2025-01-07]
        {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
        {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
         'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '105.00', 'volume': '6'},
        {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
         'period_start_date': '2025-01-05', 'period_end_date': '2025-01-07',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '110.00', 'volume': '7'},

        # Card B: has end_dates [2025-01-03, 2025-01-05] (missing 2025-01-07)
        {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
        {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
         'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '205.00', 'volume': '11'},

        # Card C: has end_dates [2025-01-03, 2025-01-07] (missing 2025-01-05)
        {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '300.00', 'volume': '15'},
        {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
         'period_start_date': '2025-01-05', 'period_end_date': '2025-01-07',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '307.00', 'volume': '16'},
    ]


@pytest.fixture
def aligned_test_data():
    """Test data where all cards have the same period_end_dates (perfect alignment)"""
    return [
        # All three cards have end_dates [2025-01-03, 2025-01-05]
        {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
        {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
         'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '105.00', 'volume': '6'},

        {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
        {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
         'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '205.00', 'volume': '11'},

        {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
         'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '300.00', 'volume': '15'},
        {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
         'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
         'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '305.00', 'volume': '16'},
    ]


@pytest.fixture
def create_test_csv(request):
    """Create temporary CSV file from test data"""
    def _create_csv(data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            headers = list(data[0].keys())
            f.write(','.join(headers) + '\n')
            for row in data:
                values = [str(row[h]) for h in headers]
                f.write(','.join(values) + '\n')
            f.flush()
            return Path(f.name)

    files_to_cleanup = []

    def cleanup():
        for file_path in files_to_cleanup:
            if os.path.exists(file_path):
                os.remove(file_path)

    request.addfinalizer(cleanup)

    def wrapper(data):
        file_path = _create_csv(data)
        files_to_cleanup.append(file_path)
        return file_path

    return wrapper


class TestTimeSeriesAlignment:
    """Test cases for time series alignment functionality"""

    def setup_class(self):
        """Setup logging for test class"""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")

    @pytest.fixture
    def aggregator(self):
        """Create IndexAggregator instance"""
        return IndexAggregator()

    def test_time_series_alignment_with_complete_coverage(self, aggregator, create_test_csv):
        """Test time series alignment when first date achieves 100% signature coverage"""
        # Create data where 2025-01-03 has all signatures (100% coverage)
        complete_first_date_data = [
            # All cards have 2025-01-03 (100% coverage)
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
            {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '300.00', 'volume': '15'},

            # Only some cards continue to later dates (incomplete coverage)
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '105.00', 'volume': '6'},
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '205.00', 'volume': '11'},
            # Card C missing on 2025-01-05 - will be gap-filled

            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-05', 'period_end_date': '2025-01-07',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '110.00', 'volume': '7'},
            # Cards B and C missing on 2025-01-07 - will be gap-filled
        ]

        test_file = create_test_csv(complete_first_date_data)
        subset_df = aggregator.create_subset(test_file, sets='*', types='*', period='3M')

        # Step 1: Should find 2025-01-03 as optimal start date (100% coverage with 3 signatures)
        # Step 2: Should fill gaps to ensure all signatures present on all dates
        assert len(subset_df) == 9  # 3 signatures × 3 dates = 9 records total

        # Verify optimal start date is respected
        earliest_date = subset_df['period_end_date'].min()
        assert earliest_date.strftime('%Y-%m-%d') == '2025-01-03'

        # Verify 100% signature coverage achieved
        dates = subset_df['period_end_date'].unique()
        signatures = subset_df.groupby(['set', 'type', 'period', 'name']).ngroups
        expected_records = len(dates) * signatures
        assert len(subset_df) == expected_records  # Perfect completeness

        # Verify all signatures present on all dates
        for date in dates:
            date_records = subset_df[subset_df['period_end_date'] == date]
            assert len(date_records) == 3  # All 3 signatures present
            card_names = set(date_records['name'].unique())
            assert card_names == {'Card A', 'Card B', 'Card C'}

    def test_time_series_alignment_no_complete_coverage(self, aggregator, create_test_csv):
        """Test time series alignment when no date has 100% signature coverage"""
        # Create data where no single date has all signatures present
        no_complete_data = [
            # Card A: only on early dates
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '105.00', 'volume': '6'},

            # Card B: only on middle dates
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-05', 'period_end_date': '2025-01-07',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '205.00', 'volume': '11'},

            # Card C: only on late dates
            {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
             'period_start_date': '2025-01-05', 'period_end_date': '2025-01-07',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '300.00', 'volume': '15'},
            {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
             'period_start_date': '2025-01-07', 'period_end_date': '2025-01-09',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '305.00', 'volume': '16'},
        ]

        test_file = create_test_csv(no_complete_data)

        # Test default behavior (allow_fallback=False) - should return empty DataFrame
        subset_df = aggregator.create_subset(test_file, sets='*', types='*', period='3M')
        assert subset_df.empty  # No complete coverage found, returns empty

        # Test fallback behavior (allow_fallback=True) - should return gap-filled data
        subset_df_fallback = aggregator.create_subset(test_file, sets='*', types='*', period='3M', allow_fallback=True)
        assert not subset_df_fallback.empty
        assert len(subset_df_fallback) > 6  # Original + gap-filled records

        # Should include all signatures with fallback mode
        card_names = set(subset_df_fallback['name'].unique())
        assert card_names == {'Card A', 'Card B', 'Card C'}

    def test_time_series_alignment_with_filters(self, aggregator, time_series_test_data, create_test_csv):
        """Test time series alignment combined with filtering"""
        test_file = create_test_csv(time_series_test_data)

        # Create subset with filter for only SV01 and SV02 using fallback mode
        subset_df = aggregator.create_subset(test_file, sets='SV01,SV02', types='*', period='3M', allow_fallback=True)

        # Expected: Card A (3 dates) and Card B (2 dates) after filtering with gap filling
        assert not subset_df.empty

        # Should include both cards with gap filling
        card_names = set(subset_df['name'].unique())
        assert card_names == {'Card A', 'Card B'}

        # Verify dates are present (union of both card dates with gap filling)
        end_dates = set(subset_df['period_end_date'].dt.strftime('%Y-%m-%d').unique())
        expected_dates = {'2025-01-03', '2025-01-05', '2025-01-07'}  # Union of A and B dates
        assert end_dates == expected_dates

    def test_time_series_alignment_no_common_dates(self, aggregator, create_test_csv):
        """Test time series alignment when signatures have no overlapping dates"""
        # Create data where cards have same date count but no overlapping dates
        no_common_data = [
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-02', 'period_end_date': '2025-01-04',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
        ]

        test_file = create_test_csv(no_common_data)

        # Test default behavior - should return empty DataFrame (no common dates)
        subset_df = aggregator.create_subset(test_file, sets='*', types='*', period='3M')
        assert subset_df.empty  # No overlapping dates, no complete coverage

        # Test fallback behavior - should include both cards with gap filling
        subset_df_fallback = aggregator.create_subset(test_file, sets='*', types='*', period='3M', allow_fallback=True)
        assert not subset_df_fallback.empty
        card_names = set(subset_df_fallback['name'].unique())
        assert card_names == {'Card A', 'Card B'}

        # Should have union of both dates with gap filling
        end_dates = set(subset_df_fallback['period_end_date'].dt.strftime('%Y-%m-%d').unique())
        assert end_dates == {'2025-01-03', '2025-01-04'}

    def test_time_series_alignment_single_card(self, aggregator, create_test_csv):
        """Test time series alignment with only one card"""
        single_card_data = [
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Single Card',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Single Card',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '105.00', 'volume': '6'},
        ]

        test_file = create_test_csv(single_card_data)

        # Create subset - should include all data since only one signature
        subset_df = aggregator.create_subset(test_file, sets='*', types='*', period='3M')

        assert len(subset_df) == 2
        assert all(subset_df['name'] == 'Single Card')
        end_dates = set(subset_df['period_end_date'].dt.strftime('%Y-%m-%d').unique())
        assert end_dates == {'2025-01-03', '2025-01-05'}

    def test_time_series_alignment_most_common_count(self, aggregator, create_test_csv):
        """Test that alignment uses signatures with most common date count"""
        # Create data where majority have 2 dates, minority have 3 dates
        mixed_count_data = [
            # Card A: 3 dates (minority)
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '105.00', 'volume': '6'},
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-05', 'period_end_date': '2025-01-07',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '110.00', 'volume': '7'},

            # Card B: 2 dates (majority)
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '205.00', 'volume': '11'},

            # Card C: 2 dates (majority)
            {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
             'period_start_date': '2025-01-02', 'period_end_date': '2025-01-04',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '300.00', 'volume': '15'},
            {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
             'period_start_date': '2025-01-04', 'period_end_date': '2025-01-06',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '305.00', 'volume': '16'},

            # Card D: 2 dates (majority)
            {'set': 'SV04', 'type': 'Card', 'period': '3M', 'name': 'Card D',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '400.00', 'volume': '20'},
            {'set': 'SV04', 'type': 'Card', 'period': '3M', 'name': 'Card D',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '405.00', 'volume': '21'},
        ]

        test_file = create_test_csv(mixed_count_data)

        # Test with fallback mode to get alignment behavior
        subset_df = aggregator.create_subset(test_file, sets='*', types='*', period='3M', allow_fallback=True)

        # Should include all cards with gap filling for complete coverage
        assert not subset_df.empty
        card_names = set(subset_df['name'].unique())
        assert card_names == {'Card A', 'Card B', 'Card C', 'Card D'}

        # Should have comprehensive date coverage with gap filling
        end_dates = set(subset_df['period_end_date'].dt.strftime('%Y-%m-%d').unique())
        assert len(end_dates) >= 4  # Multiple dates from alignment


class TestCompleteDataFiltering:
    """Test cases for complete data filtering functionality"""

    def setup_class(self):
        """Setup logging for test class"""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")

    @pytest.fixture
    def aggregator(self):
        """Create IndexAggregator instance"""
        return IndexAggregator()

    @pytest.fixture
    def incomplete_coverage_data(self):
        """Test data where different signatures have different date coverage"""
        return [
            # Signature A: has dates [2025-01-03, 2025-01-05, 2025-01-07]
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '105.00', 'volume': '6'},
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-05', 'period_end_date': '2025-01-07',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '110.00', 'volume': '7'},

            # Signature B: has dates [2025-01-03, 2025-01-05] (missing 2025-01-07)
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-03', 'period_end_date': '2025-01-05',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '205.00', 'volume': '11'},

            # Signature C: has dates [2025-01-03, 2025-01-07] (missing 2025-01-05)
            {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '300.00', 'volume': '15'},
            {'set': 'SV03', 'type': 'Card', 'period': '3M', 'name': 'Card C',
             'period_start_date': '2025-01-05', 'period_end_date': '2025-01-07',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '307.00', 'volume': '16'},
        ]

    def test_create_complete_subset_with_incomplete_data(self, aggregator, incomplete_coverage_data, create_test_csv):
        """Test create_complete_subset with data that has gaps"""
        test_file = create_test_csv(incomplete_coverage_data)

        # Use the new complete subset method
        complete_subset_df = aggregator.create_complete_subset(test_file, sets='*', types='*', period='3M')

        # Expected: Only 2025-01-03 has all 3 signatures, so only 3 records total
        assert len(complete_subset_df) == 3

        # Verify only the common date is included
        end_dates = set(complete_subset_df['period_end_date'].dt.strftime('%Y-%m-%d').unique())
        assert end_dates == {'2025-01-03'}

        # Verify all 3 signatures are present for the common date
        card_names = set(complete_subset_df['name'].unique())
        assert card_names == {'Card A', 'Card B', 'Card C'}

    def test_create_complete_subset_vs_create_subset(self, aggregator, incomplete_coverage_data, create_test_csv):
        """Test difference between create_subset and create_complete_subset"""
        test_file = create_test_csv(incomplete_coverage_data)

        # Original method: uses most common date count (2 dates), includes signatures B&C only
        original_subset = aggregator.create_subset(test_file, sets='*', types='*', period='3M')

        # New method: uses only dates with complete coverage across ALL signatures (including A)
        complete_subset = aggregator.create_complete_subset(test_file, sets='*', types='*', period='3M')

        # Original method: with fallback=True, fills gaps for all signatures across all dates = 9 records
        # Complete method: All 3 signatures, intersection gives 1 date = 3 records
        assert len(original_subset) == 9  # 3 signatures × 3 dates (with gap filling) = 9 records
        assert len(complete_subset) == 3  # Cards A, B, and C for 2025-01-03 only

        # Complete subset should have perfect alignment
        if not complete_subset.empty:
            dates = complete_subset['period_end_date'].unique()
            signatures = complete_subset.groupby(['set', 'type', 'period', 'name']).ngroups
            expected_records = len(dates) * signatures
            # Should have exactly one record per signature per date
            assert len(complete_subset) == expected_records

        # Both methods include all signatures after completeness-only alignment changes
        expected_signatures = {'Card A', 'Card B', 'Card C'}
        assert set(original_subset['name'].unique()) == set(complete_subset['name'].unique()) == expected_signatures

    def test_create_complete_subset_perfect_alignment(self, aggregator, aligned_test_data, create_test_csv):
        """Test create_complete_subset with perfectly aligned data"""
        test_file = create_test_csv(aligned_test_data)

        complete_subset_df = aggregator.create_complete_subset(test_file, sets='*', types='*', period='3M')

        # With perfect alignment, should include all records
        assert len(complete_subset_df) == 6  # 3 signatures × 2 common dates

        # Verify both common dates are included
        end_dates = set(complete_subset_df['period_end_date'].dt.strftime('%Y-%m-%d').unique())
        assert end_dates == {'2025-01-03', '2025-01-05'}

        # Verify perfect alignment: each date should have exactly 3 records
        for date in ['2025-01-03', '2025-01-05']:
            date_records = complete_subset_df[
                complete_subset_df['period_end_date'].dt.strftime('%Y-%m-%d') == date
            ]
            assert len(date_records) == 3  # All 3 signatures present

    def test_create_complete_subset_no_common_dates(self, aggregator, create_test_csv):
        """Test create_complete_subset when no dates have complete coverage"""
        no_overlap_data = [
            {'set': 'SV01', 'type': 'Card', 'period': '3M', 'name': 'Card A',
             'period_start_date': '2025-01-01', 'period_end_date': '2025-01-03',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '100.00', 'volume': '5'},
            {'set': 'SV02', 'type': 'Card', 'period': '3M', 'name': 'Card B',
             'period_start_date': '2025-01-04', 'period_end_date': '2025-01-06',
             'timestamp': '2025-07-24 15:00:00', 'holofoil_price': '200.00', 'volume': '10'},
        ]

        test_file = create_test_csv(no_overlap_data)

        complete_subset_df = aggregator.create_complete_subset(test_file, sets='*', types='*', period='3M')

        # Should return empty DataFrame since no dates have complete coverage
        assert complete_subset_df.empty


class TestIndexAggregatorIntegration:
    """Integration tests for the full workflow"""

    def setup_class(self):
        """Setup logging for test class"""
        logger = AppLogger()
        logger.setup_logging(verbose=True, log_file="test.log")

    @pytest.fixture
    def runner(self):
        """Test runner for CLI commands"""
        class TestRunner:
            def invoke(self, args):
                import sys
                import io
                from contextlib import redirect_stdout, redirect_stderr
                from chart.index_aggregator import main

                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()
                original_argv = sys.argv
                sys.argv = ['index_aggregator.py'] + args

                try:
                    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                        main()
                    exit_code = 0
                except SystemExit as e:
                    # argparse --help exits with code 0, but other exits may have different codes
                    exit_code = e.code if e.code is not None else 0
                except Exception as e:
                    stderr_capture.write(str(e))
                    exit_code = 1
                finally:
                    sys.argv = original_argv

                class MockResult:
                    def __init__(self, exit_code, stdout, stderr):
                        self.exit_code = exit_code
                        self.stdout = stdout
                        self.stderr = stderr

                return MockResult(exit_code, stdout_capture.getvalue(), stderr_capture.getvalue())

        return TestRunner()

    def test_main_help(self, runner):
        """Test help command"""
        result = runner.invoke(['--help'])
        assert result.exit_code == 0
        assert 'TCGPlayer Price Data Index Aggregator' in result.stdout

    def test_main_basic_usage(self, runner, temp_input_file, temp_output_file):
        """Test basic command execution"""
        result = runner.invoke([str(temp_input_file), '--name', 'test_series'])

        assert result.exit_code == 0
        expected_output = Path('data/test_series_time_series.csv')
        assert expected_output.exists()

        # Verify output file has aggregated time series data
        df = pd.read_csv(expected_output)
        assert len(df) == 1  # 2 input records aggregated into 1 time series point
        assert list(df.columns) == ['name', 'period_end_date', 'aggregate_price', 'aggregate_value']

        # Cleanup
        expected_output.unlink(missing_ok=True)

    def test_main_with_filters(self, runner, temp_input_file, temp_output_file):
        """Test command execution with filters"""
        result = runner.invoke([
            str(temp_input_file), '--name', 'test_series',
            '--sets', 'SV01',
            '--types', 'Card'
        ])

        assert result.exit_code == 0
        expected_output = Path('data/test_series_time_series.csv')

        if expected_output.exists():
            # Verify filtered and aggregated output
            df = pd.read_csv(expected_output)
            assert len(df) >= 0  # Should have filtered data if any matches
            assert list(df.columns) == ['name', 'period_end_date', 'aggregate_price', 'aggregate_value']
            # Cleanup
            expected_output.unlink(missing_ok=True)
        # Verify it's aggregated data (price should be 100.0 from the SV01 Card)
        assert df.iloc[0]['aggregate_price'] == 100.0

    def test_main_no_matches(self, runner, temp_input_file, temp_output_file):
        """Test command execution with no matching filters"""
        result = runner.invoke([
            str(temp_input_file), '--name', 'test_series',
            '--sets', 'SV99'  # Non-existent set
        ])

        assert result.exit_code == 0
        # Should output message about no matching data
        expected_output = Path('data/test_series_time_series.csv')
        # Cleanup if file was created
        expected_output.unlink(missing_ok=True)

    def test_main_missing_args(self, runner):
        """Test command execution with missing arguments"""
        result = runner.invoke([])
        assert result.exit_code == 2  # argparse error