# CoverageAnalyzer Class Interface: Technical Architecture Design

## Overview
The `CoverageAnalyzer` class serves as the core analysis engine powering the Interactive Alignment Workbench CLI commands. It wraps existing components without modification, providing coverage insights and recommendations that transform the current trial-and-error workflow.

## Design Philosophy

### **Wrapper Architecture Pattern**
- **Zero Modifications**: No changes to existing `TimeSeriesAligner`, `IndexAggregator`, or `FilterValidator` classes
- **Delegation Pattern**: Leverages existing components for all core operations
- **Analysis Layer**: Adds coverage analysis capabilities on top of existing alignment logic
- **Composable Design**: Can be used independently or integrated with CLI commands

### **Integration with Existing Components**
```python
# CoverageAnalyzer uses existing components via composition
class CoverageAnalyzer:
    def __init__(self):
        self.aggregator = IndexAggregator()      # Existing data loading/filtering
        self.aligner = TimeSeriesAligner()       # Existing alignment logic
        self.logger = AppLogger.get_logger(__name__)  # Existing logging
```

## Class Interface Specification

### **Core Class Definition**
```python
from typing import Dict, List, Tuple, Optional, Set
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from chart.index_aggregator import IndexAggregator, FilterValidator
from common.time_series_aligner import TimeSeriesAligner
from common.logger import AppLogger

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

    def __init__(self, input_csv: Path = Path("data/output.csv")):
        self.input_csv = input_csv
        self.aggregator = IndexAggregator()
        self.aligner = TimeSeriesAligner()
        self.logger = AppLogger.get_logger(__name__)
        self._dataset_cache: Optional[pd.DataFrame] = None
        self._signature_cache: Optional[Set[str]] = None
```

### **Primary Analysis Methods**

#### **1. Single Filter Analysis**
```python
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

    Example:
        result = analyzer.analyze_filter_combination("SV*", "Card")
        print(f"Coverage: {result.coverage_percentage:.1%}")
        print(f"Records aligned: {result.records_aligned}")
    """
```

#### **2. Recommendation Discovery**
```python
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

    Algorithm:
        1. Enumerate common filter patterns (SV*, SWSH*, individual sets)
        2. Test each pattern combination against alignment algorithm
        3. Rank by coverage percentage, record count, and alignment quality
        4. Return top viable configurations meeting minimum threshold

    Example:
        recommendations = analyzer.discover_viable_configurations(min_coverage=0.95)
        for rec in recommendations[:3]:
            print(f"{rec.rank}. {rec.description}: {rec.coverage_result.coverage_percentage:.1%}")
    """
```

#### **3. Alternative Suggestion Engine**
```python
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

    Strategy:
        1. Analyze why original config failed (coverage gaps, problematic signatures)
        2. Generate alternatives: enable fallback, reduce scope, change types
        3. Test alternatives and rank by improvement potential
        4. Return actionable suggestions with trade-off analysis

    Example:
        alternatives = analyzer.suggest_alternatives({
            "sets": "SWSH*,SV*", "types": "Card", "period": "3M"
        })
        for alt in alternatives:
            print(f"Option: {alt.command_string}")
            print(f"Result: {alt.coverage_result.coverage_percentage:.1%} coverage")
    """
```

### **Supporting Analysis Methods**

#### **4. Dataset Introspection**
```python
def get_dataset_summary(self) -> Dict[str, any]:
    """
    Get high-level dataset statistics for analysis context.

    Returns:
        Dictionary with dataset metadata:
        - total_records: Total records in dataset
        - unique_signatures: Number of unique signatures
        - date_range: (start_date, end_date) tuple
        - available_sets: List of all sets in dataset
        - available_types: List of all types in dataset
        - max_possible_coverage: Theoretical maximum coverage percentage
    """

def get_signature_coverage_by_date(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze signature coverage patterns across all dates.

    Args:
        df: Filtered DataFrame for analysis

    Returns:
        DataFrame with columns: period_end_date, signature_count, coverage_percentage
        Sorted by coverage_percentage descending to identify optimal start dates
    """

def identify_problematic_signatures(
    self,
    df: pd.DataFrame,
    target_coverage: float = 1.0
) -> List[Tuple[str, float]]:
    """
    Identify signatures that prevent achieving target coverage.

    Args:
        df: Filtered DataFrame for analysis
        target_coverage: Target coverage percentage (default: 1.0 for 100%)

    Returns:
        List of (signature_name, availability_percentage) tuples
        sorted by availability (least available first)
    """
```

#### **5. Performance and Caching**
```python
def _load_and_cache_dataset(self) -> pd.DataFrame:
    """
    Load dataset with caching for performance optimization.

    Caches the full dataset in memory to avoid repeated CSV reads
    during analysis operations. Cache is invalidated if input_csv
    file modification time changes.
    """

def _generate_signature_key(self, row: pd.Series) -> str:
    """
    Generate consistent signature keys for analysis.

    Args:
        row: DataFrame row with set, name, type columns

    Returns:
        Signature key in format: "SET_NAME_TYPE" (e.g., "SV01_Charizard_Card")
    """

def clear_cache(self) -> None:
    """Clear internal dataset and signature caches."""
```

## Integration Patterns with Existing Components

### **1. IndexAggregator Integration**
```python
# CoverageAnalyzer reuses existing data loading and filtering
def analyze_filter_combination(self, sets: str, types: str, period: str = "3M", allow_fallback: bool = False) -> CoverageResult:
    # Step 1: Use existing IndexAggregator for data loading and filtering
    filtered_df = self.aggregator.create_subset(
        self.input_csv, sets, types, period, allow_fallback
    )

    # Step 2: Extract alignment metadata from TimeSeriesAligner logs
    # (No modifications to aligner - analyze results and logs)

    # Step 3: Generate CoverageResult with extracted metrics
    return CoverageResult(...)
```

### **2. TimeSeriesAligner Integration**
```python
# CoverageAnalyzer analyzes alignment results without modifying the aligner
def _extract_alignment_metrics(self, df: pd.DataFrame, allow_fallback: bool) -> Dict[str, any]:
    """
    Extract alignment metrics by analyzing TimeSeriesAligner behavior.

    Uses existing aligner methods to perform alignment and analyzes
    the results to extract coverage statistics and quality metrics.
    """
    # Call existing aligner method
    aligned_df = self.aligner.align_complete(df, allow_fallback)

    # Analyze results to extract metrics
    if aligned_df.empty:
        return {"coverage_percentage": 0.0, "alignment_successful": False}

    # Extract metrics from aligned result and original data
    return {
        "coverage_percentage": self._calculate_coverage_percentage(df, aligned_df),
        "records_aligned": len(aligned_df),
        "gap_fills_required": self._count_gap_fills(df, aligned_df),
        "alignment_successful": True
    }
```

### **3. FilterValidator Integration**
```python
# CoverageAnalyzer extends FilterValidator for recommendation generation
def _generate_filter_combinations(self) -> List[Dict[str, str]]:
    """
    Generate common filter combinations for recommendation testing.

    Uses FilterValidator.VALID_SETS and VALID_TYPES to generate
    realistic filter combinations that users are likely to try.
    """
    combinations = []

    # Individual generation patterns
    for generation in ['SV*', 'SWSH*']:
        for type_pattern in ['Card', '*Box', 'Booster Box', 'Elite Trainer Box']:
            combinations.append({
                "sets": generation,
                "types": type_pattern,
                "period": "3M"
            })

    # Individual set patterns
    for set_name in FilterValidator.VALID_SETS:
        combinations.append({
            "sets": set_name,
            "types": "*",
            "period": "3M"
        })

    return combinations
```

## Error Handling and Logging Integration

### **Consistent Error Handling**
```python
def analyze_filter_combination(self, sets: str, types: str, period: str = "3M", allow_fallback: bool = False) -> CoverageResult:
    """Analysis method with comprehensive error handling."""
    try:
        self.logger.info(f"Analyzing filter combination: sets={sets}, types={types}, period={period}")

        # Validate filters using existing FilterValidator
        valid_sets = FilterValidator.expand_set_pattern(sets)
        valid_types = FilterValidator.expand_type_pattern(types)

        if not valid_sets or not valid_types:
            self.logger.warning(f"Invalid filter patterns: sets={sets}, types={types}")
            return CoverageResult(
                filter_config={"sets": sets, "types": types, "period": period},
                coverage_percentage=0.0,
                # ... other default values for failed analysis
            )

        # Proceed with analysis using existing components
        # ...

    except Exception as e:
        self.logger.error(f"Coverage analysis failed: {e}")
        raise
```

### **Performance Logging**
```python
import time
from functools import wraps

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

@_log_performance("Coverage analysis")
def analyze_filter_combination(self, ...):
    # Method implementation
```

## Usage Examples

### **CLI Command Integration**
```python
# discover command implementation
def handle_discover_command(args):
    analyzer = CoverageAnalyzer(Path(args.input_csv))
    recommendations = analyzer.discover_viable_configurations(
        min_coverage=args.min_coverage,
        max_recommendations=10 if args.format == 'detailed' else 3
    )

    print("🔍 Analyzing dataset...")
    print(f"📊 Recommended Configurations (Coverage ≥ {args.min_coverage:.0%}):\n")

    for rec in recommendations:
        print(f"{rec.rank}. {rec.description}")
        print(f"   Command: {rec.command_string}")
        print(f"   Coverage: {rec.coverage_result.coverage_percentage:.1%}")
        print(f"   Records: {rec.estimated_records} aligned records\n")

# analyze command implementation
def handle_analyze_command(args):
    analyzer = CoverageAnalyzer(Path(args.input_csv))
    result = analyzer.analyze_filter_combination(
        args.sets, args.types, args.period
    )

    if result.coverage_percentage > 0:
        print("✅ Filter Configuration:")
        print(f"   Coverage: {result.coverage_percentage:.1%}")
        print(f"   Records: {result.records_aligned} aligned")
    else:
        print("❌ Alignment Failed")
        if args.suggest_alternatives:
            alternatives = analyzer.suggest_alternatives(result.filter_config)
            print("🔧 Suggested Solutions:")
            for alt in alternatives:
                print(f"Option: {alt.command_string}")
```

## Testing and Validation Integration

### **Test Compatibility**
```python
# CoverageAnalyzer designed for easy testing using existing test patterns
class TestCoverageAnalyzer:
    def setup_class(self):
        AppLogger.get_logger(__name__)  # Initialize logging like existing tests

    def test_sv_cards_analysis(self):
        """Test analysis of known working configuration."""
        analyzer = CoverageAnalyzer(Path("data/output.csv"))
        result = analyzer.analyze_filter_combination("SV*", "Card")

        assert result.coverage_percentage == 1.0  # 100% coverage expected
        assert result.records_aligned == 1209     # Known record count
        assert not result.fallback_required       # Perfect alignment

    def test_cross_generation_analysis(self):
        """Test analysis of known problematic configuration."""
        analyzer = CoverageAnalyzer(Path("data/output.csv"))
        result = analyzer.analyze_filter_combination("SWSH*,SV*", "Card")

        assert result.coverage_percentage < 1.0   # <100% coverage expected
        assert result.fallback_required           # Fallback mode needed
        assert len(result.missing_signatures) > 0 # Some signatures missing
```

This `CoverageAnalyzer` interface provides a comprehensive analysis engine that transforms the existing robust alignment components into an interactive, insight-driven system while maintaining zero breaking changes and full backward compatibility.