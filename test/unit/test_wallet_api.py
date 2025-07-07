"""
Unit tests for wallet API endpoints.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.presentation.api.wallet import (
    create_wallet,
    get_wallets,
    get_wallet,
    delete_wallet,
)
from app.domain.wallet_models import Wallet, WalletsPagination
from app.domain.models import Pagination
from app.domain.enums import WalletStatus


class TestCreateWallet:
    """Test cases for create_wallet endpoint."""

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, mock_dependency_injection):
        """Test successful wallet creation."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.create = AsyncMock(
            return_value=[
                Wallet(
                    id=uuid4(),
                    address="0x1234567890abcdef",
                    private_key="test_private_key",
                    status=WalletStatus.ACTIVE,
                )
            ]
        )
        
        request = MagicMock()
        
        # Act
        result = await create_wallet(
            request=request,
            di=mock_di,
            number_of_wallets=1,
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].address == "0x1234567890abcdef"
        mock_di.wallet_uc.create.assert_called_once_with(1)
        mock_di.logger.info.assert_called_once_with("Creating wallet")

    @pytest.mark.asyncio
    async def test_create_wallet_database_not_initialized(self, mock_dependency_injection):
        """Test wallet creation when database is not initialized."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.create = AsyncMock(side_effect=RuntimeError("Database not initialized"))
        
        request = MagicMock()
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_wallet(
                request=request,
                di=mock_di,
                number_of_wallets=1,
            )
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Database not available"
        mock_di.logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wallet_general_error(self, mock_dependency_injection):
        """Test wallet creation with general error."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.create = AsyncMock(side_effect=Exception("General error"))
        
        request = MagicMock()
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_wallet(
                request=request,
                di=mock_di,
                number_of_wallets=1,
            )
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unable to create wallet"
        mock_di.logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wallet_multiple_wallets(self, mock_dependency_injection):
        """Test creating multiple wallets."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.create = AsyncMock(
            return_value=[
                Wallet(
                    id=uuid4(),
                    address=f"0x1234567890abcdef{i}",
                    private_key=f"test_private_key_{i}",
                    status=WalletStatus.ACTIVE,
                )
                for i in range(3)
            ]
        )
        
        request = MagicMock()
        
        # Act
        result = await create_wallet(
            request=request,
            di=mock_di,
            number_of_wallets=3,
        )
        
        # Assert
        assert len(result) == 3
        mock_di.wallet_uc.create.assert_called_once_with(3)


class TestGetWallets:
    """Test cases for get_wallets endpoint."""

    @pytest.mark.asyncio
    async def test_get_wallets_success(self, mock_dependency_injection):
        """Test successful wallet retrieval with pagination."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.get_all = AsyncMock(
            return_value=WalletsPagination(
                pagination=Pagination(
                    page=1,
                    total=1,
                ),
                wallets=[
                    Wallet(
                        id=uuid4(),
                        address="0x1234567890abcdef",
                        private_key="test_private_key",
                        status=WalletStatus.ACTIVE,
                    )
                ],
            )
        )
        
        request = MagicMock()
        
        # Act
        result = await get_wallets(
            request=request,
            di=mock_di,
            page=1,
            limit=10,
        )
        
        # Assert
        assert result.pagination.page == 1
        assert result.pagination.total == 1
        assert len(result.wallets) == 1
        mock_di.wallet_uc.get_all.assert_called_once_with(page=1, limit=10)
        mock_di.logger.info.assert_called_once_with("Getting wallets with pagination: page=1, limit=10")

    @pytest.mark.asyncio
    async def test_get_wallets_invalid_page(self, mock_dependency_injection):
        """Test wallet retrieval with invalid page number."""
        # Arrange
        mock_di = mock_dependency_injection
        request = MagicMock()
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_wallets(
                request=request,
                di=mock_di,
                page=0,
                limit=10,
            )
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Page number must be greater than 0"

    @pytest.mark.asyncio
    async def test_get_wallets_invalid_limit(self, mock_dependency_injection):
        """Test wallet retrieval with invalid limit."""
        # Arrange
        mock_di = mock_dependency_injection
        request = MagicMock()
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_wallets(
                request=request,
                di=mock_di,
                page=1,
                limit=1001,
            )
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Limit must be between 1 and 1000"

    @pytest.mark.asyncio
    async def test_get_wallets_database_not_initialized(self, mock_dependency_injection):
        """Test wallet retrieval when database is not initialized."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.get_all = AsyncMock(side_effect=RuntimeError("Database not initialized"))
        
        request = MagicMock()
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_wallets(
                request=request,
                di=mock_di,
                page=1,
                limit=10,
            )
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Database not available"

    @pytest.mark.asyncio
    async def test_get_wallets_general_error(self, mock_dependency_injection):
        """Test wallet retrieval with general error."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.get_all = AsyncMock(side_effect=Exception("General error"))
        
        request = MagicMock()
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_wallets(
                request=request,
                di=mock_di,
                page=1,
                limit=10,
            )
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unable to get wallets"


class TestGetWallet:
    """Test cases for get_wallet endpoint."""

    @pytest.mark.asyncio
    async def test_get_wallet_success(self, mock_dependency_injection):
        """Test successful wallet retrieval by address."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.get_by_address = AsyncMock(
            return_value=                Wallet(
                    id=uuid4(),
                    address="0x1234567890abcdef",
                    private_key="test_private_key",
                    status=WalletStatus.ACTIVE,
                )
        )
        
        request = MagicMock()
        address = "0x1234567890abcdef"
        
        # Act
        result = await get_wallet(
            request=request,
            address=address,
            di=mock_di,
        )
        
        # Assert
        assert result.address == address
        mock_di.wallet_uc.get_by_address.assert_called_once_with(address)
        mock_di.logger.info.assert_called_once_with("Getting wallet")

    @pytest.mark.asyncio
    async def test_get_wallet_database_not_initialized(self, mock_dependency_injection):
        """Test wallet retrieval when database is not initialized."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.get_by_address = AsyncMock(side_effect=RuntimeError("Database not initialized"))
        
        request = MagicMock()
        address = "0x1234567890abcdef"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_wallet(
                request=request,
                address=address,
                di=mock_di,
            )
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Database not available"

    @pytest.mark.asyncio
    async def test_get_wallet_not_found(self, mock_dependency_injection):
        """Test wallet retrieval when wallet is not found."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.get_by_address = AsyncMock(side_effect=Exception("Wallet not found"))
        
        request = MagicMock()
        address = "0x1234567890abcdef"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_wallet(
                request=request,
                address=address,
                di=mock_di,
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Wallet not found"


class TestDeleteWallet:
    """Test cases for delete_wallet endpoint."""

    @pytest.mark.asyncio
    async def test_delete_wallet_success(self, mock_dependency_injection):
        """Test successful wallet deletion."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.delete_wallet = AsyncMock(
            return_value=Wallet(
                id=uuid4(),
                address="0x1234567890abcdef",
                private_key="test_private_key",
                status=WalletStatus.INACTIVE,
            )
        )
        
        request = MagicMock()
        address = "0x1234567890abcdef"
        
        # Act
        result = await delete_wallet(
            request=request,
            address=address,
            di=mock_di,
        )
        
        # Assert
        assert result.address == address
        assert result.status == WalletStatus.INACTIVE
        mock_di.wallet_uc.delete_wallet.assert_called_once_with(address)
        mock_di.logger.info.assert_called_once_with(f"Deleting wallet: {address}")

    @pytest.mark.asyncio
    async def test_delete_wallet_database_not_initialized(self, mock_dependency_injection):
        """Test wallet deletion when database is not initialized."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.delete_wallet = AsyncMock(side_effect=RuntimeError("Database not initialized"))
        
        request = MagicMock()
        address = "0x1234567890abcdef"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_wallet(
                request=request,
                address=address,
                di=mock_di,
            )
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Database not available"

    @pytest.mark.asyncio
    async def test_delete_wallet_general_error(self, mock_dependency_injection):
        """Test wallet deletion with general error."""
        # Arrange
        mock_di = mock_dependency_injection
        mock_di.wallet_uc.delete_wallet = AsyncMock(side_effect=Exception("General error"))
        
        request = MagicMock()
        address = "0x1234567890abcdef"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_wallet(
                request=request,
                address=address,
                di=mock_di,
            )
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Unable to delete wallet" 