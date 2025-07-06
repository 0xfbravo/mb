import re
from typing import Any

from ens.utils import HexStr  # type: ignore
from eth_typing import HexAddress

from app.domain.errors import AssetNotFoundError, InvalidNetworkError
from app.utils.config_manager import ConfigManager


class AssetsUseCases:
    """Use cases for assets operations."""

    def __init__(self, config_manager: ConfigManager, logger: Any):
        self._config_manager = config_manager
        self._logger = logger

    def _is_valid_hex_address(self, address: str) -> bool:
        """Check if the address is a valid hex address.
        Args:
            address: The address to validate.
        Returns:
            True if the address is valid, False otherwise.
        """
        # Check if it's a valid Ethereum address format
        # (0x followed by 40 hex characters)
        pattern = r"^0x[a-fA-F0-9]{40}$"
        return bool(re.match(pattern, address))

    def is_native_asset(self, asset: str) -> bool:
        """Check if the asset is the native asset.
        Args:
            asset: The asset to check.
        Returns:
            True if the asset is the native asset, False otherwise.
        """
        try:
            self._logger.info(f"Checking if asset {asset} is the native asset")
            native_asset = self._config_manager.get_native_asset()
            is_native_asset = native_asset == asset
            self._logger.info(
                f"Native asset: {native_asset} for network"
                f"{self._config_manager.get_current_network()}"
            )
            return is_native_asset
        except Exception as e:
            self._logger.error(
                f"Error checking if asset {asset} is the native asset: {e}"
            )
            raise InvalidNetworkError(self._config_manager.get_current_network())

    def get_native_asset(self) -> str:
        """Get native asset.
        Returns:
            The native asset.
        """
        try:
            self._logger.info("Getting native asset")
            native_asset = self._config_manager.get_native_asset()
            self._logger.info(
                f"Native asset: {native_asset} for network"
                f"{self._config_manager.get_current_network()}"
            )
            return native_asset
        except Exception as e:
            self._logger.error(f"Error getting native asset: {e}")
            raise InvalidNetworkError(self._config_manager.get_current_network())

    def get_all_assets(self) -> list[str]:
        """Get all assets.
        Returns:
            The list of all assets.
        """
        try:
            self._logger.info("Getting all assets")
            assets = self._config_manager.get_assets()
            self._logger.info(f"Successfully retrieved {len(assets)} assets")
            return assets
        except Exception as e:
            self._logger.error(f"Error getting all assets: {e}")
            raise InvalidNetworkError(self._config_manager.get_current_network())

    def get_asset(self, asset: str) -> dict:
        """Get asset configuration.
        Args:
            asset: The asset to get the configuration of.
        Returns:
            The configuration of the asset.
        """
        try:
            self._logger.info(f"Getting asset configuration: {asset}")
            asset_config = self._config_manager.get_asset(asset)
            self._logger.info(
                f"Successfully retrieved asset configuration: {asset_config}"
            )
            return asset_config
        except Exception as e:
            self._logger.error(f"Error getting asset configuration: {e}")
            raise AssetNotFoundError(asset, self._config_manager.get_current_network())

    def get_asset_address(self, asset: str) -> HexAddress:
        """Get asset address.
        Args:
            asset: The asset to get the address of.
        Returns:
            The address of the asset.
        """
        try:
            self._logger.info(f"Getting asset address: {asset} for current network")
            network = self._config_manager.get_current_network()
            asset_config = self._config_manager.get_asset(asset)

            if network not in asset_config:
                self._logger.error(
                    f"Asset {asset} not configured for network {network}"
                )
                raise AssetNotFoundError(asset, network)

            address = asset_config[network]

            # Validate hex address format
            if not self._is_valid_hex_address(address):
                self._logger.error(
                    f"Invalid hex address format for asset {asset}: {address}"
                )
                raise AssetNotFoundError(asset, network)

            self._logger.info(f"Successfully retrieved asset address: {address}")
            return HexAddress(HexStr(address))
        except Exception as e:
            self._logger.error(f"Error getting asset address: {e}")
            raise AssetNotFoundError(asset, self._config_manager.get_current_network())
