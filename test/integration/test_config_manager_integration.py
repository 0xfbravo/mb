"""
Integration tests for ConfigManager class.

This module contains integration tests for the ConfigManager class, testing
it with real files and actual configuration scenarios.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from app.utils.config_manager import ConfigManager


class TestConfigManagerIntegration:
    """Integration test cases for ConfigManager class."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            "current_network": "TEST",
            "native_asset": "ETH",
            "networks": {
                "TEST": "test-url",
                "LOCAL": "http://localhost:8545",
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
                "ARBITRUM": "https://arbitrum-one-rpc.publicnode.com",
                "BASE": "https://base-rpc.publicnode.com",
            },
            "assets": {
                "USDC": {
                    "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                    "BASE": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                },
                "USDT": {
                    "ETHEREUM": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                    "ARBITRUM": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                    "BASE": "0xfde4c96c8593536e31f229ea8f37b2ada2699bb2",
                },
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            yaml.dump(config_data, temp_file)
            temp_file_path = temp_file.name

        yield temp_file_path

        # Cleanup
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    @pytest.fixture
    def config_manager_with_temp_file(self, temp_config_file):
        """Create a ConfigManager instance using a temporary config file."""
        with patch_config_path(temp_config_file):
            return ConfigManager()

    def test_real_config_file_loading(self, temp_config_file):
        """Test ConfigManager loads a real config file correctly."""
        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()

            # Test basic configuration loading
            assert config_manager.get_current_network() == "TEST"
            assert config_manager.get_native_asset() == "ETH"

            # Test networks
            networks = list(config_manager.get_networks())
            expected_networks = ["TEST", "LOCAL", "ETHEREUM", "ARBITRUM", "BASE"]
            assert sorted(networks) == sorted(expected_networks)

            # Test assets
            assets = list(config_manager.get_assets())
            expected_assets = ["USDC", "USDT"]
            assert assets == expected_assets

    def test_real_rpc_url_retrieval(self, config_manager_with_temp_file):
        """Test getting RPC URLs from real config file."""
        config_manager = config_manager_with_temp_file

        # Test all networks
        assert config_manager.get_rpc_url("TEST") == "test-url"
        assert config_manager.get_rpc_url("LOCAL") == "http://localhost:8545"
        assert (
            config_manager.get_rpc_url("ETHEREUM")
            == "https://ethereum-rpc.publicnode.com"
        )
        assert (
            config_manager.get_rpc_url("ARBITRUM")
            == "https://arbitrum-one-rpc.publicnode.com"
        )
        assert config_manager.get_rpc_url("BASE") == "https://base-rpc.publicnode.com"

    def test_real_asset_config_retrieval(self, config_manager_with_temp_file):
        """Test getting asset configurations from real config file."""
        config_manager = config_manager_with_temp_file

        # Test USDC configuration
        usdc_config = config_manager.get_asset("USDC")
        expected_usdc_config = {
            "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "BASE": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        }
        assert usdc_config == expected_usdc_config

        # Test USDT configuration
        usdt_config = config_manager.get_asset("USDT")
        expected_usdt_config = {
            "ETHEREUM": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "ARBITRUM": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            "BASE": "0xfde4c96c8593536e31f229ea8f37b2ada2699bb2",
        }
        assert usdt_config == expected_usdt_config

    def test_error_handling_with_real_file(self, temp_config_file):
        """Test error handling with real config file."""
        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()

            # Test invalid network
            with pytest.raises(ValueError, match="Network INVALID not found in config"):
                config_manager.get_rpc_url("INVALID")

            # Test invalid asset
            with pytest.raises(ValueError, match="Asset INVALID not found in config"):
                config_manager.get_asset("INVALID")

    def test_config_file_modification(self, temp_config_file):
        """Test that ConfigManager reflects changes in the config file."""
        # Initial config
        initial_config = {
            "current_network": "TEST",
            "native_asset": "ETH",
            "networks": {"TEST": "test-url"},
            "assets": {"USDC": {"TEST": "0x123"}},
        }

        with open(temp_config_file, "w") as f:
            yaml.dump(initial_config, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()
            assert config_manager.get_current_network() == "TEST"
            assert list(config_manager.get_networks()) == ["TEST"]

        # Modify config file
        modified_config = {
            "current_network": "ETHEREUM",
            "native_asset": "ETH",
            "networks": {"ETHEREUM": "https://ethereum-rpc.publicnode.com"},
            "assets": {"USDT": {"ETHEREUM": "0x456"}},
        }

        with open(temp_config_file, "w") as f:
            yaml.dump(modified_config, f)

        # New instance should reflect changes
        with patch_config_path(temp_config_file):
            new_config_manager = ConfigManager()
            assert new_config_manager.get_current_network() == "ETHEREUM"
            assert list(new_config_manager.get_networks()) == ["ETHEREUM"]

    def test_large_config_file_performance(self, temp_config_file):
        """Test ConfigManager performance with a large config file."""
        # Create a large config with many networks and assets
        large_config = {
            "current_network": "ETHEREUM",
            "native_asset": "ETH",
            "networks": {
                f"NETWORK_{i}": f"https://network-{i}.example.com" for i in range(100)
            },
            "assets": {
                f"ASSET_{i}": {
                    f"NETWORK_{j}": f"0x{hex(i * 1000 + j)[2:].zfill(40)}"
                    for j in range(50)
                }
                for i in range(50)
            },
        }

        with open(temp_config_file, "w") as f:
            yaml.dump(large_config, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()

            # Test performance of getting all networks
            networks = list(config_manager.get_networks())
            assert len(networks) == 100

            # Test performance of getting all assets
            assets = list(config_manager.get_assets())
            assert len(assets) == 50

            # Test performance of getting specific asset
            asset_config = config_manager.get_asset("ASSET_25")
            assert len(asset_config) == 50

    def test_config_file_with_comments(self, temp_config_file):
        """Test ConfigManager handles YAML files with comments."""
        config_with_comments = """
# This is a comment
current_network: "TEST"  # Inline comment
native_asset: "ETH"

# Network configuration
networks:
  TEST: "test-url"  # Test network
  LOCAL: "http://localhost:8545"  # Local development
  ETHEREUM: "https://ethereum-rpc.publicnode.com"  # Mainnet

# Assets configuration
assets:
  USDC:  # USD Coin
    ETHEREUM: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    ARBITRUM: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
  USDT:  # Tether
    ETHEREUM: "0xdac17f958d2ee523a2206206994597c13d831ec7"
    ARBITRUM: "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
"""

        with open(temp_config_file, "w") as f:
            f.write(config_with_comments)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()

            assert config_manager.get_current_network() == "TEST"
            assert config_manager.get_native_asset() == "ETH"
            assert list(config_manager.get_networks()) == ["TEST", "LOCAL", "ETHEREUM"]
            assert list(config_manager.get_assets()) == ["USDC", "USDT"]

    def test_config_file_with_special_characters(self, temp_config_file):
        """Test ConfigManager handles config files with special characters."""
        config_with_special_chars = {
            "current_network": "TEST",
            "native_asset": "ETH",
            "networks": {
                "TEST": "https://test.example.com/path?param=value&other=123",
                "LOCAL": "http://localhost:8545",
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
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

        with open(temp_config_file, "w") as f:
            yaml.dump(config_with_special_chars, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()

            # Test URL with special characters
            assert (
                config_manager.get_rpc_url("TEST")
                == "https://test.example.com/path?param=value&other=123"
            )

            # Test other functionality still works
            assert config_manager.get_current_network() == "TEST"
            assert sorted(list(config_manager.get_networks())) == sorted(
                ["TEST", "LOCAL", "ETHEREUM"]
            )

    def test_config_file_permissions(self, temp_config_file):
        """Test ConfigManager handles different file permissions."""
        # Test with read-only file
        os.chmod(temp_config_file, 0o444)  # Read-only

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()
            assert config_manager.get_current_network() == "TEST"

        # Restore permissions
        os.chmod(temp_config_file, 0o644)

    def test_multiple_config_manager_instances(self, temp_config_file):
        """Test multiple ConfigManager instances work independently."""
        with patch_config_path(temp_config_file):
            config_manager1 = ConfigManager()
            config_manager2 = ConfigManager()

            # Both should work independently
            assert config_manager1 is not config_manager2
            assert config_manager1.config == config_manager2.config

            # Both should return the same data
            assert (
                config_manager1.get_current_network()
                == config_manager2.get_current_network()
            )
            assert list(config_manager1.get_networks()) == list(
                config_manager2.get_networks()
            )


def patch_config_path(config_path):
    """Context manager to patch the config file path for testing."""
    from unittest.mock import patch

    def mock_join(*args):
        if args[-1] == "config.yaml":
            return config_path
        return os.path.join(*args)

    return patch("os.path.join", side_effect=mock_join)
