"""
Integration tests for WalletUseCases class.

This module contains integration tests for the WalletUseCases class, testing
the integration between all dependencies including the database, EVM service,
and assets use cases.
"""

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
from app.utils.config_manager import ConfigManager


class TestWalletUseCasesIntegration:
    """Integration test cases for WalletUseCases class."""

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
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = MagicMock()
        logger.info = MagicMock()
        logger.error = MagicMock()
        return logger

    @pytest.fixture
    def assets_use_cases(self, mock_config_manager, mock_logger):
        """Create a mock AssetsUseCases instance for testing."""
        assets_use_cases = MagicMock(spec=AssetsUseCases)
        assets_use_cases.get_asset_address = MagicMock()
        return assets_use_cases

    @pytest.fixture
    def wallet_use_cases(
        self, mock_wallet_repo, mock_evm_service, assets_use_cases, mock_logger
    ):
        """Create a WalletUseCases instance with real and mocked dependencies."""
        return WalletUseCases(
            wallet_repo=mock_wallet_repo,
            evm_service=mock_evm_service,
            assets_use_cases=assets_use_cases,
            logger=mock_logger,
        )

    @pytest.fixture
    def sample_wallet_data(self):
        """Create sample wallet data for testing."""
        return {
            "id": uuid4(),
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "private_key": (
                "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
            ),
            "status": WalletStatus.ACTIVE,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted_at": None,
        }

    @pytest.fixture
    def sample_db_wallet(self, sample_wallet_data):
        """Create a sample DBWallet instance."""
        return DBWallet(**sample_wallet_data)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_wallet_full_integration(
        self,
        wallet_use_cases,
        mock_wallet_repo,
        mock_evm_service,
        mock_logger,
        sample_db_wallet,
    ):
        """Test full integration of wallet creation process."""
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
        assert result[0].private_key == sample_db_wallet.private_key
        assert result[0].status == sample_db_wallet.status

        # Verify all dependencies were called correctly
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_multiple_wallets_full_integration(
        self,
        wallet_use_cases,
        mock_wallet_repo,
        mock_evm_service,
        mock_logger,
        sample_db_wallet,
    ):
        """Test full integration of multiple wallet creation process."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_all_wallets_full_integration(
        self, wallet_use_cases, mock_wallet_repo, mock_logger, sample_db_wallet
    ):
        """Test full integration of getting all wallets with pagination."""
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

        # Verify database calls
        mock_wallet_repo.get_all.assert_called_once_with(offset=10, limit=10)
        mock_wallet_repo.get_count.assert_called_once()

        # Verify logging
        mock_logger.info.assert_any_call(
            f"Getting wallets with pagination: page={page}, limit={limit}"
        )
        mock_logger.info.assert_any_call("Successfully retrieved 5 of 25 wallets")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_wallet_by_address_full_integration(
        self, wallet_use_cases, mock_wallet_repo, mock_logger, sample_db_wallet
    ):
        """Test full integration of getting wallet by address."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet_repo.get_by_address.return_value = sample_db_wallet

        # Act
        result = await wallet_use_cases.get_by_address(address)

        # Assert
        assert isinstance(result, Wallet)
        assert result.address == sample_db_wallet.address
        assert result.private_key == sample_db_wallet.private_key
        assert result.status == sample_db_wallet.status

        # Verify database call
        mock_wallet_repo.get_by_address.assert_called_once_with(address)

        # Verify logging
        mock_logger.info.assert_any_call(f"Getting wallet by address: {address}")
        mock_logger.info.assert_any_call(f"Successfully retrieved wallet: {address}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_wallet_full_integration(
        self, wallet_use_cases, mock_wallet_repo, mock_logger, sample_db_wallet
    ):
        """Test full integration of wallet deletion."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet_repo.delete.return_value = sample_db_wallet

        # Act
        result = await wallet_use_cases.delete_wallet(address)

        # Assert
        assert isinstance(result, Wallet)
        assert result.address == sample_db_wallet.address
        assert result.private_key == sample_db_wallet.private_key
        assert result.status == sample_db_wallet.status

        # Verify database call
        mock_wallet_repo.delete.assert_called_once_with(address)

        # Verify logging
        mock_logger.info.assert_any_call(f"Deleting wallet: {address}")
        mock_logger.info.assert_any_call(f"Successfully deleted wallet: {address}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_native_balance_full_integration(
        self, wallet_use_cases, mock_evm_service, mock_logger
    ):
        """Test full integration of getting native balance."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        expected_balance = 1.5
        mock_evm_service.get_wallet_balance.return_value = expected_balance

        # Act
        result = await wallet_use_cases.get_native_balance(address)

        # Assert
        assert result == expected_balance

        # Verify EVM service call
        mock_evm_service.get_wallet_balance.assert_called_once_with(address)

        # Verify logging
        mock_logger.info.assert_any_call(f"Getting balance of wallet: {address}")
        mock_logger.info.assert_any_call(
            f"Successfully retrieved balance: {expected_balance}"
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_token_balance_full_integration(
        self, wallet_use_cases, mock_evm_service, assets_use_cases, mock_logger
    ):
        """Test full integration of getting token balance."""
        # Arrange
        asset = "USDC"
        address = "0x1234567890abcdef1234567890abcdef12345678"
        asset_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        expected_balance = 100.0
        abi_name = "erc20"

        assets_use_cases.get_asset_address.return_value = asset_address
        mock_evm_service.get_token_balance.return_value = expected_balance

        # Act
        result = await wallet_use_cases.get_token_balance(asset, address, abi_name)

        # Assert
        assert result == expected_balance

        # Verify assets use cases call
        assets_use_cases.get_asset_address.assert_called_once_with(asset)

        # Verify EVM service call
        mock_evm_service.get_token_balance.assert_called_once_with(
            address, asset_address, abi_name
        )

        # Verify logging
        mock_logger.info.assert_any_call(
            f"Getting token balance of wallet: {address} for asset: {asset}"
        )
        mock_logger.info.assert_any_call(
            f"Successfully retrieved token balance: {expected_balance}"
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_propagation_evm_service_failure(
        self, wallet_use_cases, mock_evm_service, mock_logger
    ):
        """Test error propagation when EVM service fails during wallet creation."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_propagation_database_failure(
        self, wallet_use_cases, mock_wallet_repo, mock_evm_service, mock_logger
    ):
        """Test error propagation when database fails during wallet creation."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_propagation_assets_service_failure(
        self, wallet_use_cases, assets_use_cases, mock_logger
    ):
        """Test error propagation when assets service fails during token balance
        retrieval."""
        # Arrange
        asset = "INVALID_ASSET"
        address = "0x1234567890abcdef1234567890abcdef12345678"

        # Mock assets use cases to raise an error
        assets_use_cases.get_asset_address.side_effect = Exception("Asset not found")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await wallet_use_cases.get_token_balance(asset, address)

        assert "Asset not found" in str(exc_info.value)
        mock_logger.error.assert_called_with(
            "Unexpected error getting token balance: Asset not found"
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(
        self,
        wallet_use_cases,
        mock_wallet_repo,
        mock_evm_service,
        mock_logger,
        sample_db_wallet,
    ):
        """Test concurrent operations work correctly in integration."""
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
        result = await wallet_use_cases.create(number_of_wallets)

        # Assert
        assert len(result) == number_of_wallets
        assert mock_evm_service.create_wallet.call_count == number_of_wallets
        assert mock_wallet_repo.create.call_count == number_of_wallets

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pagination_edge_cases_integration(
        self, wallet_use_cases, mock_wallet_repo, sample_db_wallet
    ):
        """Test pagination edge cases in integration."""
        # Test first page
        mock_wallet_repo.get_all.return_value = [sample_db_wallet] * 10
        mock_wallet_repo.get_count.return_value = 25

        result = await wallet_use_cases.get_all(page=1, limit=10)
        assert result.pagination.prev_page is None
        assert result.pagination.next_page == 2

        # Test last page
        mock_wallet_repo.get_all.return_value = [sample_db_wallet] * 5
        result = await wallet_use_cases.get_all(page=3, limit=10)
        assert result.pagination.next_page is None
        assert result.pagination.prev_page == 2

        # Test single page
        mock_wallet_repo.get_count.return_value = 5
        result = await wallet_use_cases.get_all(page=1, limit=10)
        assert result.pagination.next_page is None
        assert result.pagination.prev_page is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_validation_integration(self, wallet_use_cases, mock_logger):
        """Test validation rules in integration."""
        # Test invalid page
        with pytest.raises(InvalidPaginationError) as exc_info:
            await wallet_use_cases.get_all(page=0, limit=10)
        assert "Page must be greater than 0" in str(exc_info.value)

        # Test invalid limit
        with pytest.raises(InvalidPaginationError) as exc_info:
            await wallet_use_cases.get_all(page=1, limit=0)
        assert "Limit must be greater than 0" in str(exc_info.value)

        # Test limit too high
        with pytest.raises(InvalidPaginationError) as exc_info:
            await wallet_use_cases.get_all(page=1, limit=1001)
        assert "Limit must be less than 1000" in str(exc_info.value)

        # Test empty address
        with pytest.raises(InvalidWalletAddressError) as exc_info:
            await wallet_use_cases.get_by_address("")
        assert "empty address" in str(exc_info.value)

        # Test whitespace address
        with pytest.raises(InvalidWalletAddressError) as exc_info:
            await wallet_use_cases.get_by_address("   ")
        assert "empty address" in str(exc_info.value)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_logging_integration(
        self,
        wallet_use_cases,
        mock_wallet_repo,
        mock_evm_service,
        mock_logger,
        sample_db_wallet,
    ):
        """Test logging behavior in integration."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet.key.hex.return_value = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_evm_service.create_wallet.return_value = mock_wallet
        mock_wallet_repo.create.return_value = sample_db_wallet

        # Act
        await wallet_use_cases.create(1)

        # Assert logging calls
        mock_logger.info.assert_any_call("Creating wallet")
        mock_logger.info.assert_any_call(
            f"Successfully created wallet: {mock_wallet.address}"
        )
        mock_logger.info.assert_any_call("Successfully created 1 wallets")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_model_conversion_integration(self, sample_db_wallet):
        """Test model conversion in integration."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pagination_model_integration(self, sample_db_wallet):
        """Test pagination model creation in integration."""
        # Arrange
        pagination = Pagination(total=100, page=1, next_page=2, prev_page=None)
        wallets = [Wallet.from_data(sample_db_wallet)] * 3

        # Act
        result = WalletsPagination(pagination=pagination, wallets=wallets)

        # Assert
        assert result.pagination == pagination
        assert len(result.wallets) == 3
        assert all(isinstance(wallet, Wallet) for wallet in result.wallets)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_operation_error_integration(
        self, wallet_use_cases, mock_evm_service, mock_logger
    ):
        """Test batch operation error handling in integration."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_error_integration(
        self, wallet_use_cases, mock_wallet_repo, mock_logger
    ):
        """Test database error handling in integration."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_evm_service_error_integration(
        self, wallet_use_cases, mock_evm_service, mock_logger
    ):
        """Test EVM service error handling in integration."""
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
