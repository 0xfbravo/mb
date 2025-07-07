"""
Integration tests for assets API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.presentation.api.routes import api_router
from app.domain.errors import AssetNotFoundError, InvalidNetworkError


class TestAssetsAPIIntegration:
    """Integration tests for assets API endpoints."""

    @pytest.fixture
    def mock_di(self):
        """Create a mock dependency injection container."""
        di = MagicMock()
        di.logger = MagicMock()
        di.assets_uc = MagicMock()
        return di

    @pytest.fixture
    def client(self, mock_di):
        """Create a test client with mocked dependencies."""
        from fastapi import FastAPI
        from app.utils.di import get_dependency_injection
        
        app = FastAPI()
        app.include_router(api_router)
        
        # Mock the dependency injection
        app.dependency_overrides[get_dependency_injection] = lambda: mock_di
        
        return TestClient(app)

    def test_get_all_assets_success(self, client, mock_di):
        """Test successful retrieval of all assets."""
        # Arrange
        mock_di.assets_uc.get_all_assets = MagicMock(return_value=["ETH", "USDC", "DAI"])
        
        # Act
        response = client.post("/api/assets/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == ["ETH", "USDC", "DAI"]
        mock_di.assets_uc.get_all_assets.assert_called_once()

    def test_get_all_assets_database_error(self, client, mock_di):
        """Test assets retrieval when database is not available."""
        # Arrange
        mock_di.assets_uc.get_all_assets = MagicMock(side_effect=RuntimeError("Database not initialized"))
        
        # Act
        response = client.post("/api/assets/")
        
        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not available"

    def test_get_all_assets_general_error(self, client, mock_di):
        """Test assets retrieval with general error."""
        # Arrange
        mock_di.assets_uc.get_all_assets = MagicMock(side_effect=Exception("General error"))
        
        # Act
        response = client.post("/api/assets/")
        
        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Unable to get all assets"

    def test_get_native_asset_success(self, client, mock_di):
        """Test successful retrieval of native asset."""
        # Arrange
        mock_di.assets_uc.get_native_asset = MagicMock(return_value="ETH")
        
        # Act
        response = client.get("/api/assets/native")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == "ETH"
        mock_di.assets_uc.get_native_asset.assert_called_once()

    def test_get_native_asset_error(self, client, mock_di):
        """Test native asset retrieval with error."""
        # Arrange
        mock_di.assets_uc.get_native_asset = MagicMock(side_effect=Exception("General error"))
        
        # Act
        response = client.get("/api/assets/native")
        
        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Unable to get native asset"

    def test_get_asset_success(self, client, mock_di):
        """Test successful retrieval of specific asset."""
        # Arrange
        asset_config = {
            "symbol": "USDC",
            "decimals": 6,
            "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        }
        mock_di.assets_uc.get_asset = MagicMock(return_value=asset_config)
        
        # Act
        response = client.get("/api/assets/USDC")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "USDC"
        assert data["decimals"] == 6
        mock_di.assets_uc.get_asset.assert_called_once_with("USDC")

    def test_get_asset_not_found(self, client, mock_di):
        """Test asset retrieval when asset is not found."""
        # Arrange
        mock_di.assets_uc.get_asset = MagicMock(side_effect=AssetNotFoundError("FOO", "ethereum"))
        
        # Act
        response = client.get("/api/assets/FOO")
        
        # Assert
        assert response.status_code == 400
        assert "Asset 'FOO' not found on network 'ethereum'" in response.json()["detail"]

    def test_get_asset_invalid_network(self, client, mock_di):
        """Test asset retrieval when network is invalid."""
        # Arrange
        mock_di.assets_uc.get_asset = MagicMock(side_effect=InvalidNetworkError("invalid_network"))
        
        # Act
        response = client.get("/api/assets/USDC")
        
        # Assert
        assert response.status_code == 400
        assert "Network invalid_network not available" in response.json()["detail"]

    def test_get_asset_general_error(self, client, mock_di):
        """Test asset retrieval with general error."""
        # Arrange
        mock_di.assets_uc.get_asset = MagicMock(side_effect=Exception("General error"))
        
        # Act
        response = client.get("/api/assets/USDC")
        
        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Unable to get asset" 