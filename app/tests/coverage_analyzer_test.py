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


class TestCoverageResult:
    """Test cases for CoverageResult dataclass"""

    def setup_class(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_coverage_result_creation_with_successful_analysis(self):
        """Test CoverageResult creation with successful analysis data"""
        # Arrange: Prepare successful analysis data (like SV* Cards)
        filter_config = {"sets": "SV*", "types": "Card", "period": "3M"}

        # Act: Create CoverageResult with successful analysis
        result = CoverageResult(
            filter_config=filter_config,
            coverage_percentage=1.0,
            signatures_found=13,
            signatures_total=13,
            optimal_start_date="2025-04-28",
            records_before_start=57,
            records_aligned=1209,
            time_series_points=93,
            gap_fills_required=50,
            missing_signatures=[],
            fallback_required=False,
            quality_score=1.0
        )

        # Assert: Verify all fields are accessible and have correct values
        assert result.filter_config == filter_config
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

    def test_coverage_result_creation_with_failed_analysis(self):
        """Test CoverageResult creation with failed analysis data (0% coverage)"""
        # Arrange: Prepare failed analysis data (like cross-generation mixing)
        filter_config = {"sets": "SWSH*,SV*", "types": "Card", "period": "3M"}
        missing_sigs = ["SWSH06_Charizard_Card", "SV01_Pikachu_Card"]

        # Act: Create CoverageResult with failed analysis
        result = CoverageResult(
            filter_config=filter_config,
            coverage_percentage=0.0,
            signatures_found=0,
            signatures_total=20,
            optimal_start_date=None,
            records_before_start=0,
            records_aligned=0,
            time_series_points=0,
            gap_fills_required=0,
            missing_signatures=missing_sigs,
            fallback_required=False,
            quality_score=0.0
        )

        # Assert: Verify failed analysis fields are correct
        assert result.filter_config == filter_config
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

    def test_coverage_result_creation_with_partial_coverage(self):
        """Test CoverageResult creation with partial coverage requiring fallback"""
        # Arrange: Prepare partial coverage data (like 95% with fallback)
        filter_config = {"sets": "SWSH*,SV*", "types": "Card", "period": "3M"}
        missing_sigs = ["SWSH06_Charizard_Card"]

        # Act: Create CoverageResult with partial coverage
        result = CoverageResult(
            filter_config=filter_config,
            coverage_percentage=0.95,
            signatures_found=19,
            signatures_total=20,
            optimal_start_date="2025-04-28",
            records_before_start=67,
            records_aligned=1859,
            time_series_points=93,
            gap_fills_required=212,
            missing_signatures=missing_sigs,
            fallback_required=True,
            quality_score=0.85
        )

        # Assert: Verify partial coverage fields are correct
        assert result.coverage_percentage == 0.95
        assert result.signatures_found == 19
        assert result.signatures_total == 20
        assert result.fallback_required is True
        assert len(result.missing_signatures) == 1
        assert result.quality_score == 0.85

    def test_coverage_result_field_types(self):
        """Test that CoverageResult fields have correct types"""
        # Arrange & Act: Create result with minimal data
        result = CoverageResult(
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
            coverage_percentage=0.9,
            signatures_found=10,
            signatures_total=11,
            optimal_start_date="2025-04-28",
            records_before_start=50,
            records_aligned=1000,
            time_series_points=90,
            gap_fills_required=25,
            missing_signatures=["SV10_Missing_Card"],
            fallback_required=False,
            quality_score=0.88
        )

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

    def test_coverage_result_asdict_conversion(self):
        """Test CoverageResult conversion to dictionary for JSON serialization"""
        # Arrange: Create result for conversion
        filter_config = {"sets": "SV*", "types": "Card", "period": "3M"}
        result = CoverageResult(
            filter_config=filter_config,
            coverage_percentage=1.0,
            signatures_found=13,
            signatures_total=13,
            optimal_start_date="2025-04-28",
            records_before_start=57,
            records_aligned=1209,
            time_series_points=93,
            gap_fills_required=50,
            missing_signatures=[],
            fallback_required=False,
            quality_score=1.0
        )

        # Act: Convert to dictionary
        result_dict = asdict(result)

        # Assert: Verify dictionary structure and content
        assert isinstance(result_dict, dict)
        assert len(result_dict) == 12  # All 12 fields present
        assert result_dict["filter_config"] == filter_config
        assert result_dict["coverage_percentage"] == 1.0
        assert result_dict["signatures_found"] == 13
        assert result_dict["optimal_start_date"] == "2025-04-28"
        assert result_dict["missing_signatures"] == []
        assert result_dict["fallback_required"] is False

    def test_coverage_result_with_none_optional_fields(self):
        """Test CoverageResult creation with None values for optional fields"""
        # Arrange & Act: Create result with None optimal_start_date
        result = CoverageResult(
            filter_config={"sets": "invalid", "types": "invalid", "period": "3M"},
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

    def test_recommendation_result_creation_with_complete_data(self):
        """Test RecommendationResult creation with complete recommendation data"""
        # Arrange: Prepare CoverageResult for embedding
        coverage_result = CoverageResult(
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
            coverage_percentage=1.0,
            signatures_found=13,
            signatures_total=13,
            optimal_start_date="2025-04-28",
            records_before_start=57,
            records_aligned=1209,
            time_series_points=93,
            gap_fills_required=50,
            missing_signatures=[],
            fallback_required=False,
            quality_score=1.0
        )

        # Act: Create RecommendationResult with complete data
        recommendation = RecommendationResult(
            rank=1,
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
            coverage_result=coverage_result,
            description="SV Cards (Complete)",
            command_string='--sets "SV*" --types "Card" --period "3M"',
            estimated_records=1209
        )

        # Assert: Verify all fields are accessible and have correct values
        assert recommendation.rank == 1
        assert recommendation.filter_config == {"sets": "SV*", "types": "Card", "period": "3M"}
        assert recommendation.coverage_result == coverage_result
        assert recommendation.description == "SV Cards (Complete)"
        assert recommendation.command_string == '--sets "SV*" --types "Card" --period "3M"'
        assert recommendation.estimated_records == 1209

    def test_recommendation_result_creation_with_fallback_scenario(self):
        """Test RecommendationResult creation with fallback mode requirement"""
        # Arrange: Prepare CoverageResult with fallback mode
        coverage_result = CoverageResult(
            filter_config={"sets": "SWSH*,SV*", "types": "Card", "period": "3M"},
            coverage_percentage=0.95,
            signatures_found=19,
            signatures_total=20,
            optimal_start_date="2025-04-28",
            records_before_start=67,
            records_aligned=1859,
            time_series_points=93,
            gap_fills_required=212,
            missing_signatures=["SWSH06_Charizard_Card"],
            fallback_required=True,
            quality_score=0.85
        )

        # Act: Create RecommendationResult for fallback scenario
        recommendation = RecommendationResult(
            rank=2,
            filter_config={"sets": "SWSH*,SV*", "types": "Card", "period": "3M"},
            coverage_result=coverage_result,
            description="SWSH/SV Cards (Excellent)",
            command_string='--sets "SWSH*,SV*" --types "Card" --period "3M" --allow-fallback',
            estimated_records=1859
        )

        # Assert: Verify fallback scenario fields are correct
        assert recommendation.rank == 2
        assert recommendation.coverage_result.fallback_required is True
        assert recommendation.coverage_result.coverage_percentage == 0.95
        assert recommendation.description == "SWSH/SV Cards (Excellent)"
        assert "--allow-fallback" in recommendation.command_string
        assert recommendation.estimated_records == 1859

    def test_recommendation_result_field_types(self):
        """Test that RecommendationResult fields have correct types"""
        # Arrange: Create minimal CoverageResult
        coverage_result = CoverageResult(
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
            coverage_percentage=0.9,
            signatures_found=10,
            signatures_total=11,
            optimal_start_date="2025-04-28",
            records_before_start=50,
            records_aligned=1000,
            time_series_points=90,
            gap_fills_required=25,
            missing_signatures=["SV10_Missing_Card"],
            fallback_required=False,
            quality_score=0.88
        )

        # Act: Create RecommendationResult
        recommendation = RecommendationResult(
            rank=3,
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
            coverage_result=coverage_result,
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

    def test_recommendation_result_asdict_conversion(self):
        """Test RecommendationResult conversion to dictionary for JSON serialization"""
        # Arrange: Create recommendation for conversion
        coverage_result = CoverageResult(
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
            coverage_percentage=1.0,
            signatures_found=13,
            signatures_total=13,
            optimal_start_date="2025-04-28",
            records_before_start=57,
            records_aligned=1209,
            time_series_points=93,
            gap_fills_required=50,
            missing_signatures=[],
            fallback_required=False,
            quality_score=1.0
        )

        recommendation = RecommendationResult(
            rank=1,
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
            coverage_result=coverage_result,
            description="SV Cards (Complete)",
            command_string='--sets "SV*" --types "Card" --period "3M"',
            estimated_records=1209
        )

        # Act: Convert to dictionary
        recommendation_dict = asdict(recommendation)

        # Assert: Verify dictionary structure and nested CoverageResult
        assert isinstance(recommendation_dict, dict)
        assert len(recommendation_dict) == 6  # All 6 fields present
        assert recommendation_dict["rank"] == 1
        assert recommendation_dict["filter_config"] == {"sets": "SV*", "types": "Card", "period": "3M"}
        assert recommendation_dict["description"] == "SV Cards (Complete)"
        assert recommendation_dict["command_string"] == '--sets "SV*" --types "Card" --period "3M"'
        assert recommendation_dict["estimated_records"] == 1209

        # Verify nested CoverageResult is properly serialized
        assert isinstance(recommendation_dict["coverage_result"], dict)
        assert recommendation_dict["coverage_result"]["coverage_percentage"] == 1.0
        assert recommendation_dict["coverage_result"]["signatures_found"] == 13

    def test_recommendation_result_with_alternative_suggestion(self):
        """Test RecommendationResult creation for alternative suggestions from failed filters"""
        # Arrange: Prepare CoverageResult for alternative suggestion
        coverage_result = CoverageResult(
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
            coverage_percentage=0.92,
            signatures_found=12,
            signatures_total=13,
            optimal_start_date="2025-04-28",
            records_before_start=43,
            records_aligned=1156,
            time_series_points=93,
            gap_fills_required=74,
            missing_signatures=["SV10_MissingCard_Card"],
            fallback_required=False,
            quality_score=0.89
        )

        # Act: Create RecommendationResult as alternative suggestion
        recommendation = RecommendationResult(
            rank=1,
            filter_config={"sets": "SV*", "types": "Card", "period": "3M"},
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