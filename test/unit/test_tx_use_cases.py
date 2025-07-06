"""
Unit tests for TransactionUseCases class.

This module contains unit tests for the TransactionUseCases class, which is responsible
for handling transaction-related business logic.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from eth_typing import HexAddress, HexStr
from web3.types import Wei

from app.data.database import Transaction as DBTransaction
from app.data.evm.main import EVMService
from app.domain.assets_use_cases import AssetsUseCases
from app.domain.enums import TransactionStatus, WalletStatus
from app.domain.errors import (DatabaseError, EmptyAddressError,
                               EmptyTransactionIdError, EVMServiceError,
                               InsufficientBalanceError, InvalidNetworkError,
                               InvalidPaginationError,
                               InvalidWalletPrivateKeyError, SameAddressError,
                               WalletNotFoundError)
from app.domain.tx_models import (CreateTx, Pagination, Transaction,
                                  TransactionsPagination)
from app.domain.tx_use_cases import TransactionUseCases
from app.domain.wallet_use_cases import WalletUseCases
from app.utils.config_manager import ConfigManager


class TestTransactionUseCases:
    """Test cases for TransactionUseCases class."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock ConfigManager for testing."""
        config_manager = MagicMock(spec=ConfigManager)
        config_manager.get_current_network.return_value = "ethereum"
        config_manager.get_networks.return_value = ["ethereum", "polygon"]
        config_manager.get_asset.return_value = {
            "ethereum": "0x1234567890123456789012345678901234567890"
        }
        return config_manager

    @pytest.fixture
    def mock_wallet_use_cases(self):
        """Create a mock WalletUseCases for testing."""
        wallet_use_cases = MagicMock(spec=WalletUseCases)
        wallet_use_cases.get_by_address = AsyncMock()
        wallet_use_cases.get_native_balance = AsyncMock()
        wallet_use_cases.get_token_balance = AsyncMock()
        return wallet_use_cases

    @pytest.fixture
    def mock_assets_use_cases(self):
        """Create a mock AssetsUseCases for testing."""
        assets_use_cases = MagicMock(spec=AssetsUseCases)
        assets_use_cases.is_native_asset.return_value = False
        return assets_use_cases

    @pytest.fixture
    def mock_evm_service(self):
        """Create a mock EVMService for testing."""
        evm_service = MagicMock(spec=EVMService)
        evm_service.send_transaction = MagicMock()
        evm_service.get_token_contract = MagicMock()
        evm_service.get_transaction_receipt = MagicMock()

        # Mock the w3 attribute
        mock_w3 = MagicMock()
        mock_eth = MagicMock()
        mock_w3.eth = mock_eth
        evm_service.w3 = mock_w3

        return evm_service

    @pytest.fixture
    def mock_tx_repo(self):
        """Create a mock TransactionRepository for testing."""
        repo = MagicMock()
        repo.create = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_tx_hash = AsyncMock()
        repo.get_by_wallet = AsyncMock()
        repo.get_all = AsyncMock()
        repo.get_count = AsyncMock()
        repo.get_count_by_wallet = AsyncMock()
        return repo

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        logger = MagicMock()
        logger.info = MagicMock()
        logger.error = MagicMock()
        return logger

    @pytest.fixture
    def transaction_use_cases(
        self,
        mock_config_manager,
        mock_wallet_use_cases,
        mock_assets_use_cases,
        mock_evm_service,
        mock_tx_repo,
        mock_logger,
    ):
        """Create a TransactionUseCases instance with mocked dependencies."""
        return TransactionUseCases(
            config_manager=mock_config_manager,
            wallet_use_cases=mock_wallet_use_cases,
            assets_use_cases=mock_assets_use_cases,
            evm_service=mock_evm_service,
            tx_repo=mock_tx_repo,
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
            "network": "ethereum",
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
    def sample_db_transaction(self, sample_transaction_data):
        """Create a sample DBTransaction instance."""
        return DBTransaction(**sample_transaction_data)

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

    def test_init(
        self,
        mock_config_manager,
        mock_wallet_use_cases,
        mock_assets_use_cases,
        mock_evm_service,
        mock_tx_repo,
        mock_logger,
    ):
        """Test TransactionUseCases initialization."""
        tx_use_cases = TransactionUseCases(
            config_manager=mock_config_manager,
            wallet_use_cases=mock_wallet_use_cases,
            assets_use_cases=mock_assets_use_cases,
            evm_service=mock_evm_service,
            tx_repo=mock_tx_repo,
            logger=mock_logger,
        )
        assert tx_use_cases.config_manager == mock_config_manager
        assert tx_use_cases.wallet_use_cases == mock_wallet_use_cases
        assert tx_use_cases.assets_use_cases == mock_assets_use_cases
        assert tx_use_cases.evm_service == mock_evm_service
        assert tx_use_cases.tx_repo == mock_tx_repo
        assert tx_use_cases.logger == mock_logger

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        transaction_use_cases,
        mock_config_manager,
        mock_wallet_use_cases,
        mock_assets_use_cases,
        mock_evm_service,
        mock_tx_repo,
        mock_logger,
        sample_create_tx,
        sample_db_transaction,
    ):
        """Test successful transaction creation."""
        # Arrange
        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = (
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )

        mock_wallet = MagicMock()
        mock_wallet.private_key = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_contract = MagicMock()
        mock_contract.functions.transfer.return_value.build_transaction.return_value = {
            "to": "0x1234567890abcdef1234567890abcdef1234567890",
            "data": "0x1234567890abcdef",
        }

        mock_wallet_use_cases.get_by_address.return_value = mock_wallet
        mock_wallet_use_cases.get_token_balance.return_value = 200.0
        mock_evm_service.send_transaction.return_value = mock_tx_hash
        mock_evm_service.get_token_contract.return_value = mock_contract
        mock_tx_repo.create.return_value = sample_db_transaction

        # Act
        result = await transaction_use_cases.create(sample_create_tx)

        # Assert
        assert isinstance(result, Transaction)
        assert result.tx_hash == sample_db_transaction.tx_hash
        mock_wallet_use_cases.get_by_address.assert_called_once_with(
            sample_create_tx.from_address
        )
        mock_wallet_use_cases.get_token_balance.assert_called_once_with(
            sample_create_tx.asset, sample_create_tx.from_address
        )
        mock_evm_service.send_transaction.assert_called_once()
        mock_tx_repo.create.assert_called_once()
        mock_logger.info.assert_any_call(
            f"Creating a new transaction for {sample_create_tx.asset}"
        )

    @pytest.mark.asyncio
    async def test_create_native_asset_success(
        self,
        transaction_use_cases,
        mock_config_manager,
        mock_wallet_use_cases,
        mock_assets_use_cases,
        mock_evm_service,
        mock_tx_repo,
        mock_logger,
        sample_db_transaction,
    ):
        """Test successful native asset transaction creation."""
        # Arrange
        create_tx = CreateTx(
            from_address=HexAddress(
                HexStr("0x1234567890abcdef1234567890abcdef12345678")
            ),
            to_address=HexAddress(HexStr("0xfedcba0987654321fedcba0987654321fedcba09")),
            asset="ETH",
            amount=1.5,
        )

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = (
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )

        mock_wallet = MagicMock()
        mock_wallet.private_key = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_assets_use_cases.is_native_asset.return_value = True
        mock_wallet_use_cases.get_by_address.return_value = mock_wallet
        mock_wallet_use_cases.get_native_balance.return_value = 5.0
        mock_evm_service.send_transaction.return_value = mock_tx_hash
        mock_tx_repo.create.return_value = sample_db_transaction

        # Act
        result = await transaction_use_cases.create(create_tx)

        # Assert
        assert isinstance(result, Transaction)
        mock_wallet_use_cases.get_native_balance.assert_called_once_with(
            create_tx.from_address
        )
        mock_evm_service.send_transaction.assert_called_once()
        # Verify TxParams for native asset
        call_args = mock_evm_service.send_transaction.call_args[0]
        tx_params = call_args[0]
        assert tx_params["to"] == create_tx.to_address
        assert tx_params["value"] == Wei(int(create_tx.amount * 10**18))

    @pytest.mark.asyncio
    async def test_create_invalid_network(
        self, transaction_use_cases, mock_config_manager, mock_logger, sample_create_tx
    ):
        """Test transaction creation fails with invalid network."""
        # Arrange
        mock_config_manager.get_current_network.return_value = "invalid_network"

        # Act & Assert
        with pytest.raises(InvalidNetworkError):
            await transaction_use_cases.create(sample_create_tx)

        mock_logger.error.assert_called_with("Network invalid_network not available")

    @pytest.mark.asyncio
    async def test_create_invalid_amount(self, transaction_use_cases, mock_logger):
        """Test transaction creation fails with invalid amount."""
        # Arrange
        # Test Pydantic validation directly
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            CreateTx(
                from_address=HexAddress(
                    HexStr("0x1234567890abcdef1234567890abcdef12345678")
                ),
                to_address=HexAddress(
                    HexStr("0xfedcba0987654321fedcba0987654321fedcba09")
                ),
                asset="USDC",
                amount=0.0,
            )

    @pytest.mark.asyncio
    async def test_create_same_address(self, transaction_use_cases, mock_logger):
        """Test transaction creation fails with same from and to addresses."""
        # Arrange
        create_tx = CreateTx(
            from_address=HexAddress(
                HexStr("0x1234567890abcdef1234567890abcdef12345678")
            ),
            to_address=HexAddress(HexStr("0x1234567890abcdef1234567890abcdef12345678")),
            asset="USDC",
            amount=100.0,
        )

        # Act & Assert
        with pytest.raises(SameAddressError):
            await transaction_use_cases.create(create_tx)

        mock_logger.error.assert_called_with(
            "From address and to address cannot be the same"
        )

    @pytest.mark.asyncio
    async def test_create_empty_from_address(self, transaction_use_cases, mock_logger):
        """Test transaction creation fails with empty from address."""
        # Arrange
        # This test is now handled by Pydantic validation
        # so we need to test the validation directly
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            CreateTx(
                from_address=HexAddress(HexStr("")),
                to_address=HexAddress(
                    HexStr("0xfedcba0987654321fedcba0987654321fedcba09")
                ),
                asset="USDC",
                amount=100.0,
            )

    @pytest.mark.asyncio
    async def test_create_empty_to_address(self, transaction_use_cases, mock_logger):
        """Test transaction creation fails with empty to address."""
        # Arrange
        # This test is now handled by Pydantic validation
        # so we need to test the validation directly
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            CreateTx(
                from_address=HexAddress(
                    HexStr("0x1234567890abcdef1234567890abcdef12345678")
                ),
                to_address=HexAddress(HexStr("")),
                asset="USDC",
                amount=100.0,
            )

    @pytest.mark.asyncio
    async def test_create_asset_not_supported_on_network(
        self,
        transaction_use_cases,
        mock_config_manager,
        mock_assets_use_cases,
        mock_logger,
        sample_create_tx,
    ):
        """Test transaction creation fails when asset is not supported on network."""
        # Arrange
        mock_config_manager.get_asset.return_value = {
            "polygon": "0x1234567890abcdef1234567890abcdef1234567890"
        }

        # Act & Assert
        with pytest.raises(EVMServiceError):
            await transaction_use_cases.create(sample_create_tx)

        mock_logger.error.assert_called_with(
            f"Unexpected error creating transaction: EVM service error during transfer: Unable to transfer {sample_create_tx.asset} on ethereum"
        )

    @pytest.mark.asyncio
    async def test_create_insufficient_balance(
        self,
        transaction_use_cases,
        mock_wallet_use_cases,
        mock_assets_use_cases,
        mock_logger,
        sample_create_tx,
    ):
        """Test transaction creation fails with insufficient balance."""
        # Arrange
        mock_wallet_use_cases.get_token_balance.return_value = 50.0

        # Act & Assert
        with pytest.raises(InsufficientBalanceError):
            await transaction_use_cases.create(sample_create_tx)

        mock_logger.error.assert_called_with("Insufficient balance for USDC")

    @pytest.mark.asyncio
    async def test_create_wallet_not_found(
        self,
        transaction_use_cases,
        mock_wallet_use_cases,
        mock_logger,
        sample_create_tx,
    ):
        """Test transaction creation fails when wallet not found."""
        # Arrange
        mock_wallet_use_cases.get_by_address.return_value = None
        # Set up the balance mock to return a value so the validation passes
        mock_wallet_use_cases.get_token_balance.return_value = 200.0

        # Act & Assert
        with pytest.raises(WalletNotFoundError):
            await transaction_use_cases.create(sample_create_tx)

        mock_logger.error.assert_called_with(
            f"Wallet {sample_create_tx.from_address} not found"
        )

    @pytest.mark.asyncio
    async def test_create_invalid_wallet_private_key(
        self,
        transaction_use_cases,
        mock_wallet_use_cases,
        mock_logger,
        sample_create_tx,
    ):
        """Test transaction creation fails when wallet has no private key."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.private_key = None
        mock_wallet_use_cases.get_by_address.return_value = mock_wallet
        # Set up the balance mock to return a value so the validation passes
        mock_wallet_use_cases.get_token_balance.return_value = 200.0

        # Act & Assert
        with pytest.raises(InvalidWalletPrivateKeyError):
            await transaction_use_cases.create(sample_create_tx)

        mock_logger.error.assert_called_with(
            f"Wallet {sample_create_tx.from_address} has no private key"
        )

    @pytest.mark.asyncio
    async def test_create_database_error(
        self,
        transaction_use_cases,
        mock_wallet_use_cases,
        mock_assets_use_cases,
        mock_evm_service,
        mock_tx_repo,
        mock_logger,
        sample_create_tx,
    ):
        """Test transaction creation fails with database error."""
        # Arrange
        mock_wallet = MagicMock()
        mock_wallet.private_key = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = (
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )

        mock_contract = MagicMock()
        mock_contract.functions.transfer.return_value.build_transaction.return_value = {
            "to": "0x1234567890abcdef1234567890abcdef1234567890",
            "data": "0x1234567890abcdef",
        }

        mock_wallet_use_cases.get_by_address.return_value = mock_wallet
        mock_wallet_use_cases.get_token_balance.return_value = 200.0
        mock_evm_service.send_transaction.return_value = mock_tx_hash
        mock_evm_service.get_token_contract.return_value = mock_contract
        mock_tx_repo.create.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError):
            await transaction_use_cases.create(sample_create_tx)

        mock_logger.error.assert_called_with(
            "Database error creating transaction: Database error"
        )

    @pytest.mark.asyncio
    async def test_validate_wallet_private_key_success(
        self, transaction_use_cases, mock_wallet_use_cases, mock_logger
    ):
        """Test successful wallet private key validation."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet = MagicMock()
        mock_wallet.private_key = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        mock_wallet_use_cases.get_by_address.return_value = mock_wallet

        # Act
        result = await transaction_use_cases._validate_wallet_private_key(address)

        # Assert
        assert result == mock_wallet.private_key
        mock_wallet_use_cases.get_by_address.assert_called_once_with(address)
        mock_logger.info.assert_any_call(
            f"Wallet {address} exists and has a valid private key"
        )

    @pytest.mark.asyncio
    async def test_validate_wallet_private_key_wallet_not_found(
        self, transaction_use_cases, mock_wallet_use_cases, mock_logger
    ):
        """Test wallet private key validation fails when wallet not found."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet_use_cases.get_by_address.return_value = None

        # Act & Assert
        with pytest.raises(WalletNotFoundError):
            await transaction_use_cases._validate_wallet_private_key(address)

        mock_logger.error.assert_called_with(f"Wallet {address} not found")

    @pytest.mark.asyncio
    async def test_validate_wallet_private_key_no_private_key(
        self, transaction_use_cases, mock_wallet_use_cases, mock_logger
    ):
        """Test wallet private key validation fails when wallet has no private key."""
        # Arrange
        address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_wallet = MagicMock()
        mock_wallet.private_key = None
        mock_wallet_use_cases.get_by_address.return_value = mock_wallet

        # Act & Assert
        with pytest.raises(InvalidWalletPrivateKeyError):
            await transaction_use_cases._validate_wallet_private_key(address)

        mock_logger.error.assert_called_with(f"Wallet {address} has no private key")

    def test_create_tx_params_token_asset(
        self,
        transaction_use_cases,
        mock_assets_use_cases,
        mock_evm_service,
        sample_create_tx,
    ):
        """Test creating transaction parameters for token asset."""
        # Arrange
        mock_assets_use_cases.is_native_asset.return_value = False
        current_network = "ethereum"
        asset_config = {"ethereum": "0x1234567890abcdef1234567890abcdef1234567890"}

        mock_contract = MagicMock()
        mock_contract.functions.transfer.return_value.build_transaction.return_value = {
            "to": "0x1234567890abcdef1234567890abcdef1234567890",
            "data": "0x1234567890abcdef",
        }
        mock_evm_service.get_token_contract.return_value = mock_contract

        # Act
        _ = transaction_use_cases._create_tx_params(
            sample_create_tx, current_network, asset_config
        )

        # Assert
        mock_evm_service.get_token_contract.assert_called_once_with(
            HexAddress(HexStr(asset_config[current_network]))
        )
        mock_contract.functions.transfer.assert_called_once_with(
            sample_create_tx.to_address, sample_create_tx.amount * 10**18
        )

    @pytest.mark.asyncio
    async def test_validate_balance_native_asset_success(
        self,
        transaction_use_cases,
        mock_assets_use_cases,
        mock_wallet_use_cases,
        mock_logger,
    ):
        """Test successful balance validation for native asset."""
        # Arrange
        asset = "ETH"
        from_address = "0x1234567890abcdef1234567890abcdef12345678"
        amount = 1.5

        mock_assets_use_cases.is_native_asset.return_value = True
        mock_wallet_use_cases.get_native_balance.return_value = 5.0

        # Act
        await transaction_use_cases.validate_balance(asset, from_address, amount)

        # Assert
        mock_wallet_use_cases.get_native_balance.assert_called_once_with(from_address)
        mock_logger.info.assert_called_with(
            f"Validating user balance for transaction"
            f" of {asset} from {from_address} with amount {amount}"
        )

    @pytest.mark.asyncio
    async def test_validate_balance_token_asset_success(
        self,
        transaction_use_cases,
        mock_assets_use_cases,
        mock_wallet_use_cases,
        mock_logger,
    ):
        """Test successful balance validation for token asset."""
        # Arrange
        asset = "USDC"
        from_address = "0x1234567890abcdef1234567890abcdef12345678"
        amount = 100.0

        mock_assets_use_cases.is_native_asset.return_value = False
        mock_wallet_use_cases.get_token_balance.return_value = 200.0

        # Act
        await transaction_use_cases.validate_balance(asset, from_address, amount)

        # Assert
        mock_wallet_use_cases.get_token_balance.assert_called_once_with(
            asset, from_address
        )

    @pytest.mark.asyncio
    async def test_validate_balance_insufficient_balance(
        self,
        transaction_use_cases,
        mock_assets_use_cases,
        mock_wallet_use_cases,
        mock_logger,
    ):
        """Test balance validation fails with insufficient balance."""
        # Arrange
        asset = "USDC"
        from_address = "0x1234567890abcdef1234567890abcdef12345678"
        amount = 100.0

        mock_assets_use_cases.is_native_asset.return_value = False
        mock_wallet_use_cases.get_token_balance.return_value = 50.0

        # Act & Assert
        with pytest.raises(InsufficientBalanceError):
            await transaction_use_cases.validate_balance(asset, from_address, amount)

        mock_logger.error.assert_called_with("Insufficient balance for USDC")

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self, transaction_use_cases, mock_tx_repo, mock_logger, sample_db_transaction
    ):
        """Test successful transaction retrieval by ID."""
        # Arrange
        transaction_id = uuid4()
        mock_tx_repo.get_by_id.return_value = sample_db_transaction

        # Act
        result = await transaction_use_cases.get_by_id(transaction_id)

        # Assert
        assert isinstance(result, Transaction)
        assert result.id == sample_db_transaction.id
        mock_tx_repo.get_by_id.assert_called_once_with(transaction_id)
        mock_logger.info.assert_called_with(
            f"Getting transaction by ID {transaction_id}"
        )

    @pytest.mark.asyncio
    async def test_get_by_id_empty_id(self, transaction_use_cases, mock_logger):
        """Test transaction retrieval fails with empty ID."""
        # Arrange
        transaction_id = ""

        # Act & Assert
        with pytest.raises(EmptyTransactionIdError):
            await transaction_use_cases.get_by_id(transaction_id)

        mock_logger.error.assert_called_with("Transaction ID is required")

    @pytest.mark.asyncio
    async def test_get_by_id_database_error(
        self, transaction_use_cases, mock_tx_repo, mock_logger
    ):
        """Test transaction retrieval fails with database error."""
        # Arrange
        transaction_id = uuid4()
        mock_tx_repo.get_by_id.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError):
            await transaction_use_cases.get_by_id(transaction_id)

        mock_logger.error.assert_called_with(
            f"Database error getting transaction {transaction_id}: Database error"
        )

    @pytest.mark.asyncio
    async def test_get_by_tx_hash_success(
        self, transaction_use_cases, mock_tx_repo, mock_logger, sample_db_transaction
    ):
        """Test successful transaction retrieval by hash."""
        # Arrange
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        mock_tx_repo.get_by_tx_hash.return_value = sample_db_transaction

        # Act
        result = await transaction_use_cases.get_by_tx_hash(tx_hash)

        # Assert
        assert isinstance(result, Transaction)
        assert result.tx_hash == sample_db_transaction.tx_hash
        mock_tx_repo.get_by_tx_hash.assert_called_once_with(tx_hash)
        mock_logger.info.assert_called_with(f"Getting transaction by hash {tx_hash}")

    @pytest.mark.asyncio
    async def test_get_by_tx_hash_empty_hash(self, transaction_use_cases, mock_logger):
        """Test transaction retrieval fails with empty hash."""
        # Arrange
        tx_hash = ""

        # Act & Assert
        with pytest.raises(EmptyAddressError):
            await transaction_use_cases.get_by_tx_hash(tx_hash)

        mock_logger.error.assert_called_with("Transaction hash is required")

    @pytest.mark.asyncio
    async def test_get_by_tx_hash_database_error(
        self, transaction_use_cases, mock_tx_repo, mock_evm_service, mock_logger
    ):
        """Test transaction retrieval fails with database error."""
        # Arrange
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        mock_tx_repo.get_by_tx_hash.side_effect = RuntimeError("Database error")
        mock_evm_service.get_transaction_receipt.side_effect = Exception(
            "Blockchain error"
        )

        # Act & Assert
        with pytest.raises(Exception):
            await transaction_use_cases.get_by_tx_hash(tx_hash)

        mock_logger.error.assert_any_call(
            f"Database error getting transaction by hash {tx_hash}: Database error"
        )

    @pytest.mark.asyncio
    async def test_get_txs_success(
        self, transaction_use_cases, mock_tx_repo, mock_logger, sample_db_transaction
    ):
        """Test successful transaction retrieval for wallet."""
        # Arrange
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        page = 1
        limit = 10
        mock_tx_repo.get_by_wallet.return_value = [sample_db_transaction]
        mock_tx_repo.get_count_by_wallet.return_value = 1

        # Act
        result = await transaction_use_cases.get_txs(wallet_address, page, limit)

        # Assert
        assert isinstance(result, TransactionsPagination)
        assert len(result.transactions) == 1
        assert result.pagination.page == page
        assert result.pagination.total == 1
        mock_tx_repo.get_by_wallet.assert_called_once_with(
            wallet_address, offset=0, limit=limit
        )
        mock_tx_repo.get_count_by_wallet.assert_called_once_with(wallet_address)
        mock_logger.info.assert_any_call(
            f"Getting all transactions for wallet {wallet_address}"
            f"from page {page} with limit {limit}"
        )
        mock_logger.info.assert_any_call(
            f"Successfully retrieved 1 of 1 txs for wallet {wallet_address}"
        )

    @pytest.mark.asyncio
    async def test_get_txs_empty_address(self, transaction_use_cases, mock_logger):
        """Test transaction retrieval fails with empty wallet address."""
        # Arrange
        wallet_address = ""

        # Act & Assert
        with pytest.raises(EmptyAddressError):
            await transaction_use_cases.get_txs(wallet_address)

        mock_logger.error.assert_called_with("Wallet address is required")

    @pytest.mark.asyncio
    async def test_get_txs_invalid_page(self, transaction_use_cases, mock_logger):
        """Test transaction retrieval fails with invalid page."""
        # Arrange
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        page = 0

        # Act & Assert
        with pytest.raises(InvalidPaginationError):
            await transaction_use_cases.get_txs(wallet_address, page)

        mock_logger.error.assert_called_with("Page must be greater than 0")

    @pytest.mark.asyncio
    async def test_get_txs_invalid_limit(self, transaction_use_cases, mock_logger):
        """Test transaction retrieval fails with invalid limit."""
        # Arrange
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        limit = 0

        # Act & Assert
        with pytest.raises(InvalidPaginationError):
            await transaction_use_cases.get_txs(wallet_address, limit=limit)

        mock_logger.error.assert_called_with("Limit must be greater than 0")

    @pytest.mark.asyncio
    async def test_get_txs_database_error(
        self, transaction_use_cases, mock_tx_repo, mock_logger
    ):
        """Test transaction retrieval fails with database error."""
        # Arrange
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        mock_tx_repo.get_by_wallet.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError):
            await transaction_use_cases.get_txs(wallet_address)

        mock_logger.error.assert_called_with(
            f"Database error getting txs for wallet {wallet_address}: Database error"
        )

    @pytest.mark.asyncio
    async def test_get_all_success(
        self, transaction_use_cases, mock_tx_repo, mock_logger, sample_db_transaction
    ):
        """Test successful retrieval of all transactions."""
        # Arrange
        page = 1
        limit = 10
        mock_tx_repo.get_all.return_value = [sample_db_transaction]
        mock_tx_repo.get_count.return_value = 1

        # Act
        result = await transaction_use_cases.get_all(page, limit)

        # Assert
        assert isinstance(result, TransactionsPagination)
        assert len(result.transactions) == 1
        assert result.pagination.page == page
        assert result.pagination.total == 1
        mock_tx_repo.get_all.assert_called_once_with(offset=0, limit=limit)
        mock_tx_repo.get_count.assert_called_once()
        mock_logger.info.assert_any_call(
            f"Getting all transactions from page {page} with limit {limit}"
        )
        mock_logger.info.assert_any_call("Successfully retrieved 1 of 1 txs")

    @pytest.mark.asyncio
    async def test_get_all_invalid_page(self, transaction_use_cases, mock_logger):
        """Test retrieval fails with invalid page."""
        # Arrange
        page = 0

        # Act & Assert
        with pytest.raises(InvalidPaginationError):
            await transaction_use_cases.get_all(page)

        mock_logger.error.assert_called_with("Page must be greater than 0")

    @pytest.mark.asyncio
    async def test_get_all_invalid_limit(self, transaction_use_cases, mock_logger):
        """Test retrieval fails with invalid limit."""
        # Arrange
        limit = 0

        # Act & Assert
        with pytest.raises(InvalidPaginationError):
            await transaction_use_cases.get_all(limit=limit)

        mock_logger.error.assert_called_with("Limit must be greater than 0")

    @pytest.mark.asyncio
    async def test_get_all_limit_too_high(self, transaction_use_cases, mock_logger):
        """Test retrieval fails with limit too high."""
        # Arrange
        limit = 1001

        # Act & Assert
        with pytest.raises(InvalidPaginationError):
            await transaction_use_cases.get_all(limit=limit)

        mock_logger.error.assert_called_with("Limit must be less than 1000")

    @pytest.mark.asyncio
    async def test_get_all_database_error(
        self, transaction_use_cases, mock_tx_repo, mock_logger
    ):
        """Test retrieval fails with database error."""
        # Arrange
        mock_tx_repo.get_all.side_effect = RuntimeError("Database error")

        # Act & Assert
        with pytest.raises(DatabaseError):
            await transaction_use_cases.get_all()

        mock_logger.error.assert_called_with(
            "Database error getting all transactions: Database error"
        )

    def test_pagination_calculation_edge_cases(
        self, transaction_use_cases, mock_tx_repo, sample_db_transaction
    ):
        """Test pagination calculation edge cases."""
        # Test first page with no previous
        mock_tx_repo.get_all.return_value = [sample_db_transaction]
        mock_tx_repo.get_count.return_value = 1
        result = asyncio.run(transaction_use_cases.get_all(page=1, limit=10))
        assert result.pagination.prev_page is None
        # With 1 transaction and limit 10,
        # we're on the only page, so next_page should be None
        assert result.pagination.next_page is None

        # Test last page with no next
        mock_tx_repo.get_all.return_value = []
        mock_tx_repo.get_count.return_value = (
            5  # 5 total transactions, page 2 with limit 10
        )
        result = asyncio.run(transaction_use_cases.get_all(page=2, limit=10))
        assert result.pagination.prev_page == 1
        assert result.pagination.next_page is None

    def test_transaction_model_conversion(self, sample_db_transaction):
        """Test transaction model conversion from database to domain."""
        # Act
        result = Transaction.from_data(sample_db_transaction)

        # Assert
        assert result.id == sample_db_transaction.id
        assert result.tx_hash == sample_db_transaction.tx_hash
        assert result.asset == sample_db_transaction.asset
        assert result.from_address == sample_db_transaction.from_address
        assert result.to_address == sample_db_transaction.to_address
        assert result.amount == sample_db_transaction.amount
        assert result.gas_price == sample_db_transaction.gas_price
        assert result.gas_limit == sample_db_transaction.gas_limit
        assert result.status == sample_db_transaction.status
        assert result.created_at == sample_db_transaction.created_at
        assert result.updated_at == sample_db_transaction.updated_at

    def test_transactions_pagination_model(self, sample_db_transaction):
        """Test transactions pagination model creation."""
        # Arrange
        transactions = [Transaction.from_data(sample_db_transaction)]
        pagination = Pagination(total=1, page=1, next_page=2, prev_page=None)

        # Act
        result = TransactionsPagination(
            transactions=transactions, pagination=pagination
        )

        # Assert
        assert len(result.transactions) == 1
        assert result.pagination.total == 1
        assert result.pagination.page == 1
        assert result.pagination.next_page == 2
        assert result.pagination.prev_page is None

    @pytest.mark.asyncio
    async def test_validate_transaction_empty_hash(
        self, transaction_use_cases, mock_logger
    ):
        """Test transaction validation fails with empty hash."""
        # Act & Assert
        with pytest.raises(EmptyAddressError):
            await transaction_use_cases.validate_transaction("")

        mock_logger.error.assert_called_with("Transaction hash is required")

    @pytest.mark.asyncio
    async def test_validate_transaction_success(
        self,
        transaction_use_cases,
        mock_evm_service,
        mock_wallet_use_cases,
        mock_logger,
    ):
        """Test successful transaction validation."""
        # Arrange
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        # Mock transaction receipt
        mock_receipt = {"status": 1, "logs": []}

        # Mock transaction details
        mock_tx = {
            "to": "0xabcdef1234567890abcdef1234567890abcdef12",
            "from": "0x1234567890abcdef1234567890abcdef12345678",
            "value": 1000000000000000000,  # 1 ETH in wei
            "input": "0x",
            "gasPrice": 20000000000,
            "gas": 21000,
        }

        mock_evm_service.get_transaction_receipt.return_value = mock_receipt
        mock_evm_service.w3.eth.get_transaction.return_value = mock_tx

        # Mock wallet validation
        mock_wallet_use_cases.get_by_address.return_value = MagicMock()

        # Act
        result = await transaction_use_cases.validate_transaction(tx_hash)

        # Assert
        assert result.is_valid is True
        assert result.transaction_hash == tx_hash
        assert len(result.transfers) == 1
        assert result.transfers[0].asset == "ETH"
        assert result.transfers[0].amount == 1.0
        assert (
            result.transfers[0].destination_address
            == "0xabcdef1234567890abcdef1234567890abcdef12"
        )
        assert "Valid ETH transfer" in result.validation_message

    @pytest.mark.asyncio
    async def test_validate_transaction_failed_status(
        self, transaction_use_cases, mock_evm_service, mock_logger
    ):
        """Test transaction validation with failed status."""
        # Arrange
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        # Mock failed transaction receipt
        mock_receipt = {"status": 0, "logs": []}

        mock_evm_service.get_transaction_receipt.return_value = mock_receipt

        # Act
        result = await transaction_use_cases.validate_transaction(tx_hash)

        # Assert
        assert result.is_valid is False
        assert result.transaction_hash == tx_hash
        assert len(result.transfers) == 0
        assert "Transaction failed or was reverted" in result.validation_message

    @pytest.mark.asyncio
    async def test_validate_transaction_invalid_destination(
        self,
        transaction_use_cases,
        mock_evm_service,
        mock_wallet_use_cases,
        mock_logger,
    ):
        """Test transaction validation with invalid destination address."""
        # Arrange
        tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

        # Mock transaction receipt
        mock_receipt = {"status": 1, "logs": []}

        # Mock transaction details
        mock_tx = {
            "to": "0xabcdef1234567890abcdef1234567890abcdef12",
            "from": "0x1234567890abcdef1234567890abcdef12345678",
            "value": 1000000000000000000,  # 1 ETH in wei
            "input": "0x",
            "gasPrice": 20000000000,
            "gas": 21000,
        }

        mock_evm_service.get_transaction_receipt.return_value = mock_receipt
        mock_evm_service.w3.eth.get_transaction.return_value = mock_tx

        # Mock wallet validation failure
        mock_wallet_use_cases.get_by_address.side_effect = Exception("Wallet not found")

        # Act
        result = await transaction_use_cases.validate_transaction(tx_hash)

        # Assert
        assert result.is_valid is False
        assert result.transaction_hash == tx_hash
        assert len(result.transfers) == 0
        assert "is not one of our addresses" in result.validation_message
