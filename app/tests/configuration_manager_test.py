#!/usr/bin/env python3
"""
Unit tests for Configuration Manager functionality

Tests the ConfigurationManager class and related helper classes for the
Interactive Alignment Workbench configuration persistence system.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open

try:
    import pytest
except ImportError:
    pytest = None

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.configuration_manager import ConfigurationManager, FilterConfiguration
from common.helpers import JsonConfigHelper, ConfigurationFactory, ConfigurationManagerHelper, ConfigurationTestHelper
from common.logger import AppLogger


class TestFilterConfiguration:
    """Test cases for FilterConfiguration dataclass"""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_filter_configuration_creation(self):
        """Test FilterConfiguration dataclass creation with all fields"""
        config_data = ConfigurationTestHelper.create_test_config()
        config = FilterConfiguration(**config_data)
        
        ConfigurationTestHelper.assert_config_equality(
            config, "test_config", {"sets": "SV*", "types": "Card", "period": "3M"}, 
            {"coverage_percentage": 1.0}
        )


class TestJsonConfigHelper:
    """Test cases for JsonConfigHelper utility class"""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_load_json_config_existing_file(self, config_temp_file):
        """Test loading JSON config from existing file"""
        test_data = {"test": "data", "number": 123}
        config_temp_file.write_text(json.dumps(test_data))
        
        result = JsonConfigHelper.load_json_config(config_temp_file, lambda: {"default": "value"})
        assert result == test_data

    def test_load_json_config_nonexistent_file(self):
        """Test loading JSON config with nonexistent file uses default factory"""
        result = JsonConfigHelper.load_json_config(Path("/nonexistent/file.json"), lambda: {"default": "value"})
        assert result == {"default": "value"}

    def test_load_json_config_invalid_json(self, config_temp_file):
        """Test loading invalid JSON file uses default factory"""
        config_temp_file.write_text("invalid json content {")
        result = JsonConfigHelper.load_json_config(config_temp_file, lambda: {"default": "value"})
        assert result == {"default": "value"}

    def test_save_json_atomic_success(self, config_temp_file):
        """Test atomic JSON save creates file correctly"""
        test_data = {"test": "data", "nested": {"key": "value"}}
        assert JsonConfigHelper.save_json_atomic(config_temp_file, test_data)
        assert json.loads(config_temp_file.read_text()) == test_data

    def test_save_json_atomic_creates_directory(self, tmp_path):
        """Test atomic JSON save creates parent directories"""
        test_path = tmp_path / "subdir" / "test_config.json"
        assert JsonConfigHelper.save_json_atomic(test_path, {"test": "data"})
        assert test_path.exists() and test_path.parent.exists()


class TestConfigurationFactory:
    """Test cases for ConfigurationFactory utility class"""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_from_dict_creation(self, sample_filter_config):
        """Test FilterConfiguration creation from dictionary"""
        config_data = ConfigurationTestHelper.create_test_config(filters=sample_filter_config)
        config = ConfigurationFactory.from_dict(config_data)
        
        ConfigurationTestHelper.assert_config_equality(config, "test_config", sample_filter_config, {"coverage_percentage": 1.0})

    @patch('builtins.open', mock_open(read_data=b'test file content'))
    @patch('pathlib.Path.exists', return_value=True)
    def test_create_config_entry_new_configuration(self, _mock_exists, sample_filter_config, sample_validation_metadata):
        """Test creating new configuration entry"""
        entry = ConfigurationFactory.create_config_entry(
            name="test_config", display_name="Test Configuration", 
            filters=sample_filter_config, validation_metadata=sample_validation_metadata,
            description="Test description", updating_existing=False, existing_usage=None
        )
        
        assert all([
            entry["name"] == "test_config",
            entry["filters"] == sample_filter_config,
            entry["usage_statistics"]["use_count"] == 0,
            entry["usage_statistics"]["last_used"] is None
        ])

    def test_create_config_entry_updating_existing(self, sample_filter_config, sample_validation_metadata, existing_usage_stats):
        """Test updating existing configuration preserves usage statistics"""
        entry = ConfigurationFactory.create_config_entry(
            name="test_config", display_name="Updated Configuration",
            filters=sample_filter_config, validation_metadata=sample_validation_metadata,
            description="Updated description", updating_existing=True, existing_usage=existing_usage_stats
        )
        
        # Check that existing usage stats are preserved
        assert entry["usage_statistics"]["created_at"] == existing_usage_stats["created_at"]
        assert entry["usage_statistics"]["last_used"] == existing_usage_stats["last_used"]  
        assert entry["usage_statistics"]["use_count"] == existing_usage_stats["use_count"]
        # last_validation is added by the factory method, so check it exists
        assert "last_validation" in entry["usage_statistics"]


class TestConfigurationManagerHelper:
    """Test cases for ConfigurationManagerHelper utility class"""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_update_usage_stats_use_action(self):
        """Test updating usage statistics for 'use' action"""
        config = {"usage_statistics": {"created_at": "2025-07-29T10:00:00Z", "last_used": None, "use_count": 0}}
        updated = ConfigurationManagerHelper.update_usage_stats(config, "use")
        
        assert updated["usage_statistics"]["use_count"] == 1 and updated["usage_statistics"]["last_used"] is not None
        # Verify ISO timestamp format
        datetime.fromisoformat(updated["usage_statistics"]["last_used"].replace('Z', '+00:00'))

    def test_update_usage_stats_validate_action(self):
        """Test updating usage statistics for 'validate' action"""
        config = {"usage_statistics": {"created_at": "2025-07-29T10:00:00Z", "last_validation": "2025-07-29T10:00:00Z"}}
        updated = ConfigurationManagerHelper.update_usage_stats(config, "validate")
        
        assert "last_validation" in updated["usage_statistics"] and updated["usage_statistics"]["last_validation"] != "2025-07-29T10:00:00Z"

    def test_validate_and_log_success(self):
        """Test validation with successful result"""
        logger, validation_func = Mock(), lambda: (True, [])
        result = ConfigurationManagerHelper.validate_and_log("test_name", validation_func, logger)
        
        assert result is True and not logger.error.called

    def test_validate_and_log_failure(self):
        """Test validation with failure result logs errors"""
        logger, validation_func = Mock(), lambda: (False, ["Error 1", "Error 2"])
        result = ConfigurationManagerHelper.validate_and_log("test_name", validation_func, logger)
        
        assert result is False
        logger.error.assert_called_once_with("Validation failed for test_name: ['Error 1', 'Error 2']")


class TestConfigurationManager:
    """Test cases for ConfigurationManager class"""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Initialize logging for test class"""
        AppLogger.get_logger(__name__)

    def test_config_manager_initialization(self, config_manager, config_temp_file):
        """Test ConfigurationManager initializes and creates config file"""
        assert config_manager.config_file == config_temp_file
        assert config_temp_file.exists()
        
        # Use the ConfigurationManager's internal method to load data properly
        data = config_manager._load_configurations_file()
        assert "schema_version" in data
        assert "configurations" in data
        assert data["configurations"] == {}

    def test_save_configuration_new(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test saving new configuration"""
        success = config_manager.save_configuration(
            name="test_config", display_name="Test Configuration", 
            filters=sample_filter_config, validation_metadata=sample_validation_metadata, description="Test description"
        )
        
        assert success
        config = config_manager.load_configuration("test_config")
        ConfigurationTestHelper.assert_config_equality(config, "test_config", sample_filter_config)

    def test_save_configuration_update_existing(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test updating existing configuration preserves usage statistics"""
        # Create and use initial configuration
        config_manager.save_configuration("test_config", "Initial Configuration", sample_filter_config, sample_validation_metadata)
        config_manager.update_usage_statistics("test_config")

        # Update configuration
        updated_filters = {"sets": "SWSH*", "types": "Card", "period": "3M"}
        assert config_manager.save_configuration("test_config", "Updated Configuration", updated_filters, sample_validation_metadata, "Updated description")
        
        config = config_manager.load_configuration("test_config")
        ConfigurationTestHelper.assert_config_equality(config, "test_config", updated_filters)
        ConfigurationTestHelper.validate_usage_update(config, 1)

    def test_save_configuration_invalid_name(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test saving configuration with invalid name fails"""
        assert not config_manager.save_configuration("invalid name with spaces!", "Test Configuration", sample_filter_config, sample_validation_metadata)

    def test_save_configuration_invalid_filters(self, config_manager, sample_validation_metadata):
        """Test saving configuration with invalid filters fails"""
        assert not config_manager.save_configuration("test_config", "Test Configuration", {"sets": "SV*", "types": "Card"}, sample_validation_metadata)

    def test_load_configuration_existing(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test loading existing configuration"""
        config_manager.save_configuration("test_config", "Test Configuration", sample_filter_config, sample_validation_metadata)
        config = config_manager.load_configuration("test_config")
        
        assert isinstance(config, FilterConfiguration)
        ConfigurationTestHelper.assert_config_equality(config, "test_config", sample_filter_config)

    def test_load_configuration_nonexistent(self, config_manager):
        """Test loading nonexistent configuration returns None"""
        assert config_manager.load_configuration("nonexistent_config") is None

    def test_list_configurations_empty(self, config_manager):
        """Test listing configurations when none exist"""
        assert config_manager.list_configurations() == []

    def test_list_configurations_multiple(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test listing multiple configurations sorted by usage"""
        # Create and use configurations
        for name in ["config_1", "config_2"]:
            config_manager.save_configuration(name, f"Config {name[-1]}", sample_filter_config, sample_validation_metadata)
        config_manager.update_usage_statistics("config_2")

        configs = config_manager.list_configurations()
        assert len(configs) == 2 and configs[0].name == "config_2" and configs[1].name == "config_1"

    def test_delete_configuration_existing(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test deleting existing configuration"""
        config_manager.save_configuration("test_config", "Test Configuration", sample_filter_config, sample_validation_metadata)
        assert config_manager.delete_configuration("test_config") and config_manager.load_configuration("test_config") is None

    def test_delete_configuration_nonexistent(self, config_manager):
        """Test deleting nonexistent configuration returns False"""
        assert not config_manager.delete_configuration("nonexistent_config")

    def test_update_usage_statistics_existing(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test updating usage statistics for existing configuration"""
        config_manager.save_configuration("test_config", "Test Configuration", sample_filter_config, sample_validation_metadata)
        assert config_manager.update_usage_statistics("test_config")
        
        config = config_manager.load_configuration("test_config")
        ConfigurationTestHelper.validate_usage_update(config, 1)

    def test_update_usage_statistics_nonexistent(self, config_manager):
        """Test updating usage statistics for nonexistent configuration"""
        assert not config_manager.update_usage_statistics("nonexistent_config")

    def test_refresh_validation_metadata(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test refreshing validation metadata for existing configuration"""
        config_manager.save_configuration("test_config", "Test Configuration", sample_filter_config, sample_validation_metadata)
        
        new_metadata = {"coverage_percentage": 0.95, "signatures_found": 12}
        assert config_manager.refresh_validation_metadata("test_config", new_metadata)
        
        config = config_manager.load_configuration("test_config")
        assert config.validation_metadata["coverage_percentage"] == 0.95 and config.validation_metadata["signatures_found"] == 12

    def test_validate_configuration_name_valid(self, config_manager):
        """Test validating valid configuration names"""
        valid_names = ["valid_name", "valid-name", "validname123", "a"]
        assert all(config_manager.validate_configuration_name(name)[0] for name in valid_names)

    def test_validate_configuration_name_invalid(self, config_manager):
        """Test validating invalid configuration names"""
        invalid_names = ["invalid name", "invalid@name", "", "a" * 51]
        assert all(not config_manager.validate_configuration_name(name)[0] for name in invalid_names)

    def test_validate_filter_format_valid(self, config_manager):
        """Test validating valid filter formats"""
        valid_filters = [
            {"sets": "SV*", "types": "Card", "period": "3M"},
            {"sets": "SV01,SV02", "types": "*Box", "period": "3M"},
            {"sets": "*", "types": "*", "period": "3M"}
        ]
        assert all(config_manager.validate_filter_format(filters)[0] for filters in valid_filters)

    def test_validate_filter_format_invalid(self, config_manager):
        """Test validating invalid filter formats"""
        invalid_filters = [
            {"sets": "SV*", "types": "Card"},  # Missing period
            {"sets": "SV*", "period": "3M"},   # Missing types
            {"types": "Card", "period": "3M"},  # Missing sets
            {"sets": "SV*", "types": "Card", "period": "1Y"}  # Invalid period
        ]
        assert all(not config_manager.validate_filter_format(filters)[0] for filters in invalid_filters)

    def test_backup_configurations(self, config_manager, sample_filter_config, sample_validation_metadata):
        """Test creating backup of configurations"""
        config_manager.save_configuration("config_1", "Config 1", sample_filter_config, sample_validation_metadata)
        backup_path = config_manager.backup_configurations()
        
        assert backup_path.exists() and "workbench_configurations_backup_" in backup_path.name
        backup_data = JsonConfigHelper.load_json_config(backup_path, dict)
        assert "config_1" in backup_data.get("configurations", {})
        
        backup_path.unlink()  # Clean up

    def test_resilient_operation_decorator_error_handling(self, config_manager):
        """Test that resilient operation decorator handles errors properly"""
        config_manager.config_file = Path("/")  # Force error with directory path
        
        assert config_manager.load_configuration("test") is None and not config_manager.delete_configuration("test")