"""
Unit tests for AssetsUseCases class.

This module contains unit tests for the AssetsUseCases class, which is responsible
for handling asset-related business logic.
"""

from unittest.mock import MagicMock, patch

import pytest
from eth_typing import HexAddress

from app.domain.assets_use_cases import AssetsUseCases
from app.domain.errors import AssetNotFoundError, InvalidNetworkError
from app.utils.config_manager import ConfigManager


class TestAssetsUseCases:
    """Test cases for AssetsUseCases class."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock ConfigManager for testing."""
        config_manager = MagicMock(spec=ConfigManager)
        config_manager.get_current_network.return_value = "ETHEREUM"
        config_manager.get_native_asset.return_value = "ETH"
        config_manager.get_assets.return_value = ["ETH", "USDC", "USDT"]
        config_manager.get_asset.return_value = {
            "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        }
        return config_manager

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = MagicMock()
        logger.info = MagicMock()
        logger.error = MagicMock()
        return logger

    @pytest.fixture
    def assets_use_cases(self, mock_config_manager, mock_logger):
        """Create an AssetsUseCases instance with mocked dependencies."""
        return AssetsUseCases(mock_config_manager, mock_logger)

    def test_init(self, mock_config_manager, mock_logger):
        """Test AssetsUseCases initialization."""
        assets_use_cases = AssetsUseCases(mock_config_manager, mock_logger)
        assert assets_use_cases._config_manager == mock_config_manager
        assert assets_use_cases._logger == mock_logger

    def test_is_native_asset_true(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test is_native_asset returns True for native asset."""
        # Arrange
        asset = "ETH"
        mock_config_manager.get_native_asset.return_value = "ETH"
        mock_config_manager.get_current_network.return_value = "ETHEREUM"

        # Act
        result = assets_use_cases.is_native_asset(asset)

        # Assert
        assert result is True
        mock_logger.info.assert_any_call(
            f"Checking if asset {asset} is the native asset"
        )
        mock_logger.info.assert_any_call(f"Native asset: ETH for networkETHEREUM")
        mock_config_manager.get_native_asset.assert_called_once()
        mock_config_manager.get_current_network.assert_called_once()

    def test_is_native_asset_false(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test is_native_asset returns False for non-native asset."""
        # Arrange
        asset = "USDC"
        mock_config_manager.get_native_asset.return_value = "ETH"
        mock_config_manager.get_current_network.return_value = "ETHEREUM"

        # Act
        result = assets_use_cases.is_native_asset(asset)

        # Assert
        assert result is False
        mock_logger.info.assert_any_call(
            f"Checking if asset {asset} is the native asset"
        )
        mock_logger.info.assert_any_call(f"Native asset: ETH for networkETHEREUM")
        mock_config_manager.get_native_asset.assert_called_once()

    def test_is_native_asset_config_manager_exception(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test is_native_asset raises InvalidNetworkError when config_manager fails."""
        # Arrange
        asset = "ETH"
        mock_config_manager.get_native_asset.side_effect = Exception("Config error")
        mock_config_manager.get_current_network.return_value = "ETHEREUM"

        # Act & Assert
        with pytest.raises(InvalidNetworkError) as exc_info:
            assets_use_cases.is_native_asset(asset)

        assert str(exc_info.value) == "Network ETHEREUM not available"
        mock_logger.error.assert_called_with(
            f"Error checking if asset {asset} is the native asset: Config error"
        )

    def test_get_native_asset_success(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_native_asset returns the native asset successfully."""
        # Arrange
        mock_config_manager.get_native_asset.return_value = "ETH"
        mock_config_manager.get_current_network.return_value = "ETHEREUM"

        # Act
        result = assets_use_cases.get_native_asset()

        # Assert
        assert result == "ETH"
        mock_logger.info.assert_any_call("Getting native asset")
        mock_logger.info.assert_any_call(f"Native asset: ETH for networkETHEREUM")
        mock_config_manager.get_native_asset.assert_called_once()

    def test_get_native_asset_config_manager_exception(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_native_asset raises InvalidNetworkError when config_manager fails."""
        # Arrange
        mock_config_manager.get_native_asset.side_effect = Exception("Config error")
        mock_config_manager.get_current_network.return_value = "ETHEREUM"

        # Act & Assert
        with pytest.raises(InvalidNetworkError) as exc_info:
            assets_use_cases.get_native_asset()

        assert str(exc_info.value) == "Network ETHEREUM not available"
        mock_logger.error.assert_called_with("Error getting native asset: Config error")

    def test_get_all_assets_success(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_all_assets returns all assets successfully."""
        # Arrange
        expected_assets = ["ETH", "USDC", "USDT"]
        mock_config_manager.get_assets.return_value = expected_assets

        # Act
        result = assets_use_cases.get_all_assets()

        # Assert
        assert result == expected_assets
        mock_logger.info.assert_any_call("Getting all assets")
        mock_logger.info.assert_any_call(
            f"Successfully retrieved {len(expected_assets)} assets"
        )
        mock_config_manager.get_assets.assert_called_once()

    def test_get_all_assets_config_manager_exception(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_all_assets raises InvalidNetworkError when config_manager fails."""
        # Arrange
        mock_config_manager.get_assets.side_effect = Exception("Config error")
        mock_config_manager.get_current_network.return_value = "ETHEREUM"

        # Act & Assert
        with pytest.raises(InvalidNetworkError) as exc_info:
            assets_use_cases.get_all_assets()

        assert str(exc_info.value) == "Network ETHEREUM not available"
        mock_logger.error.assert_called_with("Error getting all assets: Config error")

    def test_get_asset_success(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_asset returns asset configuration successfully."""
        # Arrange
        asset = "USDC"
        expected_config = {
            "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        }
        mock_config_manager.get_asset.return_value = expected_config

        # Act
        result = assets_use_cases.get_asset(asset)

        # Assert
        assert result == expected_config
        mock_logger.info.assert_any_call(f"Getting asset configuration: {asset}")
        mock_logger.info.assert_any_call(
            f"Successfully retrieved asset configuration: {expected_config}"
        )
        mock_config_manager.get_asset.assert_called_once_with(asset)

    def test_get_asset_config_manager_exception(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_asset raises AssetNotFoundError when config_manager fails."""
        # Arrange
        asset = "INVALID"
        mock_config_manager.get_asset.side_effect = Exception("Config error")
        mock_config_manager.get_current_network.return_value = "ETHEREUM"

        # Act & Assert
        with pytest.raises(AssetNotFoundError) as exc_info:
            assets_use_cases.get_asset(asset)

        assert str(exc_info.value) == "Asset 'INVALID' not found on network 'ETHEREUM'"
        mock_logger.error.assert_called_with(
            f"Error getting asset configuration: Config error"
        )

    def test_get_asset_address_success(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_asset_address returns asset address successfully."""
        # Arrange
        asset = "USDC"
        network = "ETHEREUM"
        asset_config = {
            "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        }
        mock_config_manager.get_current_network.return_value = network
        mock_config_manager.get_asset.return_value = asset_config

        # Act
        result = assets_use_cases.get_asset_address(asset)

        # Assert
        assert str(result) == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        mock_logger.info.assert_any_call(
            f"Getting asset address: {asset} for current network"
        )
        mock_logger.info.assert_any_call(
            f"Successfully retrieved asset address: {asset_config[network]}"
        )

    def test_get_asset_address_network_not_found(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_asset_address raises AssetNotFoundError when network not in asset config."""
        # Arrange
        asset = "USDC"
        network = "INVALID_NETWORK"
        asset_config = {
            "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        }
        mock_config_manager.get_current_network.return_value = network
        mock_config_manager.get_asset.return_value = asset_config

        # Act & Assert
        with pytest.raises(AssetNotFoundError) as exc_info:
            assets_use_cases.get_asset_address(asset)

        assert (
            str(exc_info.value)
            == f"Asset 'USDC' not found on network 'INVALID_NETWORK'"
        )
        mock_logger.error.assert_any_call(
            f"Asset {asset} not configured for network {network}"
        )

    def test_get_asset_address_config_manager_exception(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_asset_address raises AssetNotFoundError when config_manager fails."""
        # Arrange
        asset = "USDC"
        mock_config_manager.get_asset.side_effect = Exception("Config error")

        # Act & Assert
        with pytest.raises(AssetNotFoundError) as exc_info:
            assets_use_cases.get_asset_address(asset)

        assert str(exc_info.value) == "Asset 'USDC' not found on network 'ETHEREUM'"
        mock_logger.error.assert_any_call("Error getting asset address: Config error")

    def test_get_asset_address_invalid_hex(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_asset_address raises AssetNotFoundError for invalid hex address."""
        # Arrange
        asset = "USDC"
        network = "ETHEREUM"
        asset_config = {
            "ETHEREUM": "invalid_hex_address",
            "ARBITRUM": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        }
        mock_config_manager.get_current_network.return_value = network
        mock_config_manager.get_asset.return_value = asset_config

        # Act & Assert
        with pytest.raises(AssetNotFoundError) as exc_info:
            assets_use_cases.get_asset_address(asset)

        assert str(exc_info.value) == f"Asset 'USDC' not found on network 'ETHEREUM'"
        mock_logger.error.assert_any_call(
            f"Invalid hex address format for asset {asset}: invalid_hex_address"
        )

    def test_empty_asset_list(self, assets_use_cases, mock_config_manager, mock_logger):
        """Test get_all_assets handles empty asset list."""
        # Arrange
        mock_config_manager.get_assets.return_value = []

        # Act
        result = assets_use_cases.get_all_assets()

        # Assert
        assert result == []
        mock_logger.info.assert_called_with("Successfully retrieved 0 assets")

    def test_single_asset_config(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test get_asset with single network configuration."""
        # Arrange
        asset = "SINGLE_ASSET"
        asset_config = {"ETHEREUM": "0x1234567890abcdef"}
        mock_config_manager.get_asset.return_value = asset_config

        # Act
        result = assets_use_cases.get_asset(asset)

        # Assert
        assert result == asset_config

    def test_case_sensitive_asset_names(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test that asset names are handled case-sensitively."""
        # Arrange
        asset = "usdc"  # lowercase
        mock_config_manager.get_asset.side_effect = Exception("Asset not found")

        # Act & Assert
        with pytest.raises(AssetNotFoundError):
            assets_use_cases.get_asset(asset)

    def test_logging_behavior(self, assets_use_cases, mock_config_manager, mock_logger):
        """Test that all methods log appropriate messages."""
        # Arrange
        asset = "USDC"
        mock_config_manager.get_native_asset.return_value = "ETH"
        mock_config_manager.get_assets.return_value = ["ETH", "USDC"]
        mock_config_manager.get_asset.return_value = {"ETHEREUM": "0x123"}

        # Act - Call all methods
        assets_use_cases.is_native_asset(asset)
        assets_use_cases.get_native_asset()
        assets_use_cases.get_all_assets()
        assets_use_cases.get_asset(asset)

        # Assert - Verify logging calls
        assert mock_logger.info.call_count >= 4
        assert mock_logger.error.call_count == 0

    def test_error_logging_behavior(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test that errors are properly logged."""
        # Arrange
        asset = "INVALID"
        mock_config_manager.get_asset.side_effect = Exception("Test error")

        # Act
        with pytest.raises(AssetNotFoundError):
            assets_use_cases.get_asset(asset)

        # Assert
        mock_logger.error.assert_called_with(
            f"Error getting asset configuration: Test error"
        )

    def test_hex_address_validation(
        self, assets_use_cases, mock_config_manager, mock_logger
    ):
        """Test that get_asset_address properly validates and converts hex addresses."""
        # Arrange
        asset = "USDC"
        network = "ETHEREUM"
        valid_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        asset_config = {network: valid_address}
        mock_config_manager.get_current_network.return_value = network
        mock_config_manager.get_asset.return_value = asset_config

        # Act
        result = assets_use_cases.get_asset_address(asset)

        # Assert
        assert str(result) == valid_address
