"""
Integration tests for transaction API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.presentation.api.routes import api_router
from app.domain.tx_models import Transaction, TransactionValidation, CreateTx, TransactionsPagination
from app.domain.models import Pagination
from app.domain.errors import (
    EmptyAddressError, EmptyTransactionIdError, InsufficientBalanceError, InvalidAmountError,
    InvalidNetworkError, InvalidPaginationError, InvalidTxAssetError, InvalidWalletPrivateKeyError,
    SameAddressError, WalletNotFoundError
)


class TestTransactionAPIIntegration:
    """Integration tests for transaction API endpoints."""

    @pytest.fixture
    def mock_di(self):
        """Create a mock dependency injection container."""
        di = MagicMock()
        di.logger = MagicMock()
        di.tx_uc = MagicMock()
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

    def test_validate_transaction_success(self, client, mock_di):
        """Test successful transaction validation."""
        # Arrange
        mock_validation = TransactionValidation(
            is_valid=True,
            transaction_hash="0xabc123",
            transfers=[],
            validation_message="Valid transaction",
            network="ethereum"
        )
        mock_di.tx_uc.validate_transaction = AsyncMock(return_value=mock_validation)
        
        # Act
        response = client.post("/api/tx/validate?tx_hash=0xabc123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["transaction_hash"] == "0xabc123"
        assert data["network"] == "ethereum"

    def test_validate_transaction_empty_address(self, client, mock_di):
        """Test transaction validation with empty address error."""
        # Arrange
        mock_di.tx_uc.validate_transaction = AsyncMock(side_effect=EmptyAddressError("from"))
        
        # Act
        response = client.post("/api/tx/validate?tx_hash=0xabc123")
        
        # Assert
        assert response.status_code == 400
        assert "from address cannot be empty" in response.json()["detail"]

    def test_validate_transaction_db_not_initialized(self, client, mock_di):
        """Test transaction validation when database is not initialized."""
        # Arrange
        mock_di.tx_uc.validate_transaction = AsyncMock(side_effect=RuntimeError("Database not initialized"))
        
        # Act
        response = client.post("/api/tx/validate?tx_hash=0xabc123")
        
        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not initialized"

    def test_validate_transaction_general_error(self, client, mock_di):
        """Test transaction validation with general error."""
        # Arrange
        mock_di.tx_uc.validate_transaction = AsyncMock(side_effect=Exception("General error"))
        
        # Act
        response = client.post("/api/tx/validate?tx_hash=0xabc123")
        
        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Unexpected error"

    def test_create_transaction_success(self, client, mock_di):
        """Test successful transaction creation."""
        # Arrange
        mock_transaction = Transaction(
            id=uuid4(),
            tx_hash="0xabc123",
            asset="ETH",
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0xfedcba0987654321fedcba0987654321fedcba09",
            amount=1.5
        )
        mock_di.tx_uc.create = AsyncMock(return_value=mock_transaction)
        
        # Act
        tx_data = {
            "from_address": "0x1234567890123456789012345678901234567890",
            "to_address": "0xfedcba0987654321fedcba0987654321fedcba09",
            "asset": "ETH",
            "amount": 1.5
        }
        response = client.post("/api/tx/", json=tx_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tx_hash"] == "0xabc123"
        assert data["asset"] == "ETH"
        assert data["amount"] == 1.5

    def test_create_transaction_same_address_error(self, client, mock_di):
        """Test transaction creation with same address error."""
        # Arrange
        mock_di.tx_uc.create = AsyncMock(side_effect=SameAddressError("0x1234567890123456789012345678901234567890"))
        
        # Act
        tx_data = {
            "from_address": "0x1234567890123456789012345678901234567890",
            "to_address": "0x1234567890123456789012345678901234567890",
            "asset": "ETH",
            "amount": 1.5
        }
        response = client.post("/api/tx/", json=tx_data)
        
        # Assert
        assert response.status_code == 400
        assert "From address and to address cannot be the same" in response.json()["detail"]

    def test_create_transaction_insufficient_balance_error(self, client, mock_di):
        """Test transaction creation with insufficient balance error."""
        # Arrange
        mock_di.tx_uc.create = AsyncMock(side_effect=InsufficientBalanceError("ETH", 0.5, 1.0))
        
        # Act
        tx_data = {
            "from_address": "0x1234567890123456789012345678901234567890",
            "to_address": "0xfedcba0987654321fedcba0987654321fedcba09",
            "asset": "ETH",
            "amount": 1.0
        }
        response = client.post("/api/tx/", json=tx_data)
        
        # Assert
        assert response.status_code == 400
        assert "Insufficient balance" in response.json()["detail"]

    def test_create_transaction_db_not_initialized(self, client, mock_di):
        """Test transaction creation when database is not initialized."""
        # Arrange
        mock_di.tx_uc.create = AsyncMock(side_effect=RuntimeError("Database not initialized"))
        
        # Act
        tx_data = {
            "from_address": "0x1234567890123456789012345678901234567890",
            "to_address": "0xfedcba0987654321fedcba0987654321fedcba09",
            "asset": "ETH",
            "amount": 1.5
        }
        response = client.post("/api/tx/", json=tx_data)
        
        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not initialized"

    def test_get_transactions_by_id(self, client, mock_di):
        """Test getting transaction by ID."""
        # Arrange
        transaction_id = uuid4()
        mock_transaction = Transaction(
            id=transaction_id,
            tx_hash="0xabc123",
            asset="ETH",
            amount=1.5
        )
        mock_di.tx_uc.get_by_id = AsyncMock(return_value=mock_transaction)
        
        # Act
        response = client.get(f"/api/tx/?transaction_id={transaction_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tx_hash"] == "0xabc123"
        assert data["asset"] == "ETH"

    def test_get_transactions_by_tx_hash(self, client, mock_di):
        """Test getting transaction by transaction hash."""
        # Arrange
        mock_transaction = Transaction(
            id=uuid4(),
            tx_hash="0xabc123",
            asset="ETH",
            amount=1.5
        )
        mock_di.tx_uc.get_by_tx_hash = AsyncMock(return_value=mock_transaction)
        
        # Act
        response = client.get("/api/tx/?tx_hash=0xabc123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tx_hash"] == "0xabc123"

    def test_get_transactions_by_wallet_address(self, client, mock_di):
        """Test getting transactions by wallet address."""
        # Arrange
        from app.domain.tx_models import TransactionsPagination
        from app.domain.models import Pagination
        mock_pagination = TransactionsPagination(
            transactions=[
                Transaction(
                    id=uuid4(),
                    tx_hash="0xabc123",
                    asset="ETH",
                    amount=1.5
                )
            ],
            pagination=Pagination(total=1, page=1)
        )
        mock_di.tx_uc.get_txs = AsyncMock(return_value=mock_pagination)
        
        # Act
        response = client.get("/api/tx/?wallet_address=0x1234567890123456789012345678901234567890")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert data["transactions"][0]["tx_hash"] == "0xabc123"

    def test_get_transactions_pagination(self, client, mock_di):
        """Test getting transactions with pagination."""
        # Arrange
        mock_pagination = TransactionsPagination(
            transactions=[],
            pagination=Pagination(total=0, page=1)
        )
        mock_di.tx_uc.get_all = AsyncMock(return_value=mock_pagination)
        
        # Act
        response = client.get("/api/tx/?page=1&limit=10")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "pagination" in data
        assert data["pagination"]["total"] == 0

    def test_get_transactions_invalid_pagination(self, client, mock_di):
        """Test getting transactions with invalid pagination."""
        # Arrange
        mock_di.tx_uc.get_all = AsyncMock(side_effect=InvalidPaginationError("Invalid pagination"))
        
        # Act
        response = client.get("/api/tx/?page=1&limit=10")
        
        # Assert
        assert response.status_code == 400
        assert "Invalid pagination" in response.json()["detail"]

    def test_get_transactions_db_not_initialized(self, client, mock_di):
        """Test getting transactions when database is not initialized."""
        # Arrange
        mock_di.tx_uc.get_all = AsyncMock(side_effect=RuntimeError("Database not initialized"))
        
        # Act
        response = client.get("/api/tx/?page=1&limit=10")
        
        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Database not initialized" 