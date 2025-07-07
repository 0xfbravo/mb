"""
Unit tests for assets API endpoints.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.domain.errors import AssetNotFoundError, InvalidNetworkError
from app.presentation.api.assets import (get_all_assets, get_asset,
                                         get_native_asset)


class TestGetAllAssets:
    @pytest.mark.asyncio
    async def test_get_all_assets_success(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_all_assets = MagicMock(return_value=["ETH", "USDC"])
        request = MagicMock()
        result = await get_all_assets(request=request, di=mock_di)
        assert result == ["ETH", "USDC"]
        mock_di.logger.info.assert_called_once_with("Getting all assets")

    @pytest.mark.asyncio
    async def test_get_all_assets_db_not_initialized(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_all_assets = MagicMock(
            side_effect=RuntimeError("Database not initialized")
        )
        request = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_all_assets(request=request, di=mock_di)
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Database not available"
        mock_di.logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_assets_general_error(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_all_assets = MagicMock(
            side_effect=Exception("General error")
        )
        request = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_all_assets(request=request, di=mock_di)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unable to get all assets"
        mock_di.logger.error.assert_called_once()


class TestGetNativeAsset:
    @pytest.mark.asyncio
    async def test_get_native_asset_success(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_native_asset = MagicMock(return_value="ETH")
        request = MagicMock()
        result = await get_native_asset(request=request, di=mock_di)
        assert result == "ETH"
        mock_di.logger.info.assert_called_once_with("Getting native asset")

    @pytest.mark.asyncio
    async def test_get_native_asset_error(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_native_asset = MagicMock(
            side_effect=Exception("General error")
        )
        request = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_native_asset(request=request, di=mock_di)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unable to get native asset"
        mock_di.logger.error.assert_called_once()


class TestGetAsset:
    @pytest.mark.asyncio
    async def test_get_asset_success(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_asset = MagicMock(
            return_value={"symbol": "ETH", "decimals": 18}
        )
        request = MagicMock()
        asset = "ETH"
        result = await get_asset(request=request, asset=asset, di=mock_di)
        assert result["symbol"] == "ETH"
        mock_di.logger.info.assert_called_once_with(f"Getting asset: {asset}")

    @pytest.mark.asyncio
    async def test_get_asset_not_found(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_asset = MagicMock(
            side_effect=AssetNotFoundError("FOO", "ethereum")
        )
        request = MagicMock()
        asset = "FOO"
        with pytest.raises(HTTPException) as exc_info:
            await get_asset(request=request, asset=asset, di=mock_di)
        assert exc_info.value.status_code == 400
        assert "Asset 'FOO' not found on network 'ethereum'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_asset_invalid_network(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_asset = MagicMock(
            side_effect=InvalidNetworkError("Invalid network")
        )
        request = MagicMock()
        asset = "FOO"
        with pytest.raises(HTTPException) as exc_info:
            await get_asset(request=request, asset=asset, di=mock_di)
        assert exc_info.value.status_code == 400
        assert "Invalid network" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_asset_general_error(self, mock_dependency_injection):
        mock_di = mock_dependency_injection
        mock_di.assets_uc.get_asset = MagicMock(side_effect=Exception("General error"))
        request = MagicMock()
        asset = "FOO"
        with pytest.raises(HTTPException) as exc_info:
            await get_asset(request=request, asset=asset, di=mock_di)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unable to get asset"
        mock_di.logger.error.assert_called_once()
