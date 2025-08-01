#!/usr/bin/env python3
"""
Unit tests for Coverage Analyzer functionality

Tests the CoverageAnalyzer class and related data structures for the
Interactive Alignment Workbench.
"""

import pytest
import sys
from pathlib import Path
from dataclasses import asdict
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.coverage_analyzer import CoverageResult, RecommendationResult, CoverageAnalyzer
from common.logger import AppLogger
from chart.index_aggregator import IndexAggregator, FilterValidator
from common.time_series_aligner import TimeSeriesAligner


class TestCoverageResult:
    """Test cases for CoverageResult dataclass"""

    def setup_class(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_coverage_result_creation_with_successful_analysis(self, successful_coverage_result, sv_card_filter_config):
        """Test CoverageResult creation with successful analysis data"""
        # Act: Use fixture for successful analysis result
        result = successful_coverage_result

        # Assert: Verify all fields are accessible and have correct values
        assert result.filter_config == sv_card_filter_config
        assert result.coverage_percentage == 1.0
        assert result.signatures_found == 13
        assert result.signatures_total == 13
        assert result.optimal_start_date == "2025-04-28"
        assert result.records_before_start == 57
        assert result.records_aligned == 1209
        assert result.time_series_points == 93
        assert result.gap_fills_required == 50
        assert result.missing_signatures == []
        assert result.fallback_required is False
        assert result.quality_score == 1.0

    def test_coverage_result_creation_with_failed_analysis(self, failed_coverage_result, mixed_generation_filter_config, failed_coverage_result_data):
        """Test CoverageResult creation with failed analysis data (0% coverage)"""
        # Act: Use fixture for failed analysis result
        result = failed_coverage_result
        missing_sigs = failed_coverage_result_data["missing_signatures"]

        # Assert: Verify failed analysis fields are correct
        assert result.filter_config == mixed_generation_filter_config
        assert result.coverage_percentage == 0.0
        assert result.signatures_found == 0
        assert result.signatures_total == 20
        assert result.optimal_start_date is None
        assert result.records_before_start == 0
        assert result.records_aligned == 0
        assert result.time_series_points == 0
        assert result.gap_fills_required == 0
        assert result.missing_signatures == missing_sigs
        assert result.fallback_required is False
        assert result.quality_score == 0.0

    def test_coverage_result_creation_with_partial_coverage(self, partial_coverage_result):
        """Test CoverageResult creation with partial coverage requiring fallback"""
        # Act: Use fixture for partial coverage result
        result = partial_coverage_result

        # Assert: Verify partial coverage fields are correct
        assert result.coverage_percentage == 0.95
        assert result.signatures_found == 19
        assert result.signatures_total == 20
        assert result.fallback_required is True
        assert len(result.missing_signatures) == 1
        assert result.quality_score == 0.85

    def test_coverage_result_field_types(self, standard_coverage_result):
        """Test that CoverageResult fields have correct types"""
        # Act: Use fixture for standard result
        result = standard_coverage_result

        # Assert: Verify field types
        assert isinstance(result.filter_config, dict)
        assert isinstance(result.coverage_percentage, float)
        assert isinstance(result.signatures_found, int)
        assert isinstance(result.signatures_total, int)
        assert isinstance(result.optimal_start_date, str)
        assert isinstance(result.records_before_start, int)
        assert isinstance(result.records_aligned, int)
        assert isinstance(result.time_series_points, int)
        assert isinstance(result.gap_fills_required, int)
        assert isinstance(result.missing_signatures, list)
        assert isinstance(result.fallback_required, bool)
        assert isinstance(result.quality_score, float)

    def test_coverage_result_asdict_conversion(self, successful_coverage_result, sv_card_filter_config):
        """Test CoverageResult conversion to dictionary for JSON serialization"""
        # Act: Convert fixture result to dictionary
        result_dict = asdict(successful_coverage_result)

        # Assert: Verify dictionary structure and content
        assert isinstance(result_dict, dict)
        assert len(result_dict) == 12  # All 12 fields present
        assert result_dict["filter_config"] == sv_card_filter_config
        assert result_dict["coverage_percentage"] == 1.0
        assert result_dict["signatures_found"] == 13
        assert result_dict["optimal_start_date"] == "2025-04-28"
        assert result_dict["missing_signatures"] == []
        assert result_dict["fallback_required"] is False

    def test_coverage_result_with_none_optional_fields(self, invalid_filter_config):
        """Test CoverageResult creation with None values for optional fields"""
        # Arrange & Act: Create result with None optimal_start_date
        result = CoverageResult(
            filter_config=invalid_filter_config,
            coverage_percentage=0.0,
            signatures_found=0,
            signatures_total=0,
            optimal_start_date=None,  # This should be allowed
            records_before_start=0,
            records_aligned=0,
            time_series_points=0,
            gap_fills_required=0,
            missing_signatures=[],
            fallback_required=False,
            quality_score=0.0
        )

        # Assert: Verify None value is handled correctly
        assert result.optimal_start_date is None
        assert result.coverage_percentage == 0.0

        # Verify conversion to dict still works with None values
        result_dict = asdict(result)
        assert result_dict["optimal_start_date"] is None


class TestRecommendationResult:
    """Test cases for RecommendationResult dataclass"""

    def setup_class(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_recommendation_result_creation_with_complete_data(self, successful_recommendation_result, sv_card_filter_config, successful_coverage_result):
        """Test RecommendationResult creation with complete recommendation data"""
        # Act: Use fixture for successful recommendation
        recommendation = successful_recommendation_result

        # Assert: Verify all fields are accessible and have correct values
        assert recommendation.rank == 1
        assert recommendation.filter_config == sv_card_filter_config
        assert recommendation.coverage_result == successful_coverage_result
        assert recommendation.description == "SV Cards (Complete)"
        assert recommendation.command_string == '--sets "SV*" --types "Card" --period "3M"'
        assert recommendation.estimated_records == 1209

    def test_recommendation_result_creation_with_fallback_scenario(self, fallback_recommendation_result):
        """Test RecommendationResult creation with fallback mode requirement"""
        # Act: Use fixture for fallback recommendation
        recommendation = fallback_recommendation_result

        # Assert: Verify fallback scenario fields are correct
        assert recommendation.rank == 2
        assert recommendation.coverage_result.fallback_required is True
        assert recommendation.coverage_result.coverage_percentage == 0.95
        assert recommendation.description == "SWSH/SV Cards (Excellent)"
        assert "--allow-fallback" in recommendation.command_string
        assert recommendation.estimated_records == 1859

    def test_recommendation_result_field_types(self, sv_card_filter_config, standard_coverage_result):
        """Test that RecommendationResult fields have correct types"""
        # Act: Create RecommendationResult using fixtures
        recommendation = RecommendationResult(
            rank=3,
            filter_config=sv_card_filter_config,
            coverage_result=standard_coverage_result,
            description="SV Cards (High Quality)",
            command_string='--sets "SV*" --types "Card" --period "3M"',
            estimated_records=1000
        )

        # Assert: Verify field types
        assert isinstance(recommendation.rank, int)
        assert isinstance(recommendation.filter_config, dict)
        assert isinstance(recommendation.coverage_result, CoverageResult)
        assert isinstance(recommendation.description, str)
        assert isinstance(recommendation.command_string, str)
        assert isinstance(recommendation.estimated_records, int)

    def test_recommendation_result_asdict_conversion(self, successful_recommendation_result, sv_card_filter_config):
        """Test RecommendationResult conversion to dictionary for JSON serialization"""
        # Act: Convert fixture recommendation to dictionary
        recommendation_dict = asdict(successful_recommendation_result)

        # Assert: Verify dictionary structure and nested CoverageResult
        assert isinstance(recommendation_dict, dict)
        assert len(recommendation_dict) == 6  # All 6 fields present
        assert recommendation_dict["rank"] == 1
        assert recommendation_dict["filter_config"] == sv_card_filter_config
        assert recommendation_dict["description"] == "SV Cards (Complete)"
        assert recommendation_dict["command_string"] == '--sets "SV*" --types "Card" --period "3M"'
        assert recommendation_dict["estimated_records"] == 1209

        # Verify nested CoverageResult is properly serialized
        assert isinstance(recommendation_dict["coverage_result"], dict)
        assert recommendation_dict["coverage_result"]["coverage_percentage"] == 1.0
        assert recommendation_dict["coverage_result"]["signatures_found"] == 13

    def test_recommendation_result_with_alternative_suggestion(self, sv_card_filter_config, alternative_suggestion_result_data):
        """Test RecommendationResult creation for alternative suggestions from failed filters"""
        # Arrange: Create CoverageResult for alternative suggestion using fixture data
        coverage_result = CoverageResult(
            filter_config=sv_card_filter_config,
            **alternative_suggestion_result_data
        )

        # Act: Create RecommendationResult as alternative suggestion
        recommendation = RecommendationResult(
            rank=1,
            filter_config=sv_card_filter_config,
            coverage_result=coverage_result,
            description="Focus on SV Generation",
            command_string='--sets "SV*" --types "Card" --period "3M"',
            estimated_records=1156
        )

        # Assert: Verify alternative suggestion fields
        assert recommendation.description == "Focus on SV Generation"
        assert recommendation.coverage_result.coverage_percentage == 0.92  # Good but not perfect
        assert len(recommendation.coverage_result.missing_signatures) == 1
        assert recommendation.coverage_result.missing_signatures[0] == "SV10_MissingCard_Card"
        assert recommendation.estimated_records == 1156


class TestCoverageAnalyzer:
    """Test cases for CoverageAnalyzer class"""

    def setup_class(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_coverage_analyzer_initialization_with_dependency_injection(self, coverage_analyzer_dependencies):
        """Test CoverageAnalyzer initialization with proper dependency injection"""
        # Act: Initialize CoverageAnalyzer with dependency injection using fixtures
        analyzer = CoverageAnalyzer(**coverage_analyzer_dependencies)

        # Assert: Verify all dependencies are properly stored
        assert analyzer.aggregator is coverage_analyzer_dependencies["aggregator"]
        assert analyzer.aligner is coverage_analyzer_dependencies["aligner"]
        assert analyzer.validator is coverage_analyzer_dependencies["validator"]
        assert analyzer.logger is not None
        assert analyzer._dataset_cache is None
        assert analyzer._signature_cache is None

    def test_coverage_analyzer_initialization_with_default_csv_path(self):
        """Test CoverageAnalyzer initialization with default CSV path"""
        # Arrange: Use default constructor
        # Act: Initialize CoverageAnalyzer with default parameters
        analyzer = CoverageAnalyzer()

        # Assert: Verify default initialization
        assert analyzer.input_csv == Path("data/output.csv")
        assert isinstance(analyzer.aggregator, IndexAggregator)
        assert isinstance(analyzer.aligner, TimeSeriesAligner)
        assert analyzer.logger is not None
        assert analyzer._dataset_cache is None
        assert analyzer._signature_cache is None

    def test_coverage_analyzer_initialization_with_custom_csv_path(self):
        """Test CoverageAnalyzer initialization with custom CSV path"""
        # Arrange: Set custom CSV path
        custom_path = Path("test/custom_data.csv")

        # Act: Initialize CoverageAnalyzer with custom path
        analyzer = CoverageAnalyzer(input_csv=custom_path)

        # Assert: Verify custom path is set
        assert analyzer.input_csv == custom_path
        assert isinstance(analyzer.aggregator, IndexAggregator)
        assert isinstance(analyzer.aligner, TimeSeriesAligner)
        assert analyzer.logger is not None

    def test_analyze_filter_combination_with_valid_sv_card_filters(self, sv_card_filter_config):
        """Test analyze_filter_combination with valid SV* Card filters"""
        # Arrange: Initialize analyzer
        analyzer = CoverageAnalyzer()

        # Act: Analyze valid SV* Card filter combination using fixture
        result = analyzer.analyze_filter_combination(
            sets=sv_card_filter_config["sets"],
            types=sv_card_filter_config["types"],
            period=sv_card_filter_config["period"]
        )

        # Assert: Verify successful analysis results
        assert isinstance(result, CoverageResult)
        assert result.filter_config == sv_card_filter_config
        assert result.coverage_percentage >= 0.0
        assert result.coverage_percentage <= 1.0
        assert result.signatures_found >= 0
        assert result.signatures_total >= result.signatures_found
        assert isinstance(result.optimal_start_date, (str, type(None)))
        assert result.records_before_start >= 0
        assert result.records_aligned >= 0
        assert result.time_series_points >= 0
        assert result.gap_fills_required >= 0
        assert isinstance(result.missing_signatures, list)
        assert isinstance(result.fallback_required, bool)
        assert result.quality_score >= 0.0
        assert result.quality_score <= 1.0

    def test_analyze_filter_combination_with_invalid_filter_patterns(self):
        """Test analyze_filter_combination with invalid filter patterns that match no data"""
        # Arrange: Initialize analyzer and prepare invalid filter parameters
        analyzer = CoverageAnalyzer()
        invalid_filter_config = {"sets": "INVALID*", "types": "NonExistentType", "period": "3M"}

        # Act: Analyze invalid filter combination that should match no data
        result = analyzer.analyze_filter_combination(
            sets=invalid_filter_config["sets"],
            types=invalid_filter_config["types"],
            period=invalid_filter_config["period"]
        )

        # Assert: Verify failure scenario results
        assert isinstance(result, CoverageResult)
        assert result.filter_config == invalid_filter_config
        assert result.coverage_percentage == 0.0
        assert result.signatures_found == 0
        assert result.signatures_total == 0
        assert result.optimal_start_date is None
        assert result.records_before_start == 0
        assert result.records_aligned == 0
        assert result.time_series_points == 0
        assert result.gap_fills_required == 0
        assert len(result.missing_signatures) == 0  # No signatures found to begin with
        assert result.fallback_required == False
        assert result.quality_score == 0.0

    def test_analyze_filter_combination_with_empty_dataset(self, sv_card_filter_config):
        """Test analyze_filter_combination with empty or non-existent dataset"""
        # Arrange: Initialize analyzer with non-existent CSV file
        nonexistent_csv = Path("test_data/nonexistent.csv")
        analyzer = CoverageAnalyzer(input_csv=nonexistent_csv)

        # Act: Analyze filter combination with empty dataset using fixture
        result = analyzer.analyze_filter_combination(
            sets=sv_card_filter_config["sets"],
            types=sv_card_filter_config["types"],
            period=sv_card_filter_config["period"]
        )

        # Assert: Verify empty dataset scenario results
        assert isinstance(result, CoverageResult)
        assert result.filter_config == sv_card_filter_config
        assert result.coverage_percentage == 0.0
        assert result.signatures_found == 0
        assert result.signatures_total == 0
        assert result.optimal_start_date is None
        assert result.records_before_start == 0
        assert result.records_aligned == 0
        assert result.time_series_points == 0
        assert result.gap_fills_required == 0
        assert len(result.missing_signatures) == 0
        assert result.fallback_required == False
        assert result.quality_score == 0.0

    def test_discover_viable_configurations_with_various_coverage_thresholds(self):
        """Test discover_viable_configurations with different coverage thresholds"""
        # Arrange: Initialize analyzer
        analyzer = CoverageAnalyzer()

        # Act: Discover configurations with high coverage threshold (90%)
        high_threshold_recommendations = analyzer.discover_viable_configurations(
            min_coverage=0.9,
            max_recommendations=5,
            include_fallback_options=True
        )

        # Assert: Verify high threshold results
        assert isinstance(high_threshold_recommendations, list)
        assert len(high_threshold_recommendations) <= 5
        for rec in high_threshold_recommendations:
            assert isinstance(rec, RecommendationResult)
            assert rec.coverage_result.coverage_percentage >= 0.9
            assert rec.rank >= 1
            assert isinstance(rec.description, str)
            assert isinstance(rec.command_string, str)
            assert rec.estimated_records >= 0

        # Act: Discover configurations with lower coverage threshold (70%)
        low_threshold_recommendations = analyzer.discover_viable_configurations(
            min_coverage=0.7,
            max_recommendations=10,
            include_fallback_options=False
        )

        # Assert: Verify lower threshold returns more results
        assert isinstance(low_threshold_recommendations, list)
        assert len(low_threshold_recommendations) <= 10
        assert len(low_threshold_recommendations) >= len(high_threshold_recommendations)
        for rec in low_threshold_recommendations:
            assert isinstance(rec, RecommendationResult)
            assert rec.coverage_result.coverage_percentage >= 0.7
            assert rec.rank >= 1

        # Act: Test with very high threshold that should return fewer results
        strict_recommendations = analyzer.discover_viable_configurations(
            min_coverage=0.99,
            max_recommendations=3
        )

        # Assert: Verify strict threshold behavior
        assert isinstance(strict_recommendations, list)
        assert len(strict_recommendations) <= len(high_threshold_recommendations)
        for rec in strict_recommendations:
            assert rec.coverage_result.coverage_percentage >= 0.99

    def test_suggest_alternatives_for_failed_filter_combinations(self):
        """Test suggest_alternatives with failed filter combinations"""
        # Arrange: Initialize analyzer
        analyzer = CoverageAnalyzer()

        # Act: Get alternatives for completely invalid filter combination
        invalid_alternatives = analyzer.suggest_alternatives(
            failed_config={"sets": "INVALID*", "types": "NonExistent", "period": "3M"}
        )

        # Assert: Verify alternatives are provided for invalid filters
        assert isinstance(invalid_alternatives, list)
        assert len(invalid_alternatives) > 0
        for alt in invalid_alternatives:
            assert isinstance(alt, RecommendationResult)
            assert alt.coverage_result.coverage_percentage > 0.0
            assert alt.rank >= 1
            assert isinstance(alt.description, str)
            assert isinstance(alt.command_string, str)
            assert alt.estimated_records > 0

        # Act: Get alternatives for partially valid but problematic combination
        problematic_alternatives = analyzer.suggest_alternatives(
            failed_config={"sets": "SV01,SWSH12", "types": "Card", "period": "3M"}
        )

        # Assert: Verify alternatives for cross-generation mixing
        assert isinstance(problematic_alternatives, list)
        assert len(problematic_alternatives) > 0
        for alt in problematic_alternatives:
            assert isinstance(alt, RecommendationResult)
            assert alt.coverage_result.coverage_percentage >= 0.8  # Should suggest high-quality alternatives
            assert alt.rank >= 1

        # Act: Get alternatives for overly restrictive combination
        restrictive_alternatives = analyzer.suggest_alternatives(
            failed_config={"sets": "SV10", "types": "Elite Trainer Box", "period": "1M"}
        )

        # Assert: Verify alternatives for overly restrictive filters
        assert isinstance(restrictive_alternatives, list)
        # Should provide alternatives even if original was too restrictive
        for alt in restrictive_alternatives:
            assert isinstance(alt, RecommendationResult)
            assert alt.coverage_result.coverage_percentage > 0.0

    def test_get_dataset_summary_with_mock_data(self):
        """Test get_dataset_summary method with dataset statistics"""
        # Arrange: Initialize analyzer
        analyzer = CoverageAnalyzer()

        # Act: Get dataset summary
        summary = analyzer.get_dataset_summary()

        # Assert: Verify summary structure and content
        assert isinstance(summary, dict)
        assert "total_records" in summary
        assert "available_sets" in summary
        assert "available_types" in summary
        assert "unique_signatures" in summary
        assert "date_range" in summary
        assert "max_possible_coverage" in summary

        # Verify data types and reasonable values
        assert isinstance(summary["total_records"], int)
        assert summary["total_records"] >= 0
        assert isinstance(summary["available_sets"], list)
        assert isinstance(summary["available_types"], list)
        assert isinstance(summary["unique_signatures"], int)
        assert isinstance(summary["date_range"], tuple)
        assert isinstance(summary["max_possible_coverage"], int)

        # Verify content if data exists
        if summary["total_records"] > 0:
            assert len(summary["available_sets"]) > 0
            assert len(summary["available_types"]) > 0
            assert summary["unique_signatures"] > 0
            assert summary["max_possible_coverage"] > 0
            assert len(summary["date_range"]) == 2  # (earliest_date, latest_date)
            assert isinstance(summary["date_range"][0], str)  # earliest_date
            assert isinstance(summary["date_range"][1], str)  # latest_date

    def test_dataset_caching_and_cache_clearing_functionality(self):
        """Test dataset caching behavior and cache clearing functionality"""
        # Arrange: Initialize analyzer
        analyzer = CoverageAnalyzer()

        # Assert: Initially cache should be empty
        assert analyzer._dataset_cache is None
        assert analyzer._signature_cache is None

        # Act: First call to get_dataset_summary should load and cache data
        import time
        start_time = time.time()
        summary1 = analyzer.get_dataset_summary()
        first_call_duration = time.time() - start_time

        # Assert: Cache should now be populated
        assert analyzer._dataset_cache is not None
        assert analyzer._signature_cache is not None
        assert len(analyzer._dataset_cache) > 0
        assert len(analyzer._signature_cache) > 0

        # Act: Second call should use cached data (should be faster)
        start_time = time.time()
        summary2 = analyzer.get_dataset_summary()
        second_call_duration = time.time() - start_time

        # Assert: Results should be identical and second call faster
        assert summary1 == summary2
        assert second_call_duration < first_call_duration * 0.5  # At least 50% faster

        # Act: Clear cache
        analyzer.clear_cache()

        # Assert: Cache should be empty after clearing
        assert analyzer._dataset_cache is None
        assert analyzer._signature_cache is None

        # Act: Third call after cache clear should reload data
        start_time = time.time()
        summary3 = analyzer.get_dataset_summary()
        third_call_duration = time.time() - start_time

        # Assert: Results should be identical but timing similar to first call
        assert summary1 == summary3
        assert third_call_duration > second_call_duration  # Should be slower than cached call
        assert analyzer._dataset_cache is not None  # Cache repopulated