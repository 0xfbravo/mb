"""
Unit tests for WalletUseCases class.

This module contains unit tests for the WalletUseCases class, which is responsible
for handling wallet-related business logic.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.data.database import Wallet as DBWallet
from app.data.evm.main import EVMService
from app.domain.assets_use_cases import AssetsUseCases
from app.domain.enums import WalletStatus
from app.domain.errors import (BatchOperationError, DatabaseError,
                               InvalidPaginationError,
                               InvalidWalletAddressError)
from app.domain.wallet_models import Pagination, Wallet, WalletsPagination
from app.domain.wallet_use_cases import WalletUseCases


class TestWalletUseCases:
    """Test cases for WalletUseCases class."""

    @pytest.fixture
    def mock_wallet_repo(self):
        """Create a mock WalletRepository for testing."""
        repo = MagicMock()
        repo.create = AsyncMock()
        repo.get_by_address = AsyncMock()
        repo.get_all = AsyncMock()
        repo.get_count = AsyncMock()
        repo.delete = AsyncMock()
        return repo

    @pytest.fixture
    def mock_evm_service(self):
        """Create a mock EVMService for testing."""
        evm_service = MagicMock(spec=EVMService)
        evm_service.create_wallet = MagicMock()
        evm_service.get_wallet_balance = MagicMock()
        evm_service.get_token_balance = MagicMock()
        return evm_service

    @pytest.fixture
    def mock_assets_use_cases(self):
        """Create a mock AssetsUseCases for testing."""
        assets_use_cases = MagicMock(spec=AssetsUseCases)
        assets_use_cases.get_asset_address = MagicMock()
        return assets_use_cases

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = MagicMock()
        logger.info = MagicMock()
        logger.error = MagicMock()
        return logger

    @pytest.fixture
    def wallet_use_cases(
        self,
        mock_wallet_repo,
        mock_evm_service,
        mock_assets_use_cases,
        mock_logger,
    ):
        """Create a WalletUseCases instance with mocked dependencies."""
        return WalletUseCases(
            wallet_repo=mock_wallet_repo,
            evm_service=mock_evm_service,
            assets_use_cases=mock_assets_use_cases,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_wallet_data(self):
        """Create sample wallet data for testing."""
        private_key = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        return {
            "id": uuid4(),
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "private_key": private_key,
            "status": WalletStatus.ACTIVE,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted_at": None,
        }

    @pytest.fixture
    def sample_db_wallet(self, sample_wallet_data):
        """Create a sample DBWallet instance."""
        return DBWallet(**sample_wallet_data)

    @pytest.fixture
    def sample_wallet(self, sample_wallet_data):
        """Create a sample Wallet instance."""
        return Wallet(**sample_wallet_data)

    def test_init(
        self, mock_wallet_repo, mock_evm_service, mock_assets_use_cases, mock_logger
    ):
        """Test WalletUseCases initialization."""
        wallet_use_cases = WalletUseCases(
            wallet_repo=mock_wallet_repo,
            evm_service=mock_evm_service,
            assets_use_cases=mock_assets_use_cases,
            logger=mock_logger,
        )
        assert wallet_use_cases._wallet_repo == mock_wallet_repo
        assert wallet_use_cases._evm_service == mock_evm_service
        assert wallet_use_cases._assets_use_cases == mock_assets_use_cases
        assert wallet_use_cases._logger == mock_logger

    @pytest.mark.asyncio
    async def test_create_single_wallet_success(
        self,
        wallet_use_cases,
        mock_wallet_repo,
        mock_evm_service,
        mock_logger,
        sample_db_wallet,
    ):
        """Test successful creation of a single wallet."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet.key.hex.return_value = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_evm_service.create_wallet.return_value = mock_wallet
        mock_wallet_repo.create.return_value = sample_db_wallet

        # Act
        result = await wallet_use_cases.create(1)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], Wallet)
        assert result[0].address == sample_db_wallet.address
        mock_evm_service.create_wallet.assert_called_once()
        mock_wallet_repo.create.assert_called_once_with(
            address=mock_wallet.address,
            private_key=mock_wallet.key.hex(),
        )
        mock_logger.info.assert_any_call("Creating wallet")
        mock_logger.info.assert_any_call(
            f"Successfully created wallet: {mock_wallet.address}"
        )
        mock_logger.info.assert_any_call("Successfully created 1 wallets")

    @pytest.mark.asyncio
    async def test_create_multiple_wallets_success(
        self,
        wallet_use_cases,
        mock_wallet_repo,
        mock_evm_service,
        mock_logger,
        sample_db_wallet,
    ):
        """Test successful creation of multiple wallets."""
        # Arrange
        number_of_wallets = 3
        mock_wallets = []
        for i in range(number_of_wallets):
            mock_wallet = MagicMock()
            mock_wallet.address = f"0x1234567890abcdef1234567890abcdef1234567{i}"
            mock_wallet.key.hex.return_value = (
                f"0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef123456789{i}"
            )
            mock_wallets.append(mock_wallet)

        mock_evm_service.create_wallet.side_effect = mock_wallets
        mock_wallet_repo.create.return_value = sample_db_wallet

        # Act
        result = await wallet_use_cases.create(number_of_wallets)

        # Assert
        assert len(result) == number_of_wallets
        assert all(isinstance(wallet, Wallet) for wallet in result)
        assert mock_evm_service.create_wallet.call_count == number_of_wallets
        assert mock_wallet_repo.create.call_count == number_of_wallets
        mock_logger.info.assert_any_call("Successfully created 3 wallets")

    @pytest.mark.asyncio
    async def test_create_wallet_evm_service_error(
        self, wallet_use_cases, mock_evm_service, mock_logger
    ):
        """Test wallet creation fails when EVM service raises an error."""
        # Arrange
        mock_evm_service.create_wallet.side_effect = Exception("EVM service error")

        # Act & Assert
        with pytest.raises(BatchOperationError) as exc_info:
            await wallet_use_cases.create(1)

        assert "wallet creation" in str(exc_info.value)
        assert "EVM service error" in str(exc_info.value)
        mock_logger.error.assert_any_call(
            "EVM service error creating wallet: EVM service error"
        )
        mock_logger.error.assert_any_call(
            "Error in batch wallet creation: EVM service error during creating "
            "wallet: EVM service error"
        )

    @pytest.mark.asyncio
    async def test_create_wallet_database_error(
        self, wallet_use_cases, mock_wallet_repo, mock_evm_service, mock_logger
    ):
        """Test wallet creation fails when database raises an error."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet.key.hex.return_value = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_evm_service.create_wallet.return_value = mock_wallet
        mock_wallet_repo.create.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(BatchOperationError) as exc_info:
            await wallet_use_cases.create(1)

        assert "wallet creation" in str(exc_info.value)
        assert "Database error" in str(exc_info.value)
        mock_logger.error.assert_any_call(
            f"Database error creating wallet {mock_wallet.address}: Database error"
        )
        mock_logger.error.assert_any_call(
            "Error in batch wallet creation: Database error during creating "
            "wallet: Database error"
        )

    @pytest.mark.asyncio
    async def test_create_wallet_unexpected_error(
        self, wallet_use_cases, mock_wallet_repo, mock_evm_service, mock_logger
    ):
        """Test wallet creation fails when an unexpected error occurs."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet.key.hex.return_value = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_evm_service.create_wallet.return_value = mock_wallet
        mock_wallet_repo.create.side_effect = ValueError("Unexpected error")

        # Act & Assert
        with pytest.raises(BatchOperationError) as exc_info:
            await wallet_use_cases.create(1)

        assert "wallet creation" in str(exc_info.value)
        assert "Unexpected error" in str(exc_info.value)
        mock_logger.error.assert_any_call(
            f"Unexpected error creating wallet {mock_wallet.address}: Unexpected error"
        )
        mock_logger.error.assert_any_call(
            "Error in batch wallet creation: Failed to create wallet: "
            "Unexpected error"
        )

    @pytest.mark.asyncio
    async def test_create_wallet_batch_operation_error(
        self, wallet_use_cases, mock_evm_service, mock_logger
    ):
        """Test wallet creation fails when batch operation fails."""
        # Arrange
        mock_evm_service.create_wallet.side_effect = Exception("Batch error")

        # Act & Assert
        with pytest.raises(BatchOperationError) as exc_info:
            await wallet_use_cases.create(2)

        assert "wallet creation" in str(exc_info.value)
        assert "Batch error" in str(exc_info.value)
        mock_logger.error.assert_any_call(
            "EVM service error creating wallet: Batch error"
        )
        mock_logger.error.assert_any_call(
            "Error in batch wallet creation: EVM service error during creating "
            "wallet: Batch error"
        )

    @pytest.mark.asyncio
    async def test_get_all_success(
        self, wallet_use_cases, mock_wallet_repo, mock_logger, sample_db_wallet
    ):
        """Test successful retrieval of all wallets with pagination."""
        # Arrange
        page = 2
        limit = 10
        total_count = 25
        db_wallets = [sample_db_wallet] * 5

        mock_wallet_repo.get_all.return_value = db_wallets
        mock_wallet_repo.get_count.return_value = total_count

        # Act
        result = await wallet_use_cases.get_all(page=page, limit=limit)

        # Assert
        assert isinstance(result, WalletsPagination)
        assert len(result.wallets) == 5
        assert all(isinstance(wallet, Wallet) for wallet in result.wallets)
        assert result.pagination.total == total_count
        assert result.pagination.page == page
        assert result.pagination.next_page == 3
        assert result.pagination.prev_page == 1

        mock_wallet_repo.get_all.assert_called_once_with(offset=10, limit=10)
        mock_wallet_repo.get_count.assert_called_once()
        mock_logger.info.assert_any_call(
            f"Getting wallets with pagination: page={page}, limit={limit}"
        )
        mock_logger.info.assert_any_call("Successfully retrieved 5 of 25 wallets")

    @pytest.mark.asyncio
    async def test_get_all_first_page(
        self, wallet_use_cases, mock_wallet_repo, sample_db_wallet
    ):
        """Test pagination for first page."""
        # Arrange
        page = 1
        limit = 10
        total_count = 25
        db_wallets = [sample_db_wallet] * 10

        mock_wallet_repo.get_all.return_value = db_wallets
        mock_wallet_repo.get_count.return_value = total_count

        # Act
        result = await wallet_use_cases.get_all(page=page, limit=limit)

        # Assert
        assert result.pagination.prev_page is None
        assert result.pagination.next_page == 2

    @pytest.mark.asyncio
    async def test_get_all_last_page(
        self, wallet_use_cases, mock_wallet_repo, sample_db_wallet
    ):
        """Test pagination for last page."""
        # Arrange
        page = 3
        limit = 10
        total_count = 25
        db_wallets = [sample_db_wallet] * 5

        mock_wallet_repo.get_all.return_value = db_wallets
        mock_wallet_repo.get_count.return_value = total_count

        # Act
        result = await wallet_use_cases.get_all(page=page, limit=limit)

        # Assert
        assert result.pagination.next_page is None
        assert result.pagination.prev_page == 2

    @pytest.mark.asyncio
    async def test_get_all_invalid_page(self, wallet_use_cases, mock_logger):
        """Test get_all raises error for invalid page number."""
        # Act & Assert
        with pytest.raises(InvalidPaginationError) as exc_info:
            await wallet_use_cases.get_all(page=0, limit=10)

        assert "Page must be greater than 0" in str(exc_info.value)
        mock_logger.error.assert_called_with("Page must be greater than 0")

    @pytest.mark.asyncio
    async def test_get_all_invalid_limit(self, wallet_use_cases, mock_logger):
        """Test get_all raises error for invalid limit."""
        # Act & Assert
        with pytest.raises(InvalidPaginationError) as exc_info:
            await wallet_use_cases.get_all(page=1, limit=0)

        assert "Limit must be greater than 0" in str(exc_info.value)
        mock_logger.error.assert_called_with("Limit must be greater than 0")

    @pytest.mark.asyncio
    async def test_get_all_limit_too_high(self, wallet_use_cases, mock_logger):
        """Test get_all raises error for limit too high."""
        # Act & Assert
        with pytest.raises(InvalidPaginationError) as exc_info:
            await wallet_use_cases.get_all(page=1, limit=1001)

        assert "Limit must be less than 1000" in str(exc_info.value)
        mock_logger.error.assert_called_with("Limit must be less than 1000")

    @pytest.mark.asyncio
    async def test_get_all_database_error(
        self, wallet_use_cases, mock_wallet_repo, mock_logger
    ):
        """Test get_all raises error when database fails."""
        # Arrange
        mock_wallet_repo.get_all.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await wallet_use_cases.get_all()

        assert "getting wallets" in str(exc_info.value)
        assert "Database error" in str(exc_info.value)
        mock_logger.error.assert_called_with(
            "Database error getting wallets: Database error"
        )

    @pytest.mark.asyncio
    async def test_get_by_address_success(
        self, wallet_use_cases, mock_wallet_repo, mock_logger, sample_db_wallet
    ):
        """Test successful retrieval of wallet by address."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet_repo.get_by_address.return_value = sample_db_wallet

        # Act
        result = await wallet_use_cases.get_by_address(address)

        # Assert
        assert isinstance(result, Wallet)
        assert result.address == sample_db_wallet.address
        mock_wallet_repo.get_by_address.assert_called_once_with(address)
        mock_logger.info.assert_any_call(f"Getting wallet by address: {address}")
        mock_logger.info.assert_any_call(f"Successfully retrieved wallet: {address}")

    @pytest.mark.asyncio
    async def test_get_by_address_empty_address(self, wallet_use_cases, mock_logger):
        """Test get_by_address raises error for empty address."""
        # Act & Assert
        with pytest.raises(InvalidWalletAddressError) as exc_info:
            await wallet_use_cases.get_by_address("")

        assert "empty address" in str(exc_info.value)
        mock_logger.error.assert_called_with("Wallet address is required")

    @pytest.mark.asyncio
    async def test_get_by_address_whitespace_address(
        self, wallet_use_cases, mock_logger
    ):
        """Test get_by_address raises error for whitespace-only address."""
        # Act & Assert
        with pytest.raises(InvalidWalletAddressError) as exc_info:
            await wallet_use_cases.get_by_address("   ")

        assert "empty address" in str(exc_info.value)
        mock_logger.error.assert_called_with("Wallet address is required")

    @pytest.mark.asyncio
    async def test_get_by_address_database_error(
        self, wallet_use_cases, mock_wallet_repo, mock_logger
    ):
        """Test get_by_address raises error when database fails."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet_repo.get_by_address.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await wallet_use_cases.get_by_address(address)

        assert "getting wallet by address" in str(exc_info.value)
        assert "Database error" in str(exc_info.value)
        mock_logger.error.assert_called_with(
            f"Database error getting wallet {address}: Database error"
        )

    @pytest.mark.asyncio
    async def test_delete_wallet_success(
        self, wallet_use_cases, mock_wallet_repo, mock_logger, sample_db_wallet
    ):
        """Test successful deletion of wallet."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet_repo.delete.return_value = sample_db_wallet

        # Act
        result = await wallet_use_cases.delete_wallet(address)

        # Assert
        assert isinstance(result, Wallet)
        assert result.address == sample_db_wallet.address
        mock_wallet_repo.delete.assert_called_once_with(address)
        mock_logger.info.assert_any_call(f"Deleting wallet: {address}")
        mock_logger.info.assert_any_call(f"Successfully deleted wallet: {address}")

    @pytest.mark.asyncio
    async def test_delete_wallet_empty_address(self, wallet_use_cases, mock_logger):
        """Test delete_wallet raises error for empty address."""
        # Act & Assert
        with pytest.raises(InvalidWalletAddressError) as exc_info:
            await wallet_use_cases.delete_wallet("")

        assert "empty address" in str(exc_info.value)
        mock_logger.error.assert_called_with("Wallet address is required")

    @pytest.mark.asyncio
    async def test_delete_wallet_database_error(
        self, wallet_use_cases, mock_wallet_repo, mock_logger
    ):
        """Test delete_wallet raises error when database fails."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet_repo.delete.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await wallet_use_cases.delete_wallet(address)

        assert "deleting wallet" in str(exc_info.value)
        assert "Database error" in str(exc_info.value)
        mock_logger.error.assert_called_with(
            f"Database error deleting wallet {address}: Database error"
        )

    @pytest.mark.asyncio
    async def test_get_native_balance_success(
        self, wallet_use_cases, mock_evm_service, mock_logger
    ):
        """Test successful retrieval of native balance."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        expected_balance = 1.5
        mock_evm_service.get_wallet_balance.return_value = expected_balance

        # Act
        result = await wallet_use_cases.get_native_balance(address)

        # Assert
        assert result == expected_balance
        mock_evm_service.get_wallet_balance.assert_called_once_with(address)
        mock_logger.info.assert_any_call(f"Getting balance of wallet: {address}")
        mock_logger.info.assert_any_call(
            f"Successfully retrieved balance: {expected_balance}"
        )

    @pytest.mark.asyncio
    async def test_get_native_balance_empty_address(
        self, wallet_use_cases, mock_logger
    ):
        """Test get_native_balance raises error for empty address."""
        # Act & Assert
        with pytest.raises(InvalidWalletAddressError) as exc_info:
            await wallet_use_cases.get_native_balance("")

        assert "empty address" in str(exc_info.value)
        mock_logger.error.assert_called_with("Wallet address is required")

    @pytest.mark.asyncio
    async def test_get_native_balance_evm_service_error(
        self, wallet_use_cases, mock_evm_service, mock_logger
    ):
        """Test get_native_balance raises error when EVM service fails."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_evm_service.get_wallet_balance.side_effect = Exception("EVM service error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await wallet_use_cases.get_native_balance(address)

        assert "EVM service error" in str(exc_info.value)
        mock_logger.error.assert_called_with(
            "Unexpected error getting balance: EVM service error"
        )

    @pytest.mark.asyncio
    async def test_get_token_balance_success(
        self, wallet_use_cases, mock_evm_service, mock_assets_use_cases, mock_logger
    ):
        """Test successful retrieval of token balance."""
        # Arrange
        asset = "USDC"
        address = "0x1234567890abcdef1234567890abcdef12345678"
        asset_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        expected_balance = 100.0
        abi_name = "erc20"

        mock_assets_use_cases.get_asset_address.return_value = asset_address
        mock_evm_service.get_token_balance.return_value = expected_balance

        # Act
        result = await wallet_use_cases.get_token_balance(asset, address, abi_name)

        # Assert
        assert result == expected_balance
        mock_assets_use_cases.get_asset_address.assert_called_once_with(asset)
        mock_evm_service.get_token_balance.assert_called_once_with(
            address, asset_address, abi_name
        )
        mock_logger.info.assert_any_call(
            f"Getting token balance of wallet: {address} for asset: {asset}"
        )
        mock_logger.info.assert_any_call(
            f"Successfully retrieved token balance: {expected_balance}"
        )

    @pytest.mark.asyncio
    async def test_get_token_balance_default_abi(
        self, wallet_use_cases, mock_evm_service, mock_assets_use_cases, mock_logger
    ):
        """Test get_token_balance uses default abi_name when not specified."""
        # Arrange
        asset = "USDC"
        address = "0x1234567890abcdef1234567890abcdef12345678"
        asset_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        expected_balance = 100.0

        mock_assets_use_cases.get_asset_address.return_value = asset_address
        mock_evm_service.get_token_balance.return_value = expected_balance

        # Act
        result = await wallet_use_cases.get_token_balance(asset, address)

        # Assert
        assert result == expected_balance
        mock_evm_service.get_token_balance.assert_called_once_with(
            address, asset_address, "erc20"
        )

    @pytest.mark.asyncio
    async def test_get_token_balance_assets_service_error(
        self, wallet_use_cases, mock_assets_use_cases, mock_logger
    ):
        """Test get_token_balance raises error when assets service fails."""
        # Arrange
        asset = "USDC"
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_assets_use_cases.get_asset_address.side_effect = Exception(
            "Assets service error"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await wallet_use_cases.get_token_balance(asset, address)

        assert "Assets service error" in str(exc_info.value)
        mock_logger.error.assert_called_with(
            "Unexpected error getting token balance: Assets service error"
        )

    @pytest.mark.asyncio
    async def test_get_token_balance_evm_service_error(
        self, wallet_use_cases, mock_evm_service, mock_assets_use_cases, mock_logger
    ):
        """Test get_token_balance raises error when EVM service fails."""
        # Arrange
        asset = "USDC"
        address = "0x1234567890abcdef1234567890abcdef12345678"
        asset_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

        mock_assets_use_cases.get_asset_address.return_value = asset_address
        mock_evm_service.get_token_balance.side_effect = Exception("EVM service error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await wallet_use_cases.get_token_balance(asset, address)

        assert "EVM service error" in str(exc_info.value)
        mock_logger.error.assert_called_with(
            "Unexpected error getting token balance: EVM service error"
        )

    def test_concurrent_wallet_creation(
        self,
        wallet_use_cases,
        mock_wallet_repo,
        mock_evm_service,
        mock_logger,
        sample_db_wallet,
    ):
        """Test that multiple wallets are created concurrently."""
        # Arrange
        number_of_wallets = 5
        mock_wallets = []
        for i in range(number_of_wallets):
            mock_wallet = MagicMock()
            mock_wallet.address = f"0x1234567890abcdef1234567890abcdef1234567{i}"
            mock_wallet.key.hex.return_value = (
                f"0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef123456789{i}"
            )
            mock_wallets.append(mock_wallet)

        mock_evm_service.create_wallet.side_effect = mock_wallets
        mock_wallet_repo.create.return_value = sample_db_wallet

        # Act
        result = asyncio.run(wallet_use_cases.create(number_of_wallets))

        # Assert
        assert len(result) == number_of_wallets
        assert mock_evm_service.create_wallet.call_count == number_of_wallets
        assert mock_wallet_repo.create.call_count == number_of_wallets

    def test_pagination_calculation_edge_cases(
        self, wallet_use_cases, mock_wallet_repo, sample_db_wallet
    ):
        """Test pagination calculation for edge cases."""
        # Test exact division
        mock_wallet_repo.get_all.return_value = [sample_db_wallet] * 10
        mock_wallet_repo.get_count.return_value = 30

        result = asyncio.run(wallet_use_cases.get_all(page=3, limit=10))
        assert result.pagination.next_page is None
        assert result.pagination.prev_page == 2

        # Test remainder division
        mock_wallet_repo.get_count.return_value = 25
        result = asyncio.run(wallet_use_cases.get_all(page=3, limit=10))
        assert result.pagination.next_page is None
        assert result.pagination.prev_page == 2

    def test_wallet_model_conversion(self, sample_db_wallet):
        """Test Wallet model conversion from database model."""
        # Act
        wallet = Wallet.from_data(sample_db_wallet)

        # Assert
        assert wallet.id == sample_db_wallet.id
        assert wallet.address == sample_db_wallet.address
        assert wallet.private_key == sample_db_wallet.private_key
        assert wallet.status == sample_db_wallet.status
        assert wallet.created_at == sample_db_wallet.created_at
        assert wallet.updated_at == sample_db_wallet.updated_at
        assert wallet.deleted_at == sample_db_wallet.deleted_at

    def test_wallets_pagination_model(self, sample_wallet):
        """Test WalletsPagination model creation."""
        # Arrange
        pagination = Pagination(total=100, page=1, next_page=2, prev_page=None)
        wallets = [sample_wallet] * 3

        # Act
        result = WalletsPagination(pagination=pagination, wallets=wallets)

        # Assert
        assert result.pagination == pagination
        assert result.wallets == wallets
        assert len(result.wallets) == 3
