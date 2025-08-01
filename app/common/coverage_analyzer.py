#!/usr/bin/env python3
"""
Coverage Analyzer for TCGPlayer Time Series Alignment

Provides coverage insights and recommendations by analyzing filter
combinations against the existing robust 2-step alignment process
without modifying any core alignment logic.
"""

from typing import Dict, List, Tuple, Optional, Set
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, asdict
import time
from functools import wraps

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from chart.index_aggregator import IndexAggregator, FilterValidator
from common.time_series_aligner import TimeSeriesAligner
from common.logger import AppLogger
from common.helpers import CoverageResultFactory, FilterValidationHelper


def _log_performance(method_name: str):
    """Decorator for performance logging of analysis operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            duration = time.time() - start_time
            self.logger.info(f"{method_name} completed in {duration:.2f}s")
            return result
        return wrapper
    return decorator


@dataclass
class CoverageResult:
    """Data structure for coverage analysis results"""
    filter_config: Dict[str, str]           # Original filter configuration
    coverage_percentage: float              # Coverage achieved (0.0-1.0)
    signatures_found: int                   # Number of signatures with coverage
    signatures_total: int                   # Total signatures in filtered dataset
    optimal_start_date: Optional[str]       # Best alignment start date (YYYY-MM-DD)
    records_before_start: int               # Records excluded before optimal start
    records_aligned: int                    # Records in final aligned dataset
    time_series_points: int                 # Number of time series data points
    gap_fills_required: int                 # Number of signature gaps filled
    missing_signatures: List[str]           # Signatures causing coverage gaps
    fallback_required: bool                 # Whether fallback mode is needed
    quality_score: float                    # Overall alignment quality (0.0-1.0)


@dataclass
class RecommendationResult:
    """Data structure for filter recommendations"""
    rank: int                               # Recommendation ranking (1=best)
    filter_config: Dict[str, str]           # Recommended filter configuration
    coverage_result: CoverageResult         # Coverage analysis for this config
    description: str                        # Human-readable description
    command_string: str                     # Executable command string
    estimated_records: int                  # Estimated final record count


class CoverageAnalyzer:
    """
    Coverage analysis engine for TCGPlayer time series alignment.

    Provides coverage insights and recommendations by analyzing filter
    combinations against the existing robust 2-step alignment process
    without modifying any core alignment logic.
    """

    def __init__(
        self,
        input_csv: Path = Path("data/output.csv"),
        aggregator: Optional[IndexAggregator] = None,
        aligner: Optional[TimeSeriesAligner] = None,
        validator: Optional[FilterValidator] = None
    ):
        self.input_csv = input_csv
        self.aggregator = aggregator or IndexAggregator()
        self.aligner = aligner or TimeSeriesAligner()
        self.validator = validator or FilterValidator()
        self.logger = AppLogger.get_logger(__name__)
        self._dataset_cache: Optional[pd.DataFrame] = None
        self._signature_cache: Optional[Set[str]] = None

    @_log_performance("Coverage analysis")
    def analyze_filter_combination(
        self,
        sets: str,
        types: str,
        period: str = "3M",
        allow_fallback: bool = False
    ) -> CoverageResult:
        """
        Analyze coverage for a specific filter combination.

        This method powers the 'analyze' CLI command by providing detailed
        coverage analysis for user-specified filter combinations.

        Args:
            sets: Set filter pattern (e.g., "SV*", "SV01,SV02")
            types: Type filter pattern (e.g., "*Box", "Card")
            period: Period filter (default: "3M")
            allow_fallback: Enable fallback mode for <100% coverage scenarios

        Returns:
            CoverageResult with detailed analysis including coverage percentage,
            optimal alignment dates, record counts, and quality metrics
        """
        try:
            self.logger.info(f"Analyzing filter combination: sets={sets}, types={types}, period={period}")

            # One-liner filter validation using helper
            if not FilterValidationHelper.is_valid_filter_combination(sets, types):
                self.logger.warning(f"Invalid filter patterns: sets={sets}, types={types}")
                return CoverageResultFactory.create_empty({"sets": sets, "types": types, "period": period})

            # Load and filter dataset
            df = self._load_and_cache_dataset()
            if df.empty:
                return self._empty_coverage_result({"sets": sets, "types": types, "period": period})

            # Apply filters using existing aggregator logic
            filtered_df = self.aggregator.apply_filters(df, sets, types, period)
            if filtered_df.empty:
                return self._empty_coverage_result({"sets": sets, "types": types, "period": period})

            # Extract alignment metrics by analyzing aligner behavior
            alignment_metrics = self._extract_alignment_metrics(filtered_df, allow_fallback)

            # Generate coverage result using factory
            return CoverageResultFactory.create_from_metrics({"sets": sets, "types": types, "period": period}, alignment_metrics)

        except Exception as e:
            self.logger.error(f"Coverage analysis failed: {e}")
            raise

    @_log_performance("Configuration discovery")
    def discover_viable_configurations(
        self,
        min_coverage: float = 0.9,
        max_recommendations: int = 10,
        include_fallback_options: bool = True
    ) -> List[RecommendationResult]:
        """
        Discover viable filter combinations with high coverage rates.

        This method powers the 'discover' CLI command by analyzing the dataset
        and recommending filter combinations likely to achieve successful alignment.

        Args:
            min_coverage: Minimum coverage threshold (0.0-1.0)
            max_recommendations: Maximum number of recommendations to return
            include_fallback_options: Include configurations requiring fallback mode

        Returns:
            List of RecommendationResult objects ranked by coverage quality
        """
        self.logger.info(f"Discovering configurations with min_coverage={min_coverage}")

        recommendations = []
        filter_combinations = self._generate_filter_combinations()

        for rank, combo in enumerate(filter_combinations, 1):
            if len(recommendations) >= max_recommendations:
                break

            # Test this combination
            coverage_result = self.analyze_filter_combination(
                combo["sets"], combo["types"], combo["period"], allow_fallback=include_fallback_options
            )

            # Check if it meets minimum coverage threshold
            if coverage_result.coverage_percentage >= min_coverage:
                description = self._generate_description(combo, coverage_result)
                command_string = f'--sets "{combo["sets"]}" --types "{combo["types"]}" --period "{combo["period"]}"'

                recommendations.append(RecommendationResult(
                    rank=len(recommendations) + 1,
                    filter_config=combo,
                    coverage_result=coverage_result,
                    description=description,
                    command_string=command_string,
                    estimated_records=coverage_result.records_aligned
                ))

        # One-liner sort and rank update
        recommendations.sort(key=lambda x: (x.coverage_result.coverage_percentage, x.estimated_records), reverse=True)
        [setattr(rec, 'rank', i) for i, rec in enumerate(recommendations, 1)]

        self.logger.info(f"Found {len(recommendations)} viable configurations")
        return recommendations

    def suggest_alternatives(
        self,
        failed_config: Dict[str, str],
        max_alternatives: int = 3
    ) -> List[RecommendationResult]:
        """
        Suggest alternative configurations when a filter combination fails.

        This method powers the failure analysis feature in the 'analyze' CLI command
        by suggesting modifications to failed filter combinations.

        Args:
            failed_config: Original filter configuration that failed alignment
            max_alternatives: Maximum alternative suggestions to return

        Returns:
            List of RecommendationResult objects with alternative configurations
        """
        self.logger.info(f"Suggesting alternatives for failed config: {failed_config}")

        alternatives = []

        # Strategy 1: Enable fallback mode
        fallback_result = self.analyze_filter_combination(
            failed_config["sets"], failed_config["types"], failed_config["period"], allow_fallback=True
        )
        if fallback_result.coverage_percentage > 0:
            alternatives.append(RecommendationResult(
                rank=1,
                filter_config=failed_config,
                coverage_result=fallback_result,
                description="Enable Fallback Mode",
                command_string=f'--sets "{failed_config["sets"]}" --types "{failed_config["types"]}" --period "{failed_config["period"]}" --allow-fallback',
                estimated_records=fallback_result.records_aligned
            ))

        # Strategy 2: Reduce scope - try individual generations
        if "," in failed_config["sets"] or failed_config["sets"] == "*":
            for generation in ["SV*", "SWSH*"]:
                gen_result = self.analyze_filter_combination(
                    generation, failed_config["types"], failed_config["period"]
                )
                if gen_result.coverage_percentage > 0.8 and len(alternatives) < max_alternatives:
                    alternatives.append(RecommendationResult(
                        rank=len(alternatives) + 1,
                        filter_config={"sets": generation, "types": failed_config["types"], "period": failed_config["period"]},
                        coverage_result=gen_result,
                        description=f"Focus on {generation.replace('*', '')} Generation",
                        command_string=f'--sets "{generation}" --types "{failed_config["types"]}" --period "{failed_config["period"]}"',
                        estimated_records=gen_result.records_aligned
                    ))

        # Strategy 3: Change types if mixing types
        if failed_config["types"] == "*" and len(alternatives) < max_alternatives:
            for type_pattern in ["Card", "*Box"]:
                type_result = self.analyze_filter_combination(
                    failed_config["sets"], type_pattern, failed_config["period"]
                )
                if type_result.coverage_percentage > 0.8 and len(alternatives) < max_alternatives:
                    alternatives.append(RecommendationResult(
                        rank=len(alternatives) + 1,
                        filter_config={"sets": failed_config["sets"], "types": type_pattern, "period": failed_config["period"]},
                        coverage_result=type_result,
                        description=f"Focus on {type_pattern.replace('*', '')} Types Only",
                        command_string=f'--sets "{failed_config["sets"]}" --types "{type_pattern}" --period "{failed_config["period"]}"',
                        estimated_records=type_result.records_aligned
                    ))

        # Strategy 0: If no alternatives found, use helper for default configs
        if len(alternatives) == 0:
            self.logger.info("No targeted alternatives found, providing default recommendations")
            default_configs = FilterValidationHelper.get_default_configurations()

            for i, config in enumerate(default_configs[:max_alternatives]):
                default_result = self.analyze_filter_combination(
                    config["sets"], config["types"], config["period"]
                )
                if default_result.coverage_percentage > 0:
                    alternatives.append(RecommendationResult(
                        rank=i + 1,
                        filter_config={"sets": config["sets"], "types": config["types"], "period": config["period"]},
                        coverage_result=default_result,
                        description=config["description"],
                        command_string=f'--sets "{config["sets"]}" --types "{config["types"]}" --period "{config["period"]}"',
                        estimated_records=default_result.records_aligned
                    ))

        return alternatives[:max_alternatives]

    def get_dataset_summary(self) -> Dict[str, any]:
        """
        Get high-level dataset statistics for analysis context.

        Returns:
            Dictionary with dataset metadata
        """
        df = self._load_and_cache_dataset()
        if df.empty:
            return {
                "total_records": 0,
                "unique_signatures": 0,
                "date_range": (None, None),
                "available_sets": [],
                "available_types": [],
                "max_possible_coverage": 0.0
            }

        # Cache signatures if not already cached
        if self._signature_cache is None:
            self._signature_cache = self._get_signature_set(df)

        signatures = self._signature_cache

        return {
            "total_records": len(df),
            "unique_signatures": len(signatures),
            "date_range": (df["period_end_date"].min().strftime("%Y-%m-%d"),
                          df["period_end_date"].max().strftime("%Y-%m-%d")),
            "available_sets": sorted(df["set"].unique().tolist()),
            "available_types": sorted(df["type"].unique().tolist()),
            "max_possible_coverage": len(signatures)
        }

    def _load_and_cache_dataset(self) -> pd.DataFrame:
        """
        Load dataset with caching for performance optimization.

        Caches the full dataset in memory to avoid repeated CSV reads
        during analysis operations.
        """
        if self._dataset_cache is None:
            self.logger.info(f"Loading and caching dataset from {self.input_csv}")
            self._dataset_cache = self.aggregator.read_csv(self.input_csv)
        return self._dataset_cache

    def _extract_alignment_metrics(self, df: pd.DataFrame, allow_fallback: bool) -> Dict[str, any]:
        """
        Extract alignment metrics by analyzing TimeSeriesAligner behavior.

        Uses existing aligner methods to perform alignment and analyzes
        the results to extract coverage statistics and quality metrics.
        """
        # Get signatures before alignment
        original_signatures = self._get_signature_set(df)
        original_record_count = len(df)

        # Call existing aligner method
        aligned_df = self.aligner.align_complete(df, allow_fallback)

        # Analyze results to extract metrics
        if aligned_df.empty:
            return {
                "coverage_percentage": 0.0,
                "signatures_found": 0,
                "signatures_total": len(original_signatures),
                "optimal_start_date": None,
                "records_before_start": 0,
                "records_aligned": 0,
                "time_series_points": 0,
                "gap_fills_required": 0,
                "missing_signatures": list(original_signatures),
                "fallback_required": False,
                "quality_score": 0.0
            }

        # Extract metrics from aligned result
        aligned_signatures = self._get_signature_set(aligned_df)
        coverage_percentage = len(aligned_signatures) / len(original_signatures) if original_signatures else 0.0

        # Estimate records before start by comparing original vs aligned
        records_before_start = max(0, original_record_count - len(aligned_df) - 100)  # Rough estimate

        # Calculate missing signatures
        missing_signatures = list(original_signatures - aligned_signatures)

        # Determine optimal start date (first date in aligned data)
        optimal_start_date = None
        if not aligned_df.empty:
            optimal_start_date = aligned_df["period_end_date"].min().strftime("%Y-%m-%d")

        # Calculate time series points (unique dates)
        time_series_points = aligned_df["period_end_date"].nunique() if not aligned_df.empty else 0

        # Estimate gap fills (very rough - based on expected vs actual records)
        expected_records = len(aligned_signatures) * time_series_points
        actual_records = len(aligned_df)
        gap_fills_required = max(0, expected_records - actual_records)

        # Calculate quality score
        quality_score = coverage_percentage * (0.8 + 0.2 * (1.0 if gap_fills_required == 0 else 0.5))

        return {
            "coverage_percentage": coverage_percentage,
            "signatures_found": len(aligned_signatures),
            "signatures_total": len(original_signatures),
            "optimal_start_date": optimal_start_date,
            "records_before_start": records_before_start,
            "records_aligned": len(aligned_df),
            "time_series_points": time_series_points,
            "gap_fills_required": gap_fills_required,
            "missing_signatures": missing_signatures,
            "fallback_required": allow_fallback and coverage_percentage < 1.0,
            "quality_score": quality_score
        }

    def _generate_filter_combinations(self) -> List[Dict[str, str]]:
        """
        Generate common filter combinations for recommendation testing.

        Uses FilterValidator.VALID_SETS and VALID_TYPES to generate
        realistic filter combinations that users are likely to try.
        """
        combinations = []

        # High-priority patterns (generation-based) - one-liner nested comprehension
        combinations.extend([{"sets": gen, "types": typ, "period": "3M"}
                           for gen in ['SV*', 'SWSH*']
                           for typ in ['Card', '*Box', 'Booster Box', 'Elite Trainer Box']])

        # Medium-priority patterns (individual sets) - one-liner comprehension
        combinations.extend([{"sets": s, "types": "*", "period": "3M"} for s in sorted(FilterValidator.VALID_SETS)])

        # Lower-priority patterns (broader combinations)
        combinations.extend([
            {"sets": "*", "types": "Card", "period": "3M"},
            {"sets": "*", "types": "*Box", "period": "3M"},
            {"sets": "SV01,SV02,SV03", "types": "*", "period": "3M"}
        ])

        return combinations

    def _generate_description(self, combo: Dict[str, str], result: CoverageResult) -> str:
        """One-liner description generation using helper."""
        return FilterValidationHelper.generate_description(combo, result.coverage_percentage)

    def _get_signature_set(self, df: pd.DataFrame) -> Set[str]:
        """Generate set of unique signatures from DataFrame."""
        if df.empty:
            return set()
        return set(df.apply(lambda row: f"{row['set']}_{row['name']}_{row['type']}", axis=1))

    def _empty_coverage_result(self, filter_config: Dict[str, str]) -> CoverageResult:
        """One-liner empty coverage result generation using factory."""
        return CoverageResultFactory.create_empty(filter_config)

    def clear_cache(self) -> None:
        """Clear internal dataset and signature caches."""
        self._dataset_cache = None
        self._signature_cache = None
        self.logger.info("Dataset cache cleared")