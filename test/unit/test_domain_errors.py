"""Tests for custom error classes."""

import pytest

from app.domain.errors import (AssetNotFoundError, AssetsError,
                               BatchOperationError, BusinessRuleError,
                               ConfigurationError)
from app.domain.errors import DatabaseError
from app.domain.errors import DatabaseError as WalletDatabaseError
from app.domain.errors import (DomainError, EmptyAddressError,
                               EmptyTransactionIdError)
from app.domain.errors import EVMServiceError
from app.domain.errors import EVMServiceError as WalletEVMServiceError
from app.domain.errors import (InsufficientBalanceError, InvalidAddressError,
                               InvalidAmountError, InvalidInputError,
                               InvalidNetworkError)
from app.domain.errors import InvalidPaginationError
from app.domain.errors import \
    InvalidPaginationError as WalletInvalidPaginationError
from app.domain.errors import (InvalidTxAssetError, InvalidWalletAddressError,
                               InvalidWalletPrivateKeyError, NotFoundError,
                               SameAddressError, TransactionError,
                               TransactionNotFoundError, ValidationError,
                               WalletCreationError, WalletError,
                               WalletNotFoundError)


class TestDomainErrors:
    """Test shared domain errors."""

    def test_domain_error_base(self):
        """Test base domain error."""
        error = DomainError("Test error")
        assert str(error) == "Test error"

    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Invalid field", "email")
        assert str(error) == "Invalid field"
        assert error.field == "email"

    def test_not_found_error(self):
        """Test not found error."""
        error = NotFoundError("User", "123")
        assert str(error) == "User with identifier 123 not found"
        assert error.resource_type == "User"
        assert error.identifier == "123"

    def test_invalid_input_error(self):
        """Test invalid input error."""
        error = InvalidInputError("Invalid email format", "email")
        assert str(error) == "Invalid email format"
        assert error.field == "email"

    def test_business_rule_error(self):
        """Test business rule error."""
        error = BusinessRuleError("Insufficient balance", "min_balance")
        assert str(error) == "Insufficient balance"
        assert error.rule == "min_balance"

    def test_configuration_error(self):
        """Test configuration error."""
        error = ConfigurationError("Missing API key", "api_key")
        assert str(error) == "Missing API key"
        assert error.config_key == "api_key"


class TestTransactionErrors:
    """Test transaction-specific errors."""

    def test_transaction_error_base(self):
        """Test base transaction error."""
        error = TransactionError("Transaction failed")
        assert str(error) == "Transaction failed"

    def test_invalid_asset_error(self):
        """Test invalid asset error."""
        error = InvalidTxAssetError("BTC", "Ethereum")
        assert str(error) == "Unable to trade 'BTC' on our current network 'Ethereum'"
        assert error.asset == "BTC"
        assert error.network == "Ethereum"

    def test_invalid_amount_error(self):
        """Test invalid amount error."""
        error = InvalidAmountError(-10.0)
        assert str(error) == "Amount must be greater than 0, got -10.0"
        assert error.amount == -10.0

    def test_same_address_error(self):
        """Test same address error."""
        error = SameAddressError("0x123")
        assert str(error) == "From address and to address cannot be the same: 0x123"
        assert error.address == "0x123"

    def test_empty_address_error(self):
        """Test empty address error."""
        error = EmptyAddressError("From")
        assert str(error) == "From address cannot be empty"
        assert error.address_type == "From"

    def test_transaction_not_found_error(self):
        """Test transaction not found error."""
        error = TransactionNotFoundError("abc123", "hash")
        assert str(error) == "Transaction with hash abc123 not found"
        assert error.identifier == "abc123"
        assert error.identifier_type == "hash"

    def test_invalid_pagination_error(self):
        """Test invalid pagination error."""
        error = InvalidPaginationError("Page must be positive")
        assert str(error) == "Page must be positive"

    def test_database_error(self):
        """Test database error."""
        error = DatabaseError("creating transaction", "Connection failed")
        assert (
            str(error)
            == "Database error during creating transaction: Connection failed"
        )
        assert error.operation == "creating transaction"
        assert error.details == "Connection failed"

    def test_evm_service_error(self):
        """Test EVM service error."""
        error = EVMServiceError("transfer", "Gas limit exceeded")
        assert str(error) == "EVM service error during transfer: Gas limit exceeded"
        assert error.operation == "transfer"
        assert error.details == "Gas limit exceeded"


class TestWalletErrors:
    """Test wallet-specific errors."""

    def test_wallet_error_base(self):
        """Test base wallet error."""
        error = WalletError("Wallet operation failed")
        assert str(error) == "Wallet operation failed"

    def test_invalid_wallet_address_error(self):
        """Test invalid wallet address error."""
        error = InvalidWalletAddressError("invalid_address")
        assert str(error) == "Invalid wallet address: invalid_address"
        assert error.address == "invalid_address"

    def test_wallet_not_found_error(self):
        """Test wallet not found error."""
        error = WalletNotFoundError("0x456")
        assert str(error) == "Wallet with address 0x456 not found"
        assert error.address == "0x456"

    def test_wallet_creation_error(self):
        """Test wallet creation error."""
        error = WalletCreationError("Private key generation failed")
        assert str(error) == "Failed to create wallet: Private key generation failed"
        assert error.details == "Private key generation failed"

    def test_batch_operation_error(self):
        """Test batch operation error."""
        error = BatchOperationError("wallet creation", "Network timeout")
        assert str(error) == "Batch wallet creation failed: Network timeout"
        assert error.operation == "wallet creation"
        assert error.details == "Network timeout"

    def test_wallet_database_error(self):
        """Test wallet database error."""
        error = WalletDatabaseError("getting wallet", "Record not found")
        assert str(error) == "Database error during getting wallet: Record not found"
        assert error.operation == "getting wallet"
        assert error.details == "Record not found"

    def test_wallet_evm_service_error(self):
        """Test wallet EVM service error."""
        error = WalletEVMServiceError("creating wallet", "Provider unavailable")
        assert (
            str(error)
            == "EVM service error during creating wallet: Provider unavailable"
        )
        assert error.operation == "creating wallet"
        assert error.details == "Provider unavailable"

    def test_wallet_invalid_pagination_error(self):
        """Test wallet invalid pagination error."""
        error = WalletInvalidPaginationError("Limit exceeds maximum")
        assert str(error) == "Limit exceeds maximum"

    def test_invalid_wallet_private_key_error(self):
        """Test invalid wallet private key error."""
        error = InvalidWalletPrivateKeyError("0x789")
        assert str(error) == "Invalid wallet private key: 0x789"
        assert error.address == "0x789"


class TestAssetsErrors:
    """Test assets-specific errors."""

    def test_assets_error_base(self):
        """Test base assets error."""
        error = AssetsError("Assets operation failed")
        assert str(error) == "Assets operation failed"

    def test_asset_not_found_error(self):
        """Test asset not found error."""
        error = AssetNotFoundError("BTC", "Ethereum")
        assert str(error) == "Asset 'BTC' not found on network 'Ethereum'"
        assert error.asset == "BTC"
        assert error.network == "Ethereum"


class TestAdditionalTransactionErrors:
    """Test additional transaction-specific errors."""

    def test_invalid_network_error(self):
        """Test invalid network error."""
        error = InvalidNetworkError("Bitcoin")
        assert str(error) == "Network Bitcoin not available"
        assert error.network == "Bitcoin"

    def test_invalid_address_error(self):
        """Test invalid address error."""
        error = InvalidAddressError("Address format is invalid")
        assert str(error) == "Address format is invalid"

    def test_empty_transaction_id_error(self):
        """Test empty transaction ID error."""
        error = EmptyTransactionIdError()
        assert str(error) == "Transaction ID cannot be empty"

    def test_insufficient_balance_error(self):
        """Test insufficient balance error."""
        error = InsufficientBalanceError("ETH", 5.0, 10.0)
        assert str(error) == "Insufficient balance for trading ETH:5.0 ETH < 10.0 ETH"
        assert error.asset == "ETH"
        assert error.balance == 5.0
        assert error.amount == 10.0


class TestErrorInheritance:
    """Test error inheritance hierarchy."""

    def test_transaction_error_inheritance(self):
        """Test that transaction errors inherit from TransactionError."""
        assert issubclass(InvalidTxAssetError, TransactionError)
        assert issubclass(InvalidNetworkError, TransactionError)
        assert issubclass(InvalidAmountError, TransactionError)
        assert issubclass(InvalidAddressError, TransactionError)
        assert issubclass(SameAddressError, TransactionError)
        assert issubclass(EmptyAddressError, TransactionError)
        assert issubclass(EmptyTransactionIdError, TransactionError)
        assert issubclass(TransactionNotFoundError, TransactionError)
        assert issubclass(InvalidPaginationError, TransactionError)
        assert issubclass(DatabaseError, TransactionError)
        assert issubclass(EVMServiceError, TransactionError)
        assert issubclass(InsufficientBalanceError, TransactionError)

    def test_wallet_error_inheritance(self):
        """Test that wallet errors inherit from WalletError."""
        assert issubclass(InvalidWalletAddressError, WalletError)
        assert issubclass(WalletNotFoundError, WalletError)
        assert issubclass(InvalidWalletPrivateKeyError, WalletError)
        assert issubclass(WalletCreationError, WalletError)
        assert issubclass(BatchOperationError, WalletError)

    def test_domain_error_inheritance(self):
        """Test that domain errors inherit from DomainError."""
        assert issubclass(ValidationError, DomainError)
        assert issubclass(NotFoundError, DomainError)
        assert issubclass(InvalidInputError, DomainError)
        assert issubclass(BusinessRuleError, DomainError)
        assert issubclass(ConfigurationError, DomainError)

    def test_assets_error_inheritance(self):
        """Test that assets errors inherit from AssetsError."""
        assert issubclass(AssetNotFoundError, AssetsError)
