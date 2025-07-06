"""
Integration tests for TransactionUseCases class.

This module contains integration tests for the TransactionUseCases class, which test
the interaction between different components of the system.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from eth_typing import HexAddress, HexStr

from app.data.database import Transaction as DBTransaction
from app.domain.assets_use_cases import AssetsUseCases
from app.domain.enums import TransactionStatus, WalletStatus
from app.domain.errors import (DatabaseError, InsufficientBalanceError,
                               InvalidPaginationError,
                               InvalidWalletPrivateKeyError,
                               WalletNotFoundError)
from app.domain.tx_models import CreateTx, Transaction, TransactionsPagination
from app.domain.tx_use_cases import TransactionUseCases
from app.domain.wallet_use_cases import WalletUseCases
from app.utils.config_manager import ConfigManager


class TestTransactionUseCasesIntegration:
    """Integration test cases for TransactionUseCases class."""

    @pytest.fixture
    def real_config_manager(self):
        """Create a real ConfigManager instance for testing."""
        config_manager = ConfigManager()
        # Override the current network to use a supported network
        config_manager.config["current_network"] = "ETHEREUM"
        # Ensure native asset is set correctly
        config_manager.config["native_asset"] = "ETH"
        return config_manager

    @pytest.fixture
    def real_wallet_use_cases(
        self,
        mock_wallet_repository,
        mock_evm_service,
        mock_assets_use_cases,
        mock_logger,
    ):
        """Create a real WalletUseCases instance with mocked dependencies."""
        wallet_use_cases = WalletUseCases(
            wallet_repo=mock_wallet_repository,
            evm_service=mock_evm_service,
            assets_use_cases=mock_assets_use_cases,
            logger=mock_logger,
        )
        # Ensure the mock methods return proper values instead of coroutines
        mock_wallet_repository.get_token_balance = AsyncMock(return_value=200.0)
        mock_wallet_repository.get_native_balance = AsyncMock(return_value=5.0)
        return wallet_use_cases

    @pytest.fixture
    def real_assets_use_cases(self, real_config_manager, mock_logger):
        """Create a real AssetsUseCases instance."""
        return AssetsUseCases(config_manager=real_config_manager, logger=mock_logger)

    @pytest.fixture
    def real_evm_service(self, mock_logger):
        """Create a real EVMService instance."""
        # Mock the EVMService to avoid real ABI loading and web3 interactions
        with patch("app.data.evm.main.EVMService") as mock_evm_service_class:
            mock_evm_service = MagicMock()
            mock_evm_service_class.return_value = mock_evm_service
            mock_evm_service.abis = {"erc20": []}  # Mock ABIs
            mock_evm_service.get_abi.return_value = []
            mock_evm_service.list_available_abis.return_value = ["erc20"]
            mock_evm_service.get_token_contract.return_value = MagicMock()
            mock_evm_service.get_token_balance.return_value = 100.0
            mock_evm_service.get_wallet_balance.return_value = 5.0
            mock_evm_service.create_wallet.return_value = MagicMock()
            mock_evm_service.sign_transaction.return_value = MagicMock()
            mock_evm_service.send_transaction.return_value = MagicMock()
            mock_evm_service.get_transaction_receipt.return_value = MagicMock()
            mock_evm_service.get_nonce.return_value = 0
            mock_evm_service.logger = mock_logger
            return mock_evm_service

    @pytest.fixture
    def real_tx_repo(self, mock_transaction_repository):
        """Create a mock TransactionRepository instance for testing."""
        return mock_transaction_repository

    @pytest.fixture
    def transaction_use_cases_integration(
        self,
        real_config_manager,
        real_wallet_use_cases,
        real_assets_use_cases,
        real_evm_service,
        real_tx_repo,
        mock_logger,
    ):
        """Create a TransactionUseCases instance with real dependencies."""
        return TransactionUseCases(
            config_manager=real_config_manager,
            wallet_use_cases=real_wallet_use_cases,
            assets_use_cases=real_assets_use_cases,
            evm_service=real_evm_service,
            tx_repo=real_tx_repo,
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
    def sample_transaction_data(self):
        """Create sample transaction data for testing."""
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        return {
            "id": uuid4(),
            "tx_hash": tx_hash,
            "asset": "USDC",
            "network": "ETHEREUM",
            "from_address": "0x1234567890abcdef1234567890abcdef12345678",
            "to_address": "0xfedcba0987654321fedcba0987654321fedcba09",
            "amount": 100.0,
            "gas_price": 20000000000,
            "gas_limit": 21000,
            "status": TransactionStatus.PENDING,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    @pytest.fixture
    def sample_create_tx(self):
        """Create a sample CreateTx instance."""
        return CreateTx(
            from_address=HexAddress(
                HexStr("0x1234567890abcdef1234567890abcdef12345678")
            ),
            to_address=HexAddress(HexStr("0xfedcba0987654321fedcba0987654321fedcba09")),
            asset="USDC",
            amount=100.0,
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_transaction_full_integration(
        self,
        transaction_use_cases_integration,
        mock_wallet_repository,
        real_evm_service,
        mock_transaction_repository,
        sample_create_tx,
        sample_wallet_data,
        sample_transaction_data,
    ):
        """Test full integration of transaction creation process."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.private_key = sample_wallet_data["private_key"]

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = sample_transaction_data["tx_hash"]

        # Create a proper wallet object instead of dict
        from app.domain.wallet_models import Wallet

        wallet_obj = Wallet(
            id=sample_wallet_data["id"],
            address=sample_wallet_data["address"],
            private_key=sample_wallet_data["private_key"],
            status=sample_wallet_data["status"],
            created_at=sample_wallet_data["created_at"],
            updated_at=sample_wallet_data["updated_at"],
            deleted_at=sample_wallet_data["deleted_at"],
        )
        mock_wallet_repository.get_by_address.return_value = wallet_obj
        transaction_use_cases_integration.wallet_use_cases.get_token_balance = (
            AsyncMock(return_value=200.0)
        )
        # Patch contract.functions.transfer to return a mock with build_transaction
        mock_transfer = MagicMock()
        mock_transfer.build_transaction.return_value = {
            "to": sample_wallet_data["address"],
            "data": "0x1234567890abcdef",
        }
        mock_contract = MagicMock()
        mock_contract.functions.transfer.return_value = mock_transfer
        real_evm_service.get_token_contract.return_value = mock_contract
        real_evm_service.send_transaction.return_value = mock_tx_hash
        db_transaction = DBTransaction(**sample_transaction_data)
        mock_transaction_repository.create.return_value = db_transaction

        # Act
        result = await transaction_use_cases_integration.create(sample_create_tx)

        # Assert
        assert isinstance(result, Transaction)
        assert result.tx_hash == sample_transaction_data["tx_hash"]
        assert result.asset == sample_create_tx.asset
        assert result.from_address == sample_create_tx.from_address
        assert result.to_address == sample_create_tx.to_address
        assert result.amount == sample_create_tx.amount

        # Verify all components were called correctly
        mock_wallet_repository.get_by_address.assert_called_once_with(
            sample_create_tx.from_address
        )
        transaction_use_cases_integration.wallet_use_cases.get_token_balance.assert_called_once_with(
            sample_create_tx.asset, sample_create_tx.from_address
        )
        real_evm_service.send_transaction.assert_called_once()
        mock_transaction_repository.create.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_native_asset_integration(
        self,
        transaction_use_cases_integration,
        mock_wallet_repository,
        mock_transaction_repository,
        mock_logger,
        sample_wallet_data,
        sample_transaction_data,
    ):
        """Test integration of native asset transaction creation."""
        # Arrange
        create_tx = CreateTx(
            from_address=HexAddress(
                HexStr("0x1234567890abcdef1234567890abcdef12345678")
            ),
            to_address=HexAddress(HexStr("0xfedcba0987654321fedcba0987654321fedcba09")),
            asset="ETH",
            amount=1.5,
        )

        mock_wallet = MagicMock()
        mock_wallet.private_key = sample_wallet_data["private_key"]

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = sample_transaction_data["tx_hash"]

        # Create a proper wallet object instead of dict
        from app.domain.wallet_models import Wallet

        wallet_obj = Wallet(
            id=sample_wallet_data["id"],
            address=sample_wallet_data["address"],
            private_key=sample_wallet_data["private_key"],
            status=sample_wallet_data["status"],
            created_at=sample_wallet_data["created_at"],
            updated_at=sample_wallet_data["updated_at"],
            deleted_at=sample_wallet_data["deleted_at"],
        )
        mock_wallet_repository.get_by_address.return_value = wallet_obj
        transaction_use_cases_integration.wallet_use_cases.get_native_balance = (
            AsyncMock(return_value=5.0)
        )
        transaction_use_cases_integration.evm_service.send_transaction.return_value = (
            mock_tx_hash
        )

        # Create transaction data with ETH asset instead of USDC
        eth_transaction_data = sample_transaction_data.copy()
        eth_transaction_data["asset"] = "ETH"
        eth_transaction_data["amount"] = 1.5
        db_transaction = DBTransaction(**eth_transaction_data)
        mock_transaction_repository.create.return_value = db_transaction

        # Act
        result = await transaction_use_cases_integration.create(create_tx)

        # Assert
        assert isinstance(result, Transaction)
        assert result.tx_hash == sample_transaction_data["tx_hash"]
        assert result.asset == create_tx.asset
        assert result.from_address == create_tx.from_address
        assert result.to_address == create_tx.to_address
        assert result.amount == create_tx.amount

        # Verify native balance was checked
        transaction_use_cases_integration.wallet_use_cases.get_native_balance.assert_called_once_with(
            create_tx.from_address
        )
        transaction_use_cases_integration.evm_service.send_transaction.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transaction_retrieval_integration(
        self,
        transaction_use_cases_integration,
        mock_transaction_repository,
        mock_logger,
        sample_transaction_data,
    ):
        """Test integration of transaction retrieval operations."""
        # Arrange
        transaction_id = uuid4()
        tx_hash = sample_transaction_data["tx_hash"]
        wallet_address = sample_transaction_data["from_address"]

        db_transaction = DBTransaction(**sample_transaction_data)
        db_transaction.id = (
            transaction_id  # Ensure the returned transaction has the expected ID
        )
        mock_transaction_repository.get_by_id.return_value = db_transaction
        mock_transaction_repository.get_by_tx_hash.return_value = db_transaction
        mock_transaction_repository.get_by_wallet.return_value = [db_transaction]
        mock_transaction_repository.get_all.return_value = [db_transaction]

        # Act - Test get_by_id
        result_by_id = await transaction_use_cases_integration.get_by_id(transaction_id)

        # Act - Test get_by_tx_hash
        result_by_hash = await transaction_use_cases_integration.get_by_tx_hash(tx_hash)

        # Act - Test get_txs
        result_txs = await transaction_use_cases_integration.get_txs(wallet_address)

        # Act - Test get_all
        result_all = await transaction_use_cases_integration.get_all()

        # Assert
        assert isinstance(result_by_id, Transaction)
        assert result_by_id.id == transaction_id
        assert result_by_id.tx_hash == tx_hash

        assert isinstance(result_by_hash, Transaction)
        assert result_by_hash.tx_hash == tx_hash

        assert isinstance(result_txs, TransactionsPagination)
        assert len(result_txs.transactions) == 1
        assert result_txs.transactions[0].tx_hash == tx_hash

        assert isinstance(result_all, TransactionsPagination)
        assert len(result_all.transactions) == 1
        assert result_all.transactions[0].tx_hash == tx_hash

        # Verify repository calls
        mock_transaction_repository.get_by_id.assert_called_once_with(transaction_id)
        mock_transaction_repository.get_by_tx_hash.assert_called_once_with(tx_hash)
        mock_transaction_repository.get_by_wallet.assert_called_once()
        mock_transaction_repository.get_all.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(
        self,
        transaction_use_cases_integration,
        mock_wallet_repository,
        mock_evm_service,
        mock_transaction_repository,
        mock_logger,
        sample_create_tx,
        sample_wallet_data,
    ):
        """Test integration of error handling across components."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.private_key = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = (
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )

        # Create a proper wallet object instead of dict
        from app.domain.wallet_models import Wallet

        wallet_obj = Wallet(
            id=sample_wallet_data["id"],
            address=sample_wallet_data["address"],
            private_key=sample_wallet_data["private_key"],
            status=sample_wallet_data["status"],
            created_at=sample_wallet_data["created_at"],
            updated_at=sample_wallet_data["updated_at"],
            deleted_at=sample_wallet_data["deleted_at"],
        )
        mock_wallet_repository.get_by_address.return_value = wallet_obj
        transaction_use_cases_integration.wallet_use_cases.get_token_balance = (
            AsyncMock(return_value=200.0)
        )
        # Patch contract.functions.transfer to return a mock with build_transaction
        mock_transfer = MagicMock()
        mock_transfer.build_transaction.return_value = {
            "to": sample_wallet_data["address"],
            "data": "0x1234567890abcdef",
        }
        mock_contract = MagicMock()
        mock_contract.functions.transfer.return_value = mock_transfer
        mock_evm_service.get_token_contract.return_value = mock_contract
        mock_transaction_repository.create.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError):
            await transaction_use_cases_integration.create(sample_create_tx)

        mock_logger.error.assert_called_with(
            "Database error creating transaction: Database error"
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pagination_integration(
        self,
        transaction_use_cases_integration,
        mock_transaction_repository,
        sample_transaction_data,
    ):
        """Test integration of pagination functionality."""
        # Arrange
        db_transaction = DBTransaction(**sample_transaction_data)
        mock_transaction_repository.get_by_wallet.return_value = [db_transaction]
        mock_transaction_repository.get_all.return_value = [db_transaction]

        # Act
        result_wallet = await transaction_use_cases_integration.get_txs(
            sample_transaction_data["from_address"], page=1, limit=10
        )
        result_all = await transaction_use_cases_integration.get_all(page=1, limit=10)

        # Assert
        assert isinstance(result_wallet, TransactionsPagination)
        assert result_wallet.pagination.page == 1
        assert result_wallet.pagination.total == 1
        assert len(result_wallet.transactions) == 1

        assert isinstance(result_all, TransactionsPagination)
        assert result_all.pagination.page == 1
        assert result_all.pagination.total == 1
        assert len(result_all.transactions) == 1

        # Verify pagination parameters
        mock_transaction_repository.get_by_wallet.assert_called_once_with(
            sample_transaction_data["from_address"], offset=0, limit=10
        )
        mock_transaction_repository.get_all.assert_called_once_with(offset=0, limit=10)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_balance_validation_integration(
        self,
        transaction_use_cases_integration,
        real_wallet_use_cases,
        real_assets_use_cases,
    ):
        """Test integration of balance validation functionality."""
        # Arrange
        asset = "USDC"
        from_address = "0x1234567890abcdef1234567890abcdef12345678"
        amount = 100.0

        # Mock the wallet use cases methods
        real_wallet_use_cases.get_token_balance = AsyncMock(return_value=200.0)
        real_assets_use_cases.is_native_asset = MagicMock(return_value=False)

        # Act
        await transaction_use_cases_integration.validate_balance(
            asset, from_address, amount
        )

        # Assert
        real_wallet_use_cases.get_token_balance.assert_called_once_with(
            asset, from_address
        )

        # Test insufficient balance
        real_wallet_use_cases.get_token_balance = AsyncMock(return_value=50.0)

        with pytest.raises(InsufficientBalanceError):
            await transaction_use_cases_integration.validate_balance(
                asset, from_address, amount
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_wallet_private_key_validation_integration(
        self,
        transaction_use_cases_integration,
        real_wallet_use_cases,
        mock_logger,
    ):
        """Test integration of wallet private key validation."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet = MagicMock()
        mock_wallet.private_key = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        # Mock the wallet use cases method
        real_wallet_use_cases.get_by_address = AsyncMock(return_value=mock_wallet)

        # Act
        result = await transaction_use_cases_integration._validate_wallet_private_key(
            address
        )

        # Assert
        assert result == mock_wallet.private_key
        real_wallet_use_cases.get_by_address.assert_called_once_with(address)

        # Test wallet not found
        real_wallet_use_cases.get_by_address = AsyncMock(return_value=None)

        with pytest.raises(WalletNotFoundError):
            await transaction_use_cases_integration._validate_wallet_private_key(
                address
            )

        # Test wallet with no private key
        mock_wallet_no_key = MagicMock()
        mock_wallet_no_key.private_key = None
        real_wallet_use_cases.get_by_address = AsyncMock(
            return_value=mock_wallet_no_key
        )

        with pytest.raises(InvalidWalletPrivateKeyError):
            await transaction_use_cases_integration._validate_wallet_private_key(
                address
            )

    @pytest.mark.integration
    def test_transaction_parameters_creation_integration(
        self,
        transaction_use_cases_integration,
        real_evm_service,
        real_assets_use_cases,
        sample_create_tx,
    ):
        """Test integration of transaction parameters creation."""
        # Arrange
        current_network = "ETHEREUM"
        asset_config = {"ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"}

        mock_contract = MagicMock()
        mock_contract.functions.transfer.return_value.build_transaction.return_value = {
            "to": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "data": "0x1234567890abcdef",
        }

        # Mock the EVM service method
        real_evm_service.get_token_contract = MagicMock(return_value=mock_contract)
        real_assets_use_cases.is_native_asset = MagicMock(return_value=False)

        # Act
        result = transaction_use_cases_integration._create_tx_params(
            sample_create_tx, current_network, asset_config
        )

        # Assert
        assert "to" in result
        assert "data" in result
        real_evm_service.get_token_contract.assert_called_once()
        mock_contract.functions.transfer.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_transaction_operations(
        self,
        transaction_use_cases_integration,
        mock_wallet_repository,
        mock_transaction_repository,
        sample_create_tx,
        sample_wallet_data,
        sample_transaction_data,
    ):
        """Test integration of concurrent transaction operations."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.private_key = sample_wallet_data["private_key"]

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = sample_transaction_data["tx_hash"]

        # Create a proper wallet object instead of dict
        from app.domain.wallet_models import Wallet

        wallet_obj = Wallet(
            id=sample_wallet_data["id"],
            address=sample_wallet_data["address"],
            private_key=sample_wallet_data["private_key"],
            status=sample_wallet_data["status"],
            created_at=sample_wallet_data["created_at"],
            updated_at=sample_wallet_data["updated_at"],
            deleted_at=sample_wallet_data["deleted_at"],
        )
        mock_wallet_repository.get_by_address.return_value = wallet_obj
        transaction_use_cases_integration.wallet_use_cases.get_token_balance = (
            AsyncMock(return_value=200.0)
        )
        # Patch contract.functions.transfer to return a mock with build_transaction
        mock_transfer = MagicMock()
        mock_transfer.build_transaction.return_value = {
            "to": sample_wallet_data["address"],
            "data": "0x1234567890abcdef",
        }
        mock_contract = MagicMock()
        mock_contract.functions.transfer.return_value = mock_transfer
        transaction_use_cases_integration.evm_service.get_token_contract.return_value = (
            mock_contract
        )
        transaction_use_cases_integration.evm_service.send_transaction.return_value = (
            mock_tx_hash
        )
        db_transaction = DBTransaction(**sample_transaction_data)
        mock_transaction_repository.create.return_value = db_transaction

        # Act - Create multiple concurrent transactions
        tasks = [
            transaction_use_cases_integration.create(sample_create_tx) for _ in range(3)
        ]
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 3
        for result in results:
            assert isinstance(result, Transaction)
            assert result.tx_hash == sample_transaction_data["tx_hash"]

        # Verify all components were called the expected number of times
        assert mock_wallet_repository.get_by_address.call_count == 3
        assert (
            transaction_use_cases_integration.wallet_use_cases.get_token_balance.call_count
            == 3
        )
        assert (
            transaction_use_cases_integration.evm_service.send_transaction.call_count
            == 3
        )
        assert mock_transaction_repository.create.call_count == 3

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transaction_lifecycle_integration(
        self,
        transaction_use_cases_integration,
        mock_wallet_repository,
        mock_transaction_repository,
        mock_logger,
        sample_create_tx,
        sample_wallet_data,
        sample_transaction_data,
    ):
        """Test integration of complete transaction lifecycle."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.private_key = sample_wallet_data["private_key"]

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = sample_transaction_data["tx_hash"]

        # Create a proper wallet object instead of dict
        from app.domain.wallet_models import Wallet

        wallet_obj = Wallet(
            id=sample_wallet_data["id"],
            address=sample_wallet_data["address"],
            private_key=sample_wallet_data["private_key"],
            status=sample_wallet_data["status"],
            created_at=sample_wallet_data["created_at"],
            updated_at=sample_wallet_data["updated_at"],
            deleted_at=sample_wallet_data["deleted_at"],
        )
        mock_wallet_repository.get_by_address.return_value = wallet_obj
        transaction_use_cases_integration.wallet_use_cases.get_token_balance = (
            AsyncMock(return_value=200.0)
        )
        # Patch contract.functions.transfer to return a mock with build_transaction
        mock_transfer = MagicMock()
        mock_transfer.build_transaction.return_value = {
            "to": sample_wallet_data["address"],
            "data": "0x1234567890abcdef",
        }
        mock_contract = MagicMock()
        mock_contract.functions.transfer.return_value = mock_transfer
        transaction_use_cases_integration.evm_service.get_token_contract.return_value = (
            mock_contract
        )
        transaction_use_cases_integration.evm_service.send_transaction.return_value = (
            mock_tx_hash
        )
        db_transaction = DBTransaction(**sample_transaction_data)
        mock_transaction_repository.create.return_value = db_transaction
        mock_transaction_repository.get_by_id.return_value = db_transaction
        mock_transaction_repository.get_by_tx_hash.return_value = db_transaction

        # Act - Create transaction
        created_tx = await transaction_use_cases_integration.create(sample_create_tx)

        # Act - Retrieve by ID
        retrieved_by_id = await transaction_use_cases_integration.get_by_id(
            created_tx.id
        )

        # Act - Retrieve by hash
        retrieved_by_hash = await transaction_use_cases_integration.get_by_tx_hash(
            created_tx.tx_hash
        )

        # Assert
        assert isinstance(created_tx, Transaction)
        assert created_tx.tx_hash == sample_transaction_data["tx_hash"]
        assert created_tx.asset == sample_create_tx.asset

        assert isinstance(retrieved_by_id, Transaction)
        assert retrieved_by_id.id == created_tx.id
        assert retrieved_by_id.tx_hash == created_tx.tx_hash

        assert isinstance(retrieved_by_hash, Transaction)
        assert retrieved_by_hash.tx_hash == created_tx.tx_hash

        # Verify the complete flow
        mock_wallet_repository.get_by_address.assert_called_once_with(
            sample_create_tx.from_address
        )
        transaction_use_cases_integration.wallet_use_cases.get_token_balance.assert_called_once_with(
            sample_create_tx.asset, sample_create_tx.from_address
        )
        transaction_use_cases_integration.evm_service.send_transaction.assert_called_once()
        mock_transaction_repository.create.assert_called_once()
        mock_transaction_repository.get_by_id.assert_called_once_with(created_tx.id)
        mock_transaction_repository.get_by_tx_hash.assert_called_once_with(
            created_tx.tx_hash
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_propagation_integration(
        self,
        transaction_use_cases_integration,
        mock_wallet_repository,
        mock_transaction_repository,
        mock_logger,
        sample_create_tx,
        sample_wallet_data,
    ):
        """Test integration of error propagation across components."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.private_key = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        # Create a proper wallet object instead of dict for the first case
        from app.data.database import Wallet as DBWallet
        from app.domain.errors import WalletNotFoundError
        from app.domain.wallet_models import Wallet

        _ = Wallet(
            id=sample_wallet_data["id"],
            address=sample_wallet_data["address"],
            private_key=sample_wallet_data["private_key"],
            status=sample_wallet_data["status"],
            created_at=sample_wallet_data["created_at"],
            updated_at=sample_wallet_data["updated_at"],
            deleted_at=sample_wallet_data["deleted_at"],
        )

        # Set up the repository mock that's used by the wallet use cases
        db_wallet = DBWallet(**sample_wallet_data)
        mock_wallet_repository.get_by_address.return_value = db_wallet

        # Set up insufficient balance for first test
        transaction_use_cases_integration.wallet_use_cases.get_token_balance = (
            AsyncMock(return_value=50.0)
        )  # Less than the 100.0 amount in sample_create_tx

        # Act & Assert - Test insufficient balance error
        with pytest.raises(InsufficientBalanceError):
            await transaction_use_cases_integration.create(sample_create_tx)

        # Arrange - Test wallet not found error
        mock_wallet_repository.get_by_address.side_effect = WalletNotFoundError(
            "address: test"
        )
        transaction_use_cases_integration.wallet_use_cases.get_token_balance = (
            AsyncMock(return_value=200.0)
        )

        # Act & Assert
        with pytest.raises(WalletNotFoundError):
            await transaction_use_cases_integration.create(sample_create_tx)

        # Arrange - Test invalid private key error
        _ = Wallet(
            id=sample_wallet_data["id"],
            address=sample_wallet_data["address"],
            private_key=None,
            status=sample_wallet_data["status"],
            created_at=sample_wallet_data["created_at"],
            updated_at=sample_wallet_data["updated_at"],
            deleted_at=sample_wallet_data["deleted_at"],
        )
        # Create a DBWallet with empty private key
        db_wallet_no_key = DBWallet(**sample_wallet_data)
        db_wallet_no_key.private_key = ""  # Empty string instead of None
        mock_wallet_repository.get_by_address.return_value = db_wallet_no_key
        mock_wallet_repository.get_by_address.side_effect = None  # Reset side_effect
        transaction_use_cases_integration.wallet_use_cases.get_token_balance = (
            AsyncMock(return_value=200.0)
        )

        # Act & Assert
        with pytest.raises(InvalidWalletPrivateKeyError):
            await transaction_use_cases_integration.create(sample_create_tx)

    @pytest.mark.integration
    def test_config_manager_integration(
        self,
        transaction_use_cases_integration,
        real_config_manager,
    ):
        """Test integration with ConfigManager."""
        # Act
        current_network = real_config_manager.get_current_network()
        networks = real_config_manager.get_networks()
        asset_config = real_config_manager.get_asset("USDC")

        # Assert
        assert current_network == "ETHEREUM"
        assert "ETHEREUM" in networks
        assert "ETHEREUM" in asset_config
        assert asset_config["ETHEREUM"] == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pagination_edge_cases_integration(
        self,
        transaction_use_cases_integration,
        mock_transaction_repository,
        sample_transaction_data,
    ):
        """Test integration of pagination edge cases."""
        # Arrange
        db_transaction = DBTransaction(**sample_transaction_data)

        # Test first page with results
        mock_transaction_repository.get_all.return_value = [db_transaction]

        # Act
        result_first_page = await transaction_use_cases_integration.get_all(
            page=1, limit=10
        )

        # Assert
        assert result_first_page.pagination.page == 1
        assert result_first_page.pagination.prev_page is None
        assert result_first_page.pagination.next_page is None  # Only one result

        # Test second page with no results
        mock_transaction_repository.get_all.return_value = []

        # Act
        result_second_page = await transaction_use_cases_integration.get_all(
            page=2, limit=10
        )

        # Assert
        assert result_second_page.pagination.page == 2
        assert result_second_page.pagination.prev_page == 1
        assert result_second_page.pagination.next_page is None
        assert len(result_second_page.transactions) == 0

        # Test invalid pagination parameters
        with pytest.raises(InvalidPaginationError, match="Page must be greater than 0"):
            await transaction_use_cases_integration.get_all(page=0)

        with pytest.raises(
            InvalidPaginationError, match="Limit must be greater than 0"
        ):
            await transaction_use_cases_integration.get_all(limit=0)
