# CLI Interface Specification: Interactive Alignment Workbench

## Overview
Three new CLI commands that transform the current trial-and-error workflow into guided discovery, following existing `argparse` patterns from `index_aggregator.py`.

## Command Architecture

### **File Structure**
```
chart/
├── alignment_workbench.py          # Main CLI entry point (new)
├── coverage_analyzer.py            # Coverage analysis engine (new)
├── index_aggregator.py             # Existing aggregation logic (unchanged)
└── index_chart.py                  # Existing chart generation (unchanged)
```

### **Command Invocation Pattern**
```bash
# Follows existing chart/ module pattern
PYTHONPATH=. pipenv run python chart/alignment_workbench.py [command] [options]
```

## Command Specifications

### **1. `discover` Command - Smart Filter Recommendations**

#### **Purpose**
Analyze dataset and recommend high-success filter combinations without requiring user input filters.

#### **Syntax**
```bash
python chart/alignment_workbench.py discover [input_csv] [options]
```

#### **Arguments**
```python
parser_discover.add_argument('input_csv', nargs='?', default='data/output.csv',
                           help='Input CSV file (default: data/output.csv)')
parser_discover.add_argument('--format', choices=['summary', 'detailed'], default='summary',
                           help='Output format: summary shows top 3, detailed shows all viable options')
parser_discover.add_argument('--min-coverage', type=float, default=0.9, metavar='PERCENT',
                           help='Minimum coverage threshold (0.0-1.0, default: 0.9)')
parser_discover.add_argument('--verbose', action='store_true',
                           help='Enable verbose logging')
```

#### **Output Format - Summary Mode**
```
🔍 Analyzing 3,688 records across 43 signatures...

📊 Recommended Configurations (Coverage ≥ 90%):

1. SV Cards Complete
   Command: --sets "SV*" --types "Card" --period "3M"
   Coverage: 100% (13/13 signatures from 2025-04-28)
   Records: 1,209 aligned records, 93 time series points

2. SV Boxes Mixed
   Command: --sets "SV*" --types "*Box" --period "3M"
   Coverage: 95% (12/13 signatures from 2025-04-28)
   Records: ~950 aligned records, 93 time series points

3. Premium Collection
   Command: --sets "SV01,SV02,SV03" --types "*" --period "3M"
   Coverage: 92% (11/12 signatures from 2025-04-22)
   Records: ~800 aligned records, 99 time series points

💡 Use --format detailed to see all viable combinations
💡 Use --min-coverage 0.8 to see more options with lower coverage
```

#### **Output Format - Detailed Mode**
```
📈 All Viable Configurations (Coverage ≥ 90%):

[Rank 1] SV Cards Complete - 100% Coverage
├─ Command: --sets "SV*" --types "Card" --period "3M"
├─ Signatures: 13/13 from 2025-04-28
├─ Timeline: 93 dates (2025-04-28 to 2025-07-29)
├─ Records: 1,216 → 1,209 aligned (57 pre-start excluded)
└─ Quality: Perfect alignment, no fallback required

[Rank 2] SV Boxes Mixed - 95% Coverage
├─ Command: --sets "SV*" --types "*Box" --period "3M"
├─ Signatures: 12/13 from 2025-04-28 (missing: SV10_Elite_Trainer_Box)
├─ Timeline: 93 dates (2025-04-28 to 2025-07-29)
├─ Records: ~950 aligned with 45 gap-fills
└─ Quality: High quality, minimal gap-filling

[Additional configurations...]

⚠️  Problematic Combinations to Avoid:
- Cross-generation mixing: "SWSH*,SV*" (max 95% coverage, requires fallback)
- Full wildcard: --sets "*" --types "*" (max 85% coverage, high gap-fill ratio)
```

### **2. `analyze` Command - Coverage Insight Engine**

#### **Purpose**
Analyze specific user filter combinations and provide detailed feedback, optimization suggestions.

#### **Syntax**
```bash
python chart/alignment_workbench.py analyze [input_csv] --sets PATTERN --types PATTERN [options]
```

#### **Arguments**
```python
parser_analyze.add_argument('input_csv', nargs='?', default='data/output.csv',
                          help='Input CSV file (default: data/output.csv)')
parser_analyze.add_argument('--sets', required=True,
                          help='Sets filter pattern (e.g., "SV*", "SV01,SV02")')
parser_analyze.add_argument('--types', required=True,
                          help='Types filter pattern (e.g., "*Box", "Card")')
parser_analyze.add_argument('--period', default='3M',
                          help='Period filter (default: 3M)')
parser_analyze.add_argument('--suggest-alternatives', action='store_true',
                          help='Show alternative filter suggestions when alignment fails')
parser_analyze.add_argument('--verbose', action='store_true',
                          help='Enable verbose logging')
```

#### **Output Format - Successful Analysis**
```bash
$ python chart/alignment_workbench.py analyze --sets "SV*" --types "Card"

📈 Coverage Analysis Results:

✅ Filter Configuration:
   Sets: SV* → ['SV01', 'SV02', 'SV03', 'SV03.5', 'SV04', 'SV04.5', 'SV05', 'SV06', 'SV06.5', 'SV07', 'SV08', 'SV08.5', 'SV09', 'SV10']
   Types: Card → ['Card']
   Period: 3M

📊 Alignment Quality:
   ✅ Optimal start date: 2025-04-28 (13/13 signatures - 100% coverage)
   ✅ Complete temporal alignment achieved
   ✅ No fallback mode required

📋 Record Summary:
   • Filtered: 3,688 → 1,216 records (33% of dataset)
   • Aligned: 1,216 → 1,209 records (57 pre-start excluded)
   • Time series: 93 date points from 2025-04-28 to 2025-07-29
   • Gap fills: 50 signature gaps filled via forward-fill

💡 Optimization Notes:
   • Perfect alignment achieved - no optimizations needed
   • Alternative: --allow-fallback not required for this combination
   • Timeline: 6 days of early data excluded for alignment quality
```

#### **Output Format - Failed Analysis with Suggestions**
```bash
$ python chart/alignment_workbench.py analyze --sets "SWSH*,SV*" --types "Card" --suggest-alternatives

📈 Coverage Analysis Results:

❌ Filter Configuration:
   Sets: SWSH*,SV* → ['SV01', 'SV02', ..., 'SWSH06', 'SWSH07', ..., 'SWSH12.5'] (23 sets)
   Types: Card → ['Card']
   Period: 3M

⚠️  Alignment Issues:
   ❌ No date achieves 100% signature coverage
   ❌ Maximum coverage: 2025-04-28 with 19/20 signatures (95%)
   ❌ Missing signature: SWSH06_Radiant_Charizard_Card (coverage gap)

🔧 Suggested Solutions:

Option 1: Enable Fallback Mode
   Command: [same filters] --allow-fallback
   Result: 95% coverage, 1,647 → 1,859 aligned records
   Trade-off: 212 gap-filled records, good quality overall

Option 2: Focus on SV Generation
   Command: --sets "SV*" --types "Card" --period "3M"
   Result: 100% coverage, 1,209 aligned records
   Trade-off: Excludes SWSH data, smaller dataset

Option 3: Focus on SWSH Generation
   Command: --sets "SWSH*" --types "Card" --period "3M"
   Result: ~85% coverage, ~500 aligned records
   Trade-off: Lower coverage, much smaller dataset

💡 Recommendation: Use Option 1 (fallback mode) for mixed analysis, or Option 2 for highest quality
```

### **3. `save`/`list`/`run` Commands - Configuration Management**

#### **Purpose**
Persistent storage and execution of successful filter configurations.

#### **Syntax**
```bash
# Save current configuration
python chart/alignment_workbench.py save --name CONFIG_NAME --sets PATTERN --types PATTERN [options]

# List saved configurations
python chart/alignment_workbench.py list [--detailed]

# Execute saved configuration
python chart/alignment_workbench.py run CONFIG_NAME [--output-name NAME] [options]
```

#### **Save Command Arguments**
```python
parser_save.add_argument('--name', required=True,
                        help='Configuration name (alphanumeric, underscores, hyphens)')
parser_save.add_argument('--sets', required=True,
                        help='Sets filter pattern to save')
parser_save.add_argument('--types', required=True,
                        help='Types filter pattern to save')
parser_save.add_argument('--period', default='3M',
                        help='Period filter to save (default: 3M)')
parser_save.add_argument('--description',
                        help='Optional description for this configuration')
parser_save.add_argument('--input-csv', default='data/output.csv',
                        help='Input CSV file for validation (default: data/output.csv)')
```

#### **List Command Arguments**
```python
parser_list.add_argument('--detailed', action='store_true',
                        help='Show detailed information including coverage stats')
```

#### **Run Command Arguments**
```python
parser_run.add_argument('config_name',
                       help='Name of saved configuration to execute')
parser_run.add_argument('--output-name',
                       help='Override output name (default: use config name)')
parser_run.add_argument('--input-csv', default='data/output.csv',
                       help='Input CSV file (default: data/output.csv)')
parser_run.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
```

#### **Save Command Output**
```bash
$ python chart/alignment_workbench.py save --name "sv_cards_complete" --sets "SV*" --types "Card" --description "Perfect SV card alignment for trend analysis"

✅ Validating configuration...
📊 Coverage test: 100% (13/13 signatures from 2025-04-28)
💾 Saved configuration: sv_cards_complete

Configuration Details:
├─ Sets: SV* → 14 sets (SV01 through SV10)
├─ Types: Card → Individual trading cards
├─ Period: 3M → 3-month price history
├─ Coverage: 100% perfect alignment
├─ Records: 1,209 aligned records expected
└─ Description: Perfect SV card alignment for trend analysis

💡 Use 'python chart/alignment_workbench.py run sv_cards_complete' to execute
```

#### **List Command Output**
```bash
$ python chart/alignment_workbench.py list

📋 Saved Configurations:

1. sv_cards_complete
   └─ SV* Cards, 100% coverage, 1,209 records

2. sv_boxes_mixed
   └─ SV* Boxes, 95% coverage, ~950 records

3. premium_collection
   └─ SV01,SV02,SV03 All types, 92% coverage, ~800 records

💡 Use --detailed for coverage statistics and descriptions
💡 Use 'run CONFIG_NAME' to execute a saved configuration
```

#### **List Detailed Output**
```bash
$ python chart/alignment_workbench.py list --detailed

📋 Saved Configurations (Detailed):

[1] sv_cards_complete
├─ Command: --sets "SV*" --types "Card" --period "3M"
├─ Coverage: 100% (13/13 signatures from 2025-04-28)
├─ Records: 1,209 aligned, 93 time series points
├─ Created: 2025-07-30 14:35:22
├─ Last used: Never
└─ Description: Perfect SV card alignment for trend analysis

[2] sv_boxes_mixed
├─ Command: --sets "SV*" --types "*Box" --period "3M"
├─ Coverage: 95% (estimated, needs validation)
├─ Records: ~950 aligned (estimated)
├─ Created: 2025-07-30 14:42:15
├─ Last used: 2025-07-30 14:45:33
└─ Description: (none)

💡 Coverage estimates refresh when configurations are executed
```

#### **Run Command Output**
```bash
$ python chart/alignment_workbench.py run sv_cards_complete --output-name "current_sv_cards"

🚀 Executing saved configuration: sv_cards_complete

📋 Configuration:
   Sets: SV* → ['SV01', 'SV02', 'SV03', 'SV03.5', 'SV04', 'SV04.5', 'SV05', 'SV06', 'SV06.5', 'SV07', 'SV08', 'SV08.5', 'SV09', 'SV10']
   Types: Card → ['Card']
   Period: 3M

📊 Execution Results:
   ✅ Alignment successful: 100% coverage (13/13 signatures)
   ✅ Time series generated: 93 data points
   ✅ Files created:
      • data/current_sv_cards_time_series_raw.csv (1,209 records)
      • data/current_sv_cards_time_series.csv (93 aggregated points)

🕐 Last used updated: 2025-07-30 14:48:15
```

## Integration with Existing Commands

### **Enhanced `index_aggregator.py` Integration**
Add `--config` flag to existing aggregator:

```bash
# New capability - use saved configuration
PYTHONPATH=. pipenv run python chart/index_aggregator.py --config sv_cards_complete --name analysis --verbose data/output.csv

# Equivalent to existing:
PYTHONPATH=. pipenv run python chart/index_aggregator.py --name analysis --sets "SV*" --types "Card" --period "3M" --verbose data/output.csv
```

### **Makefile Integration**
Add workbench targets to existing Makefile:

```makefile
# Interactive Alignment Workbench
discover:
	PYTHONPATH=. pipenv run python chart/alignment_workbench.py discover --verbose data/output.csv

analyze_sv_cards:
	PYTHONPATH=. pipenv run python chart/alignment_workbench.py analyze --sets "SV*" --types "Card" --suggest-alternatives data/output.csv

list_configs:
	PYTHONPATH=. pipenv run python chart/alignment_workbench.py list --detailed
```

## Technical Architecture Integration

### **Follows Existing Patterns**
- **Argument parsing**: Uses `argparse` like `index_aggregator.py`
- **CSV handling**: Leverages existing `FileHelper` and `IndexAggregator` classes
- **Logging**: Uses existing `AppLogger` singleton pattern
- **Filter validation**: Extends existing `FilterValidator` class methods

### **New Components Required**
- **`CoverageAnalyzer`**: Core analysis engine (separate deliverable #3)
- **`ConfigurationManager`**: JSON persistence handling (deliverable #4)
- **`RecommendationEngine`**: Smart filter suggestion logic

### **Zero Breaking Changes**
- All existing commands work unchanged
- New commands operate independently
- Shared components extended, not modified
- Backward compatibility maintained

This CLI specification provides a complete interactive alternative to the current trial-and-error workflow while maintaining full compatibility with existing tools and patterns.