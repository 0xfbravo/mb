"""
Integration tests for AssetsUseCases class.

This module contains integration tests for the AssetsUseCases class, testing
it with real ConfigManager instances and actual configuration scenarios.
"""

import os
import tempfile
from unittest.mock import MagicMock

import pytest
import yaml

from app.domain.assets_use_cases import AssetsUseCases
from app.domain.errors import AssetNotFoundError
from app.utils.config_manager import ConfigManager


class TestAssetsUseCasesIntegration:
    """Integration test cases for AssetsUseCases class."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            "current_network": "ETHEREUM",
            "native_asset": "ETH",
            "networks": {
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
                "ARBITRUM": "https://arbitrum-one-rpc.publicnode.com",
                "BASE": "https://base-rpc.publicnode.com",
                "TEST": "test-url",
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
                "WETH": {
                    "ETHEREUM": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "ARBITRUM": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
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

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = MagicMock()
        logger.info = MagicMock()
        logger.error = MagicMock()
        return logger

    @pytest.fixture
    def assets_use_cases_integration(self, config_manager_with_temp_file, mock_logger):
        """Create an AssetsUseCases instance with real ConfigManager."""
        return AssetsUseCases(config_manager_with_temp_file, mock_logger)

    def test_real_config_manager_integration(
        self, assets_use_cases_integration, mock_logger
    ):
        """Test AssetsUseCases with real ConfigManager integration."""
        # Test get_native_asset
        native_asset = assets_use_cases_integration.get_native_asset()
        assert native_asset == "ETH"
        mock_logger.info.assert_any_call("Getting native asset")

        # Test get_all_assets
        all_assets = assets_use_cases_integration.get_all_assets()
        expected_assets = ["USDC", "USDT", "WETH"]
        assert sorted(all_assets) == sorted(expected_assets)
        mock_logger.info.assert_any_call("Getting all assets")

        # Test is_native_asset
        assert assets_use_cases_integration.is_native_asset("ETH") is True
        assert assets_use_cases_integration.is_native_asset("USDC") is False

        # Test get_asset
        usdc_config = assets_use_cases_integration.get_asset("USDC")
        expected_usdc_config = {
            "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "BASE": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        }
        assert usdc_config == expected_usdc_config

        # Test get_asset_address
        usdc_address = assets_use_cases_integration.get_asset_address("USDC")
        assert str(usdc_address) == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

    def test_asset_address_retrieval_all_networks(
        self, assets_use_cases_integration, mock_logger
    ):
        """Test get_asset_address for all assets on current network."""
        # Current network is ETHEREUM
        usdc_address = assets_use_cases_integration.get_asset_address("USDC")
        assert str(usdc_address) == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

        usdt_address = assets_use_cases_integration.get_asset_address("USDT")
        assert str(usdt_address) == "0xdac17f958d2ee523a2206206994597c13d831ec7"

        weth_address = assets_use_cases_integration.get_asset_address("WETH")
        assert str(weth_address) == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

    def test_asset_configuration_retrieval(
        self, assets_use_cases_integration, mock_logger
    ):
        """Test get_asset returns complete configuration for all assets."""
        # Test USDC configuration
        usdc_config = assets_use_cases_integration.get_asset("USDC")
        assert "ETHEREUM" in usdc_config
        assert "ARBITRUM" in usdc_config
        assert "BASE" in usdc_config
        assert len(usdc_config) == 3

        # Test USDT configuration
        usdt_config = assets_use_cases_integration.get_asset("USDT")
        assert "ETHEREUM" in usdt_config
        assert "ARBITRUM" in usdt_config
        assert "BASE" in usdt_config
        assert len(usdt_config) == 3

        # Test WETH configuration (only 2 networks)
        weth_config = assets_use_cases_integration.get_asset("WETH")
        assert "ETHEREUM" in weth_config
        assert "ARBITRUM" in weth_config
        assert "BASE" not in weth_config
        assert len(weth_config) == 2

    def test_native_asset_identification(
        self, assets_use_cases_integration, mock_logger
    ):
        """Test is_native_asset correctly identifies native and non-native assets."""
        # Test native asset
        assert assets_use_cases_integration.is_native_asset("ETH") is True

        # Test non-native assets
        assert assets_use_cases_integration.is_native_asset("USDC") is False
        assert assets_use_cases_integration.is_native_asset("USDT") is False
        assert assets_use_cases_integration.is_native_asset("WETH") is False

        # Test case sensitivity
        assert assets_use_cases_integration.is_native_asset("eth") is False

    def test_error_handling_invalid_asset(
        self, assets_use_cases_integration, mock_logger
    ):
        """Test error handling for invalid assets."""
        # Test get_asset with invalid asset
        with pytest.raises(AssetNotFoundError) as exc_info:
            assets_use_cases_integration.get_asset("INVALID_ASSET")

        assert (
            str(exc_info.value)
            == "Asset 'INVALID_ASSET' not found on network 'ETHEREUM'"
        )
        mock_logger.error.assert_called()

        # Test get_asset_address with invalid asset
        with pytest.raises(AssetNotFoundError) as exc_info:
            assets_use_cases_integration.get_asset_address("INVALID_ASSET")

        assert (
            str(exc_info.value)
            == "Asset 'INVALID_ASSET' not found on network 'ETHEREUM'"
        )

    def test_network_switching_scenario(self, temp_config_file):
        """Test AssetsUseCases behavior when network configuration changes."""
        # Create initial config with ETHEREUM as current network
        initial_config = {
            "current_network": "ETHEREUM",
            "native_asset": "ETH",
            "networks": {
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
                "ARBITRUM": "https://arbitrum-one-rpc.publicnode.com",
            },
            "assets": {
                "USDC": {
                    "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
                },
            },
        }

        with open(temp_config_file, "w") as f:
            yaml.dump(initial_config, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()
            logger = MagicMock()
            assets_use_cases = AssetsUseCases(config_manager, logger)

            # Test with ETHEREUM network
            assert (
                assets_use_cases.get_asset_address("USDC")
                == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
            )

        # Switch to ARBITRUM network
        initial_config["current_network"] = "ARBITRUM"
        with open(temp_config_file, "w") as f:
            yaml.dump(initial_config, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()
            logger = MagicMock()
            assets_use_cases = AssetsUseCases(config_manager, logger)

            # Test with ARBITRUM network
            assert (
                assets_use_cases.get_asset_address("USDC")
                == "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
            )

    def test_large_asset_configuration(self, temp_config_file):
        """Test AssetsUseCases with a large number of assets."""
        # Create config with many assets
        large_config = {
            "current_network": "ETHEREUM",
            "native_asset": "ETH",
            "networks": {
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
                "ARBITRUM": "https://arbitrum-one-rpc.publicnode.com",
            },
            "assets": {
                f"ASSET_{i}": {
                    "ETHEREUM": f"0x{hex(i * 1000)[2:].zfill(40)}",
                    "ARBITRUM": f"0x{hex(i * 2000)[2:].zfill(40)}",
                }
                for i in range(1, 101)  # 100 assets
            },
        }

        with open(temp_config_file, "w") as f:
            yaml.dump(large_config, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()
            logger = MagicMock()
            assets_use_cases = AssetsUseCases(config_manager, logger)

            # Test getting all assets
            all_assets = assets_use_cases.get_all_assets()
            assert len(all_assets) == 100

            # Test getting specific asset
            asset_50_config = assets_use_cases.get_asset("ASSET_50")
            assert "ETHEREUM" in asset_50_config
            assert "ARBITRUM" in asset_50_config

            # Test getting asset address
            asset_50_address = assets_use_cases.get_asset_address("ASSET_50")
            expected_address = f"0x{hex(50 * 1000)[2:].zfill(40)}"
            assert str(asset_50_address) == expected_address

    def test_empty_asset_configuration(self, temp_config_file):
        """Test AssetsUseCases with empty asset configuration."""
        empty_config = {
            "current_network": "ETHEREUM",
            "native_asset": "ETH",
            "networks": {
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
            },
            "assets": {},
        }

        with open(temp_config_file, "w") as f:
            yaml.dump(empty_config, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()
            logger = MagicMock()
            assets_use_cases = AssetsUseCases(config_manager, logger)

            # Test getting all assets
            all_assets = assets_use_cases.get_all_assets()
            assert all_assets == []

            # Test getting native asset
            native_asset = assets_use_cases.get_native_asset()
            assert native_asset == "ETH"

            # Test is_native_asset
            assert assets_use_cases.is_native_asset("ETH") is True

    def test_malformed_asset_addresses(self, temp_config_file):
        """Test AssetsUseCases behavior with malformed asset addresses."""
        malformed_config = {
            "current_network": "ETHEREUM",
            "native_asset": "ETH",
            "networks": {
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
            },
            "assets": {
                "MALFORMED_ASSET": {
                    "ETHEREUM": "invalid_hex_address",
                },
            },
        }

        with open(temp_config_file, "w") as f:
            yaml.dump(malformed_config, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()
            logger = MagicMock()
            assets_use_cases = AssetsUseCases(config_manager, logger)

            # Test get_asset_address with malformed address
            with pytest.raises(AssetNotFoundError) as exc_info:
                assets_use_cases.get_asset_address("MALFORMED_ASSET")

            assert (
                str(exc_info.value)
                == "Asset 'MALFORMED_ASSET' not found on network 'ETHEREUM'"
            )

    def test_logging_integration(self, assets_use_cases_integration, mock_logger):
        """Test that logging works correctly in integration scenarios."""
        # Perform various operations
        assets_use_cases_integration.get_native_asset()
        assets_use_cases_integration.get_all_assets()
        assets_use_cases_integration.is_native_asset("ETH")
        assets_use_cases_integration.get_asset("USDC")
        assets_use_cases_integration.get_asset_address("USDC")

        # Verify logging calls were made
        assert mock_logger.info.call_count >= 5
        assert mock_logger.error.call_count == 0

        # Test error logging
        with pytest.raises(AssetNotFoundError):
            assets_use_cases_integration.get_asset("INVALID")

        assert mock_logger.error.call_count >= 1

    def test_config_manager_error_propagation(self, temp_config_file):
        """Test that ConfigManager errors are properly propagated."""
        # Create a config file that will cause ConfigManager to fail
        invalid_config = "invalid: yaml: content: ["

        with open(temp_config_file, "w") as f:
            f.write(invalid_config)

        # This should raise a YAMLError when ConfigManager tries to load it
        with patch_config_path(temp_config_file):
            with pytest.raises(Exception):  # ConfigManager will fail
                config_manager = ConfigManager()
                logger = MagicMock()
                _ = AssetsUseCases(config_manager, logger)

    def test_asset_address_case_sensitivity(
        self, assets_use_cases_integration, mock_logger
    ):
        """Test that asset addresses are handled case-sensitively."""
        # Test with exact case
        usdc_address = assets_use_cases_integration.get_asset_address("USDC")
        assert str(usdc_address) == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

        # Test with different case should fail
        with pytest.raises(AssetNotFoundError) as exc_info:
            assets_use_cases_integration.get_asset_address("usdc")

        assert str(exc_info.value) == "Asset 'usdc' not found on network 'ETHEREUM'"

    def test_network_specific_asset_availability(self, temp_config_file):
        """Test that assets are only available on configured networks."""
        network_specific_config = {
            "current_network": "ETHEREUM",
            "native_asset": "ETH",
            "networks": {
                "ETHEREUM": "https://ethereum-rpc.publicnode.com",
                "ARBITRUM": "https://arbitrum-one-rpc.publicnode.com",
            },
            "assets": {
                "ETHEREUM_ONLY": {
                    "ETHEREUM": "0x1234567890abcdef1234567890abcdef12345678",
                },
                "ARBITRUM_ONLY": {
                    "ARBITRUM": "0xfedcba0987654321fedcba0987654321fedcba09",
                },
            },
        }

        with open(temp_config_file, "w") as f:
            yaml.dump(network_specific_config, f)

        with patch_config_path(temp_config_file):
            config_manager = ConfigManager()
            logger = MagicMock()
            assets_use_cases = AssetsUseCases(config_manager, logger)

            # ETHEREUM_ONLY should work on ETHEREUM
            ethereum_address = assets_use_cases.get_asset_address("ETHEREUM_ONLY")
            assert str(ethereum_address) == "0x1234567890abcdef1234567890abcdef12345678"

            # ARBITRUM_ONLY should fail on ETHEREUM
            with pytest.raises(AssetNotFoundError) as exc_info:
                assets_use_cases.get_asset_address("ARBITRUM_ONLY")

            assert (
                str(exc_info.value)
                == "Asset 'ARBITRUM_ONLY' not found on network 'ETHEREUM'"
            )


def patch_config_path(config_path):
    """Patch the config path to use the temporary file."""
    import os
    from unittest.mock import patch

    def mock_join(*args):
        if args[-1] == "config.yaml":
            return config_path
        return os.path.join(*args)

    return patch("os.path.join", side_effect=mock_join)
