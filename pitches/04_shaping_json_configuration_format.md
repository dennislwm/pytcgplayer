# JSON Configuration Persistence Format: Storage Specification

## Overview
The configuration persistence system enables users to save, manage, and reuse successful filter combinations through simple JSON storage. This specification follows existing `FileHelper` patterns and integrates seamlessly with the current data directory structure.

## Storage Architecture

### **File Location and Structure**
```
app/
├── data/
│   ├── output.csv                          # Input data (existing)
│   ├── *_time_series.csv                   # Generated outputs (existing)
│   └── workbench_configurations.json       # Configuration storage (new)
└── schema/
    └── workbench_config_v1.json            # Configuration schema (new)
```

### **Storage Pattern Integration**
- **Follows existing data/ directory convention** for user-generated files
- **Uses existing FileHelper JSON methods** for load/save operations
- **Schema validation** using existing `validate_csv_schema` pattern
- **Atomic writes** to prevent corruption during concurrent access

## JSON Configuration Format

### **Main Configuration File Structure**
```json
{
  "schema_version": "1.0",
  "created_at": "2025-07-30T14:35:22Z",
  "last_modified": "2025-07-30T14:45:33Z",
  "configurations": {
    "sv_cards_complete": {
      "name": "sv_cards_complete",
      "display_name": "SV Cards Complete",
      "description": "Perfect SV card alignment for trend analysis",
      "filters": {
        "sets": "SV*",
        "types": "Card",
        "period": "3M"
      },
      "validation_metadata": {
        "coverage_percentage": 1.0,
        "signatures_found": 13,
        "signatures_total": 13,
        "optimal_start_date": "2025-04-28",
        "records_aligned": 1209,
        "time_series_points": 93,
        "gap_fills_required": 50,
        "fallback_required": false,
        "quality_score": 1.0
      },
      "usage_statistics": {
        "created_at": "2025-07-30T14:35:22Z",
        "last_used": null,
        "use_count": 0,
        "last_validation": "2025-07-30T14:35:22Z"
      },
      "system_metadata": {
        "created_by_version": "workbench-v1.0",
        "dataset_fingerprint": "sha256:abc123...",
        "validation_dataset_size": 3688
      }
    },
    "sv_boxes_mixed": {
      "name": "sv_boxes_mixed",
      "display_name": "SV Boxes Mixed",
      "description": null,
      "filters": {
        "sets": "SV*",
        "types": "*Box",
        "period": "3M"
      },
      "validation_metadata": {
        "coverage_percentage": 0.95,
        "signatures_found": 12,
        "signatures_total": 13,
        "optimal_start_date": "2025-04-28",
        "records_aligned": 950,
        "time_series_points": 93,
        "gap_fills_required": 45,
        "fallback_required": false,
        "quality_score": 0.92
      },
      "usage_statistics": {
        "created_at": "2025-07-30T14:42:15Z",
        "last_used": "2025-07-30T14:45:33Z",
        "use_count": 2,
        "last_validation": "2025-07-30T14:42:15Z"
      },
      "system_metadata": {
        "created_by_version": "workbench-v1.0",
        "dataset_fingerprint": "sha256:abc123...",
        "validation_dataset_size": 3688
      }
    }
  }
}
```

### **Configuration Entry Schema**
```json
{
  "name": {
    "type": "string",
    "pattern": "^[a-zA-Z0-9_-]+$",
    "minLength": 1,
    "maxLength": 50,
    "description": "Unique configuration identifier"
  },
  "display_name": {
    "type": "string",
    "minLength": 1,
    "maxLength": 100,
    "description": "Human-readable name for display"
  },
  "description": {
    "type": ["string", "null"],
    "maxLength": 500,
    "description": "Optional user description"
  },
  "filters": {
    "type": "object",
    "required": ["sets", "types", "period"],
    "properties": {
      "sets": {
        "type": "string",
        "pattern": "^[A-Z0-9*.,\\s-]+$",
        "description": "Set filter pattern (e.g., 'SV*', 'SV01,SV02')"
      },
      "types": {
        "type": "string",
        "pattern": "^[A-Za-z0-9*.,\\s-]+$",
        "description": "Type filter pattern (e.g., '*Box', 'Card')"
      },
      "period": {
        "type": "string",
        "enum": ["3M"],
        "description": "Period filter (currently only 3M supported)"
      }
    }
  },
  "validation_metadata": {
    "type": "object",
    "description": "Coverage analysis results from configuration validation"
  },
  "usage_statistics": {
    "type": "object",
    "description": "Usage tracking for configuration management"
  },
  "system_metadata": {
    "type": "object",
    "description": "System-level metadata for version compatibility"
  }
}
```

## ConfigurationManager Class Interface

### **Class Definition**
```python
from typing import Dict, List, Optional, Tuple
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from common.helpers import FileHelper
from common.logger import AppLogger

@dataclass
class FilterConfiguration:
    """Configuration data structure matching JSON format"""
    name: str
    display_name: str
    description: Optional[str]
    filters: Dict[str, str]                    # sets, types, period
    validation_metadata: Dict[str, any]        # CoverageResult data
    usage_statistics: Dict[str, any]           # created_at, last_used, use_count
    system_metadata: Dict[str, any]            # version, fingerprint, dataset_size

class ConfigurationManager:
    """
    Manages persistent storage of filter configurations using JSON format.

    Provides CRUD operations for saved configurations with atomic writes,
    validation, and usage tracking following existing FileHelper patterns.
    """

    def __init__(self, config_file: Path = Path("data/workbench_configurations.json")):
        self.config_file = config_file
        self.schema_file = Path("schema/workbench_config_v1.json")
        self.logger = AppLogger.get_logger(__name__)
        self._ensure_config_file_exists()
```

### **Core CRUD Operations**

#### **1. Save Configuration**
```python
def save_configuration(
    self,
    name: str,
    display_name: str,
    filters: Dict[str, str],
    validation_metadata: Dict[str, any],
    description: Optional[str] = None
) -> bool:
    """
    Save a new configuration or update existing one.

    Args:
        name: Unique configuration identifier (alphanumeric, underscores, hyphens)
        display_name: Human-readable name for display
        filters: Filter configuration dict with sets, types, period
        validation_metadata: Coverage analysis results from CoverageAnalyzer
        description: Optional user description

    Returns:
        bool: True if save successful, False otherwise

    Example:
        success = manager.save_configuration(
            name="sv_cards_complete",
            display_name="SV Cards Complete",
            filters={"sets": "SV*", "types": "Card", "period": "3M"},
            validation_metadata=coverage_result.to_dict(),
            description="Perfect SV card alignment for trend analysis"
        )
    """
```

#### **2. Load Configuration**
```python
def load_configuration(self, name: str) -> Optional[FilterConfiguration]:
    """
    Load a specific configuration by name.

    Args:
        name: Configuration name to load

    Returns:
        FilterConfiguration object if found, None otherwise

    Example:
        config = manager.load_configuration("sv_cards_complete")
        if config:
            print(f"Filters: {config.filters}")
            print(f"Coverage: {config.validation_metadata['coverage_percentage']:.1%}")
    """
```

#### **3. List Configurations**
```python
def list_configurations(self, detailed: bool = False) -> List[FilterConfiguration]:
    """
    List all saved configurations.

    Args:
        detailed: Include full metadata if True, summary only if False

    Returns:
        List of FilterConfiguration objects sorted by last_used desc, then created_at desc

    Example:
        configs = manager.list_configurations(detailed=True)
        for config in configs:
            print(f"{config.name}: {config.validation_metadata['coverage_percentage']:.1%} coverage")
    """
```

#### **4. Delete Configuration**
```python
def delete_configuration(self, name: str) -> bool:
    """
    Delete a configuration by name.

    Args:
        name: Configuration name to delete

    Returns:
        bool: True if deletion successful, False if not found

    Example:
        deleted = manager.delete_configuration("old_config")
        if deleted:
            print("Configuration deleted successfully")
    """
```

### **Usage Tracking and Metadata**

#### **5. Update Usage Statistics**
```python
def update_usage_statistics(self, name: str) -> bool:
    """
    Update usage statistics when configuration is executed.

    Args:
        name: Configuration name to update

    Returns:
        bool: True if update successful, False if configuration not found

    Updates:
        - last_used: Current timestamp
        - use_count: Increment by 1

    Example:
        # Called automatically when 'run' command executes a configuration
        manager.update_usage_statistics("sv_cards_complete")
    """

def refresh_validation_metadata(
    self,
    name: str,
    new_validation_metadata: Dict[str, any]
) -> bool:
    """
    Update validation metadata with fresh coverage analysis results.

    Args:
        name: Configuration name to update
        new_validation_metadata: Fresh coverage analysis results

    Returns:
        bool: True if update successful, False if configuration not found

    Use Case:
        When dataset changes, refresh stored coverage estimates with actual results
    """
```

### **Validation and Data Integrity**

#### **6. Configuration Validation**
```python
def validate_configuration_name(self, name: str) -> Tuple[bool, List[str]]:
    """
    Validate configuration name format.

    Args:
        name: Configuration name to validate

    Returns:
        Tuple of (is_valid, error_messages)

    Rules:
        - Alphanumeric characters, underscores, hyphens only
        - 1-50 characters length
        - Must be unique among existing configurations
    """

def validate_filter_format(self, filters: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate filter configuration format.

    Args:
        filters: Filter dictionary to validate

    Returns:
        Tuple of (is_valid, error_messages)

    Validation:
        - Required keys: sets, types, period
        - Valid filter patterns using existing FilterValidator
        - Supported period values
    """

def _generate_dataset_fingerprint(self, dataset_path: Path) -> str:
    """
    Generate fingerprint for dataset integrity checking.

    Args:
        dataset_path: Path to dataset file

    Returns:
        SHA256 hash of dataset file for integrity verification
    """
```

### **File System Operations**

#### **7. Atomic File Operations**
```python
def _load_configurations_file(self) -> Dict[str, any]:
    """
    Load configurations from JSON file with error handling.

    Returns:
        Dictionary with configuration data structure, empty if file doesn't exist

    Error Handling:
        - FileNotFoundError: Return empty structure
        - JSONDecodeError: Log error and return empty structure
        - PermissionError: Log error and raise exception
    """

def _save_configurations_file(self, data: Dict[str, any]) -> bool:
    """
    Save configurations to JSON file atomically.

    Args:
        data: Configuration data structure to save

    Returns:
        bool: True if save successful, False otherwise

    Atomic Operation:
        1. Write to temporary file
        2. Validate JSON structure
        3. Rename temporary file to target (atomic on most filesystems)
        4. Update last_modified timestamp
    """

def _ensure_config_file_exists(self) -> None:
    """
    Ensure configuration file exists with proper structure.

    Creates empty configuration file with schema version if it doesn't exist.
    Creates data/ directory if it doesn't exist.
    """

def backup_configurations(self, backup_path: Optional[Path] = None) -> Path:
    """
    Create backup of current configurations.

    Args:
        backup_path: Optional custom backup location

    Returns:
        Path to created backup file

    Default backup location: data/workbench_configurations_backup_YYYYMMDD_HHMMSS.json
    """
```

## Integration with CLI Commands

### **Save Command Integration**
```python
# save command implementation
def handle_save_command(args):
    config_manager = ConfigurationManager()
    coverage_analyzer = CoverageAnalyzer(Path(args.input_csv))

    # Validate configuration name
    is_valid, errors = config_manager.validate_configuration_name(args.name)
    if not is_valid:
        print(f"❌ Invalid configuration name: {', '.join(errors)}")
        return

    # Validate filters
    filters = {"sets": args.sets, "types": args.types, "period": args.period}
    is_valid, errors = config_manager.validate_filter_format(filters)
    if not is_valid:
        print(f"❌ Invalid filter format: {', '.join(errors)}")
        return

    # Validate configuration against dataset
    print("✅ Validating configuration...")
    coverage_result = coverage_analyzer.analyze_filter_combination(
        args.sets, args.types, args.period
    )

    if coverage_result.coverage_percentage == 0:
        print("❌ Configuration validation failed - no alignment possible")
        return

    # Save configuration
    success = config_manager.save_configuration(
        name=args.name,
        display_name=args.name.replace('_', ' ').title(),
        filters=filters,
        validation_metadata=asdict(coverage_result),
        description=args.description
    )

    if success:
        print(f"💾 Saved configuration: {args.name}")
        print(f"📊 Coverage test: {coverage_result.coverage_percentage:.1%} ({coverage_result.signatures_found}/{coverage_result.signatures_total} signatures)")
    else:
        print("❌ Failed to save configuration")
```

### **List Command Integration**
```python
# list command implementation
def handle_list_command(args):
    config_manager = ConfigurationManager()
    configurations = config_manager.list_configurations(detailed=args.detailed)

    if not configurations:
        print("📋 No saved configurations found")
        print("💡 Use 'save' command to create your first configuration")
        return

    print("📋 Saved Configurations:")
    if args.detailed:
        print("\n📋 Saved Configurations (Detailed):\n")
        for i, config in enumerate(configurations, 1):
            print(f"[{i}] {config.name}")
            print(f"├─ Command: --sets \"{config.filters['sets']}\" --types \"{config.filters['types']}\" --period \"{config.filters['period']}\"")
            print(f"├─ Coverage: {config.validation_metadata['coverage_percentage']:.1%} ({config.validation_metadata['signatures_found']}/{config.validation_metadata['signatures_total']} signatures)")
            print(f"├─ Records: {config.validation_metadata['records_aligned']} aligned, {config.validation_metadata['time_series_points']} time series points")
            print(f"├─ Created: {config.usage_statistics['created_at']}")
            print(f"├─ Last used: {config.usage_statistics['last_used'] or 'Never'}")
            print(f"└─ Description: {config.description or '(none)'}\n")
    else:
        for i, config in enumerate(configurations, 1):
            coverage = config.validation_metadata['coverage_percentage']
            records = config.validation_metadata['records_aligned']
            print(f"{i}. {config.name}")
            print(f"   └─ {config.filters['sets']} {config.filters['types']}, {coverage:.0%} coverage, {records} records\n")

    print("💡 Use --detailed for coverage statistics and descriptions")
    print("💡 Use 'run CONFIG_NAME' to execute a saved configuration")
```

### **Run Command Integration**
```python
# run command implementation
def handle_run_command(args):
    config_manager = ConfigurationManager()
    config = config_manager.load_configuration(args.config_name)

    if not config:
        print(f"❌ Configuration '{args.config_name}' not found")
        print("💡 Use 'list' command to see available configurations")
        return

    print(f"🚀 Executing saved configuration: {args.config_name}")
    print(f"\n📋 Configuration:")
    print(f"   Sets: {config.filters['sets']}")
    print(f"   Types: {config.filters['types']}")
    print(f"   Period: {config.filters['period']}")

    # Execute using existing IndexAggregator
    aggregator = IndexAggregator()
    output_name = args.output_name or args.config_name

    # Run aggregation with saved filters
    subset_df = aggregator.create_subset(
        Path(args.input_csv),
        config.filters['sets'],
        config.filters['types'],
        config.filters['period']
    )

    if not subset_df.empty:
        # Generate time series
        ts_df = aggregator.aggregate_time_series(subset_df, output_name)

        # Save outputs
        data_dir = Path("data")
        raw_output = data_dir / f"{output_name}_time_series_raw.csv"
        ts_output = data_dir / f"{output_name}_time_series.csv"

        aggregator.write_csv(subset_df.sort_values(['period_end_date', 'set']), raw_output)
        aggregator.write_csv(ts_df, ts_output)

        print(f"\n📊 Execution Results:")
        print(f"   ✅ Alignment successful: {len(subset_df)} records processed")
        print(f"   ✅ Time series generated: {len(ts_df)} data points")
        print(f"   ✅ Files created:")
        print(f"      • {raw_output} ({len(subset_df)} records)")
        print(f"      • {ts_output} ({len(ts_df)} aggregated points)")

        # Update usage statistics
        config_manager.update_usage_statistics(args.config_name)
        print(f"\n🕐 Last used updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("\n❌ Execution failed: No data matches the configuration filters")
```

## Error Handling and Data Integrity

### **Concurrent Access Protection**
```python
import fcntl  # Unix/Linux file locking
import msvcrt  # Windows file locking

def _acquire_file_lock(self, file_handle):
    """Acquire exclusive file lock for atomic operations."""
    try:
        if os.name == 'nt':  # Windows
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:  # Unix/Linux
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (IOError, OSError):
        return False

def _release_file_lock(self, file_handle):
    """Release file lock after atomic operation."""
    try:
        if os.name == 'nt':  # Windows
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:  # Unix/Linux
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
    except (IOError, OSError):
        pass  # Lock may have been released already
```

### **Data Validation and Recovery**
```python
def validate_configuration_file(self) -> Tuple[bool, List[str]]:
    """
    Validate entire configuration file integrity.

    Returns:
        Tuple of (is_valid, error_messages)

    Validation:
        - JSON structure validity
        - Schema version compatibility
        - Required fields presence
        - Data type correctness
        - Configuration name uniqueness
    """

def repair_configuration_file(self, backup_path: Optional[Path] = None) -> bool:
    """
    Attempt to repair corrupted configuration file.

    Args:
        backup_path: Optional backup file to restore from

    Returns:
        bool: True if repair successful, False otherwise

    Recovery Strategy:
        1. Validate current file
        2. If corrupt, restore from most recent backup
        3. If no backup available, create new empty structure
        4. Log recovery actions for audit trail
    """
```

This JSON configuration persistence system provides robust, user-friendly storage for filter configurations while maintaining data integrity and following existing project patterns. The atomic file operations and validation ensure reliable operation even under concurrent access scenarios.