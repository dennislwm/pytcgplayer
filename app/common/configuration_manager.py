#\!/usr/bin/env python3
"""
Configuration Manager for Interactive Alignment Workbench

Manages persistent storage of filter configurations using JSON format with atomic writes,
validation, and usage tracking following existing FileHelper patterns.
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from common.helpers import (JsonConfigHelper, ConfigurationFactory, ConfigurationManagerHelper, 
                           FilterValidationHelper, resilient_config_operation)
from common.logger import AppLogger


@dataclass
class FilterConfiguration:
    """Configuration data structure matching JSON format"""
    name: str
    display_name: str
    description: Optional[str]
    filters: Dict[str, str]                    # sets, types, period
    validation_metadata: Dict[str, Any]        # CoverageResult data
    usage_statistics: Dict[str, Any]           # created_at, last_used, use_count
    system_metadata: Dict[str, Any]            # version, fingerprint, dataset_size


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
    
    @resilient_config_operation("save configuration")
    def save_configuration(
        self,
        name: str,
        display_name: str,
        filters: Dict[str, str],
        validation_metadata: Dict[str, Any],
        description: Optional[str] = None
    ) -> bool:
        """Save a new configuration or update existing one."""
        # Validate inputs
        if not ConfigurationManagerHelper.validate_and_log(name, lambda: self.validate_configuration_name(name), self.logger):
            return False
        if not ConfigurationManagerHelper.validate_and_log("filters", lambda: self.validate_filter_format(filters), self.logger):
            return False
        
        # Load, create entry, save atomically
        data = self._load_configurations_file()
        updating_existing = name in data["configurations"]
        existing_usage = data["configurations"][name]["usage_statistics"] if updating_existing else None
        
        data["configurations"][name] = ConfigurationFactory.create_config_entry(
            name, display_name, filters, validation_metadata, description, updating_existing, existing_usage)
        data["last_modified"] = datetime.now(timezone.utc).isoformat()
        
        success = self._save_configurations_file(data)
        if success:
            self.logger.info(f"{'Updated' if updating_existing else 'Saved'} configuration: {name}")
        return success
    
    @resilient_config_operation("load configuration")
    def load_configuration(self, name: str) -> Optional[FilterConfiguration]:
        """Load a specific configuration by name."""
        data = self._load_configurations_file()
        return ConfigurationFactory.from_dict(data["configurations"][name]) if name in data["configurations"] else None
    
    @resilient_config_operation("list configurations")
    def list_configurations(self, detailed: bool = False) -> List[FilterConfiguration]:
        """List all saved configurations sorted by usage."""
        data = self._load_configurations_file()
        configs = [ConfigurationFactory.from_dict(config) for config in data["configurations"].values()]
        return sorted(configs, key=lambda c: (c.usage_statistics.get("last_used") or "", c.usage_statistics.get("created_at", "")), reverse=True)
    
    @resilient_config_operation("delete configuration")
    def delete_configuration(self, name: str) -> bool:
        """Delete a configuration by name."""
        data = self._load_configurations_file()
        if name not in data["configurations"]:
            return False
        
        del data["configurations"][name]
        data["last_modified"] = datetime.now(timezone.utc).isoformat()
        
        success = self._save_configurations_file(data)
        if success:
            self.logger.info(f"Deleted configuration: {name}")
        return success
    
    @resilient_config_operation("update usage statistics")
    def update_usage_statistics(self, name: str) -> bool:
        """Update usage statistics when configuration is executed."""
        data = self._load_configurations_file()
        if name not in data["configurations"]:
            return False
        
        ConfigurationManagerHelper.update_usage_stats(data["configurations"][name], "use")
        data["last_modified"] = datetime.now(timezone.utc).isoformat()
        
        success = self._save_configurations_file(data)
        if success:
            self.logger.info(f"Updated usage statistics for: {name}")
        return success
    
    @resilient_config_operation("refresh validation metadata")
    def refresh_validation_metadata(self, name: str, new_validation_metadata: Dict[str, Any]) -> bool:
        """Update validation metadata with fresh coverage analysis results."""
        data = self._load_configurations_file()
        if name not in data["configurations"]:
            return False
        
        config = data["configurations"][name]
        config["validation_metadata"] = new_validation_metadata
        ConfigurationManagerHelper.update_usage_stats(config, "validate")
        data["last_modified"] = datetime.now(timezone.utc).isoformat()
        
        success = self._save_configurations_file(data)
        if success:
            self.logger.info(f"Refreshed validation metadata for: {name}")
        return success
    
    def validate_configuration_name(self, name: str) -> Tuple[bool, List[str]]:
        """
        Validate configuration name format.
        
        Args:
            name: Configuration name to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check format: alphanumeric, underscores, hyphens only
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            errors.append("Name must contain only letters, numbers, underscores, and hyphens")
        
        # Check length
        if len(name) < 1 or len(name) > 50:
            errors.append("Name must be 1-50 characters long")
        
        # Check uniqueness (only for new configurations)
        data = self._load_configurations_file()
        if name in data["configurations"]:
            # For existing configurations, this is not an error (allows updates)
            pass
        
        return len(errors) == 0, errors
    
    def validate_filter_format(self, filters: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate filter configuration format."""
        errors = []
        
        # Check required keys
        missing_keys = {"sets", "types", "period"} - set(filters.keys())
        if missing_keys: errors.append(f"Missing required filter keys: {list(missing_keys)}")
        
        # Validate filter patterns and period
        if "sets" in filters and "types" in filters and not FilterValidationHelper.is_valid_filter_combination(filters["sets"], filters["types"]):
            errors.append("Invalid sets or types filter pattern")
        if "period" in filters and filters["period"] not in ["3M"]:
            errors.append("Period must be one of: 3M")
        
        return len(errors) == 0, errors
    
    def _load_configurations_file(self) -> Dict[str, Any]:
        """Load configurations from JSON file with error handling."""
        data = JsonConfigHelper.load_json_config(self.config_file, self._create_empty_config_structure)
        data.setdefault("configurations", {})
        return data
    
    def _save_configurations_file(self, data: Dict[str, Any]) -> bool:
        """Save configurations to JSON file atomically."""
        return JsonConfigHelper.save_json_atomic(self.config_file, data)
    
    def _ensure_config_file_exists(self) -> None:
        """Ensure configuration file exists with proper structure."""
        if not self.config_file.exists():
            self._save_configurations_file(self._create_empty_config_structure())
            self.logger.info(f"Created new configuration file: {self.config_file}")
    
    def _create_empty_config_structure(self) -> Dict[str, Any]:
        """Create empty configuration file structure"""
        now = datetime.now(timezone.utc).isoformat()
        return {"schema_version": "1.0", "created_at": now, "last_modified": now, "configurations": {}}
    
    def backup_configurations(self, backup_path: Optional[Path] = None) -> Path:
        """Create backup of current configurations."""
        backup_path = backup_path or Path(f"data/workbench_configurations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        JsonConfigHelper.save_json_atomic(backup_path, self._load_configurations_file())
        self.logger.info(f"Created configuration backup: {backup_path}")
        return backup_path

