"""
Integration tests for wallet API endpoints.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.domain.enums import WalletStatus
from app.domain.models import Pagination
from app.domain.wallet_models import Wallet, WalletsPagination
from app.presentation.api.routes import api_router


class TestWalletAPIIntegration:
    """Integration tests for wallet API endpoints."""

    @pytest.fixture
    def mock_di(self):
        """Create a mock dependency injection container."""
        di = MagicMock()
        di.logger = MagicMock()
        di.wallet_uc = MagicMock()
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

    def test_create_wallet_success(self, client, mock_di):
        """Test successful wallet creation."""
        # Arrange
        mock_wallet = Wallet(
            id=uuid4(),
            address="0x1234567890abcdef",
            private_key="test_private_key",
            status=WalletStatus.ACTIVE,
        )
        mock_di.wallet_uc.create = AsyncMock(return_value=[mock_wallet])

        # Act
        response = client.post("/api/wallet/?number_of_wallets=1")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["address"] == "0x1234567890abcdef"
        mock_di.wallet_uc.create.assert_called_once_with(1)

    def test_create_wallet_multiple(self, client, mock_di):
        """Test creating multiple wallets."""
        # Arrange
        mock_wallets = [
            Wallet(
                id=uuid4(),
                address=f"0x1234567890abcdef{i}",
                private_key=f"test_private_key_{i}",
                status=WalletStatus.ACTIVE,
            )
            for i in range(3)
        ]
        mock_di.wallet_uc.create = AsyncMock(return_value=mock_wallets)

        # Act
        response = client.post("/api/wallet/?number_of_wallets=3")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        mock_di.wallet_uc.create.assert_called_once_with(3)

    def test_create_wallet_database_error(self, client, mock_di):
        """Test wallet creation when database is not available."""
        # Arrange
        mock_di.wallet_uc.create = AsyncMock(
            side_effect=RuntimeError("Database not initialized")
        )

        # Act
        response = client.post("/api/wallet/?number_of_wallets=1")

        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not available"

    def test_create_wallet_general_error(self, client, mock_di):
        """Test wallet creation with general error."""
        # Arrange
        mock_di.wallet_uc.create = AsyncMock(side_effect=Exception("General error"))

        # Act
        response = client.post("/api/wallet/?number_of_wallets=1")

        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Unable to create wallet"

    def test_get_wallets_success(self, client, mock_di):
        """Test successful wallet retrieval with pagination."""
        # Arrange
        mock_wallet = Wallet(
            id=uuid4(),
            address="0x1234567890abcdef",
            private_key="test_private_key",
            status=WalletStatus.ACTIVE,
        )
        mock_pagination = WalletsPagination(
            pagination=Pagination(total=1, page=1), wallets=[mock_wallet]
        )
        mock_di.wallet_uc.get_all = AsyncMock(return_value=mock_pagination)

        # Act
        response = client.get("/api/wallet/?page=1&limit=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["total"] == 1
        assert data["pagination"]["page"] == 1
        assert len(data["wallets"]) == 1
        assert data["wallets"][0]["address"] == "0x1234567890abcdef"

    def test_get_wallets_invalid_page(self, client, mock_di):
        """Test wallet retrieval with invalid page number."""
        # Act
        response = client.get("/api/wallet/?page=0&limit=10")

        # Assert
        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "greater_than_equal"
        assert "greater than or equal to 1" in response.json()["detail"][0]["msg"]

    def test_get_wallets_invalid_limit(self, client, mock_di):
        """Test wallet retrieval with invalid limit."""
        # Act
        response = client.get("/api/wallet/?page=1&limit=1001")

        # Assert
        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "less_than_equal"
        assert "less than or equal to 1000" in response.json()["detail"][0]["msg"]

    def test_get_wallets_database_error(self, client, mock_di):
        """Test wallet retrieval when database is not available."""
        # Arrange
        mock_di.wallet_uc.get_all = AsyncMock(
            side_effect=RuntimeError("Database not initialized")
        )

        # Act
        response = client.get("/api/wallet/?page=1&limit=10")

        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not available"

    def test_get_wallet_success(self, client, mock_di):
        """Test successful wallet retrieval by address."""
        # Arrange
        mock_wallet = Wallet(
            id=uuid4(),
            address="0x1234567890abcdef",
            private_key="test_private_key",
            status=WalletStatus.ACTIVE,
        )
        mock_di.wallet_uc.get_by_address = AsyncMock(return_value=mock_wallet)

        # Act
        response = client.get("/api/wallet/0x1234567890abcdef")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "0x1234567890abcdef"

    def test_get_wallet_database_error(self, client, mock_di):
        """Test wallet retrieval when database is not available."""
        # Arrange
        mock_di.wallet_uc.get_by_address = AsyncMock(
            side_effect=RuntimeError("Database not initialized")
        )

        # Act
        response = client.get("/api/wallet/0x1234567890abcdef")

        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not available"

    def test_get_wallet_not_found(self, client, mock_di):
        """Test wallet retrieval when wallet is not found."""
        # Arrange
        mock_di.wallet_uc.get_by_address = AsyncMock(
            side_effect=Exception("Wallet not found")
        )

        # Act
        response = client.get("/api/wallet/0x1234567890abcdef")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Wallet not found"

    def test_delete_wallet_success(self, client, mock_di):
        """Test successful wallet deletion."""
        # Arrange
        mock_wallet = Wallet(
            id=uuid4(),
            address="0x1234567890abcdef",
            private_key="test_private_key",
            status=WalletStatus.INACTIVE,
        )
        mock_di.wallet_uc.delete_wallet = AsyncMock(return_value=mock_wallet)

        # Act
        response = client.delete("/api/wallet/0x1234567890abcdef")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "0x1234567890abcdef"
        assert data["status"] == "INACTIVE"

    def test_delete_wallet_database_error(self, client, mock_di):
        """Test wallet deletion when database is not available."""
        # Arrange
        mock_di.wallet_uc.delete_wallet = AsyncMock(
            side_effect=RuntimeError("Database not initialized")
        )

        # Act
        response = client.delete("/api/wallet/0x1234567890abcdef")

        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not available"

    def test_delete_wallet_general_error(self, client, mock_di):
        """Test wallet deletion with general error."""
        # Arrange
        mock_di.wallet_uc.delete_wallet = AsyncMock(
            side_effect=Exception("General error")
        )

        # Act
        response = client.delete("/api/wallet/0x1234567890abcdef")

        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Unable to delete wallet"
