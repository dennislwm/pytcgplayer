# pytcgplayer

## Time Series Alignment Feature Roadmap

### Current Implementation Status

#### ✅ Implemented Steps
- **Step 1**: `_1_find_first_complete_coverage_date` - Find optimal starting point with maximum signature coverage
- **Step 2**: `_2_fill_signature_gaps_after_first_complete_date` - Fill missing signatures using forward-fill from previous dates
- **Step 3**: `_analyze_signatures` - Analyze signature patterns and date coverage distribution
- **Step 4**: `_select_signatures_by_common_count` - Select signatures using most-common-date-count strategy
- **Step 5**: `_apply_union_alignment` - Apply union-based (permissive) alignment across selected signatures
- **Step 6**: `_log_coverage_info` - Log alignment coverage metrics and quality information

#### 🔄 Feature Enhancement List - Missing Steps

**High Priority (Critical for production use):**
- **Step 7**: `_4_interpolate_missing_prices` - Fill missing price points using linear/cubic/forward-fill strategies
- **Step 8**: `_5_detect_and_smooth_outliers` - Identify and handle price anomalies using statistical methods
- **Step 9**: Configurable Parameters - Allow customization of alignment behavior via constructor/config

**Medium Priority (Important for robustness):**
- **Step 10**: `_6_apply_volume_weighted_selection` - Prioritize dates/signatures with higher trading volume
- **Step 11**: `_10_generate_alignment_quality_report` - Comprehensive quality assessment with actionable metrics
- **Step 12**: `_9_trim_to_optimal_date_range` - Automatically trim to date range with best coverage

**Lower Priority (Advanced features):**
- **Step 13**: `_3_normalize_temporal_frequency` - Convert irregular date intervals to consistent frequency
- **Step 14**: `_7_validate_cross_signature_consistency` - Ensure reasonable price relationships between related cards
- **Step 15**: `align_strict` - Perfect temporal alignment using intersection of signature dates (removed, needs reimplementation)
- **Step 16**: `align_adaptive` - Automatically select best alignment strategy based on data characteristics