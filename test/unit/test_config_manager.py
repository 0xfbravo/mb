"""
Unit tests for ConfigManager class.

This module contains unit tests for the ConfigManager class, which is responsible
for managing configuration settings for the web3 service.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from app.utils.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    @pytest.fixture
    def sample_config(self):
        """Provide a sample configuration for testing."""
        return {
            "current_network": "TEST",
            "native_asset": "ETH",
            "networks": {
                "TEST": "test-url",
                "LOCAL": "http://localhost:8545",
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
                "ARBITRUM": "https://arbitrum-one-rpc.publicnode.com",
            },
            "assets": {
                "USDC": {
                    "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                },
                "USDT": {
                    "ETHEREUM": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "ARBITRUM": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                },
            },
        }

    @pytest.fixture
    def config_manager(self, sample_config):
        """Create a ConfigManager instance with mock config."""
        with patch("builtins.open", mock_open(read_data=yaml.dump(sample_config))):
            with patch("os.path.abspath", return_value="/fake/path"):
                with patch("os.path.dirname", side_effect=["/fake", "/fake/app", "/fake/app/utils"]):
                    return ConfigManager()

    def test_init_loads_config_file(self, sample_config):
        """Test that ConfigManager loads the config file correctly."""
        with patch("builtins.open", mock_open(read_data=yaml.dump(sample_config))):
            with patch("os.path.abspath", return_value="/fake/path"):
                with patch("os.path.dirname", side_effect=["/fake", "/fake/app", "/fake/app/utils"]):
                    config_manager = ConfigManager()
                    assert config_manager.config == sample_config

    def test_init_with_real_file_path(self, sample_config):
        """Test ConfigManager initialization with real file path calculation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp_file:
            yaml.dump(sample_config, temp_file)
            temp_file_path = temp_file.name

        try:
            with patch("os.path.join", return_value=temp_file_path):
                config_manager = ConfigManager()
                assert config_manager.config == sample_config
        finally:
            os.unlink(temp_file_path)

    def test_get_current_network(self, config_manager):
        """Test getting the current network."""
        assert config_manager.get_current_network() == "TEST"

    def test_get_networks(self, config_manager):
        """Test getting all networks."""
        networks = config_manager.get_networks()
        expected_networks = ["TEST", "LOCAL", "ETHEREUM", "ARBITRUM"]
        assert sorted(list(networks)) == sorted(expected_networks)

    def test_get_assets(self, config_manager):
        """Test getting all assets."""
        assets = config_manager.get_assets()
        expected_assets = ["USDC", "USDT"]
        assert list(assets) == expected_assets

    def test_get_native_asset(self, config_manager):
        """Test getting the native asset."""
        assert config_manager.get_native_asset() == "ETH"

    def test_get_rpc_url_valid_network(self, config_manager):
        """Test getting RPC URL for a valid network."""
        assert config_manager.get_rpc_url("TEST") == "test-url"
        assert config_manager.get_rpc_url("ETHEREUM") == "https://ethereum-rpc.publicnode.com"
        assert config_manager.get_rpc_url("ARBITRUM") == "https://arbitrum-one-rpc.publicnode.com"

    def test_get_rpc_url_invalid_network(self, config_manager):
        """Test getting RPC URL for an invalid network raises ValueError."""
        with pytest.raises(ValueError, match="Network INVALID not found in config"):
            config_manager.get_rpc_url("INVALID")

    def test_get_asset_valid_asset(self, config_manager):
        """Test getting asset config for a valid asset."""
        usdc_config = config_manager.get_asset("USDC")
        expected_usdc_config = {
            "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        }
        assert usdc_config == expected_usdc_config

        usdt_config = config_manager.get_asset("USDT")
        expected_usdt_config = {
            "ETHEREUM": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "ARBITRUM": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        }
        assert usdt_config == expected_usdt_config

    def test_get_asset_invalid_asset(self, config_manager):
        """Test getting asset config for an invalid asset raises ValueError."""
        with pytest.raises(ValueError, match="Asset INVALID not found in config"):
            config_manager.get_asset("INVALID")

    def test_config_file_not_found(self):
        """Test that ConfigManager raises FileNotFoundError when config file doesn't exist."""
        with patch("os.path.join", return_value="/nonexistent/config.yaml"):
            with pytest.raises(FileNotFoundError):
                ConfigManager()

    def test_invalid_yaml_config(self):
        """Test that ConfigManager handles invalid YAML gracefully."""
        invalid_yaml = "invalid: yaml: content: ["
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with patch("os.path.abspath", return_value="/fake/path"):
                with patch("os.path.dirname", side_effect=["/fake", "/fake/app", "/fake/app/utils"]):
                    with pytest.raises(yaml.YAMLError):
                        ConfigManager()

    def test_empty_config_file(self):
        """Test ConfigManager with empty config file."""
        empty_config = {}
        with patch("builtins.open", mock_open(read_data=yaml.dump(empty_config))):
            with patch("os.path.abspath", return_value="/fake/path"):
                with patch("os.path.dirname", side_effect=["/fake", "/fake/app", "/fake/app/utils"]):
                    config_manager = ConfigManager()
                    assert config_manager.config == empty_config

    def test_missing_required_config_keys(self):
        """Test ConfigManager behavior with missing required config keys."""
        incomplete_config = {
            "current_network": "TEST",
            # Missing other keys
        }
        with patch("builtins.open", mock_open(read_data=yaml.dump(incomplete_config))):
            with patch("os.path.abspath", return_value="/fake/path"):
                with patch("os.path.dirname", side_effect=["/fake", "/fake/app", "/fake/app/utils"]):
                    config_manager = ConfigManager()
                    # Should not raise error during initialization
                    assert config_manager.config == incomplete_config
                    # But accessing missing keys should raise KeyError
                    with pytest.raises(KeyError):
                        config_manager.get_networks()

    def test_networks_dict_keys_return_type(self, config_manager):
        """Test that get_networks returns a dict_keys object."""
        networks = config_manager.get_networks()
        assert hasattr(networks, "__iter__")
        assert sorted(list(networks)) == sorted(["TEST", "LOCAL", "ETHEREUM", "ARBITRUM"])

    def test_assets_dict_keys_return_type(self, config_manager):
        """Test that get_assets returns a dict_keys object."""
        assets = config_manager.get_assets()
        assert hasattr(assets, "__iter__")
        assert list(assets) == ["USDC", "USDT"]

    def test_get_rpc_url_case_sensitivity(self, config_manager):
        """Test that get_rpc_url is case sensitive."""
        # Should work with exact case
        assert config_manager.get_rpc_url("TEST") == "test-url"
        
        # Should fail with different case
        with pytest.raises(ValueError, match="Network test not found in config"):
            config_manager.get_rpc_url("test")

    def test_get_asset_case_sensitivity(self, config_manager):
        """Test that get_asset is case sensitive."""
        # Should work with exact case
        usdc_config = config_manager.get_asset("USDC")
        assert "ETHEREUM" in usdc_config
        
        # Should fail with different case
        with pytest.raises(ValueError, match="Asset usdc not found in config"):
            config_manager.get_asset("usdc")

    def test_config_manager_singleton_behavior(self, sample_config):
        """Test that each ConfigManager instance loads config independently."""
        with patch("builtins.open", mock_open(read_data=yaml.dump(sample_config))):
            with patch("os.path.abspath", return_value="/fake/path"):
                with patch("os.path.dirname", side_effect=["/fake", "/fake/app", "/fake/app/utils"]):
                    config_manager1 = ConfigManager()
                
                with patch("os.path.dirname", side_effect=["/fake", "/fake/app", "/fake/app/utils"]):
                    config_manager2 = ConfigManager()
                    
                    # Each instance should have its own config
                    assert config_manager1 is not config_manager2
                    assert config_manager1.config == config_manager2.config
                    
                    # Both should return the same data
                    assert config_manager1.get_current_network() == config_manager2.get_current_network()
                    assert sorted(list(config_manager1.get_networks())) == sorted(list(config_manager2.get_networks())) 