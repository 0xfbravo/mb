"""Shared error classes for domain layer."""

from typing import Optional


class DomainError(Exception):
    """Base exception for domain-related errors."""

    pass


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class NotFoundError(DomainError):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(f"{resource_type} with identifier {identifier} not found")


class InvalidInputError(DomainError):
    """Raised when input data is invalid."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleError(DomainError):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, rule: Optional[str] = None):
        self.message = message
        self.rule = rule
        super().__init__(message)


class ConfigurationError(DomainError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        self.message = message
        self.config_key = config_key
        super().__init__(message)


"""Custom error classes for wallet domain."""


class WalletError(Exception):
    """Base exception for wallet-related errors."""

    pass


class InvalidWalletAddressError(WalletError):
    """Raised when a wallet address is invalid."""

    def __init__(self, address: str):
        self.address = address
        super().__init__(f"Invalid wallet address: {address}")


class WalletNotFoundError(WalletError):
    """Raised when a wallet is not found."""

    def __init__(self, address: str):
        self.address = address
        super().__init__(f"Wallet with address {address} not found")


class InvalidWalletPrivateKeyError(WalletError):
    """Raised when a wallet private key is invalid."""

    def __init__(self, address: str):
        self.address = address
        super().__init__(f"Invalid wallet private key: {address}")


class WalletCreationError(WalletError):
    """Raised when wallet creation fails."""

    def __init__(self, details: str):
        self.details = details
        super().__init__(f"Failed to create wallet: {details}")


class BatchOperationError(WalletError):
    """Raised when batch operations fail."""

    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Batch {operation} failed: {details}")


"""Custom error classes for transaction domain."""


class TransactionError(Exception):
    """Base exception for transaction-related errors."""

    pass


class InvalidAssetError(TransactionError):
    """Raised when an asset is not supported on the selected network."""

    def __init__(self, asset: str, network: str):
        self.asset = asset
        self.network = network
        super().__init__(
            f'Unable to trade "{asset}" on our current network "{network}"'
        )


class InvalidNetworkError(TransactionError):
    """Raised when a network is not supported."""

    def __init__(self, network: str):
        self.network = network
        super().__init__(f"Network {network} not available")


class InvalidAmountError(TransactionError):
    """Raised when the transaction amount is invalid."""

    def __init__(self, amount: float):
        self.amount = amount
        super().__init__(f"Amount must be greater than 0, got {amount}")


class InvalidAddressError(TransactionError):
    """Raised when address validation fails."""

    def __init__(self, message: str):
        super().__init__(message)


class SameAddressError(TransactionError):
    """Raised when from_address and to_address are the same."""

    def __init__(self, address: str):
        self.address = address
        super().__init__(f"From address and to address cannot be the same: {address}")


class EmptyAddressError(TransactionError):
    """Raised when an address is empty."""

    def __init__(self, address_type: str):
        self.address_type = address_type
        super().__init__(f"{address_type} address cannot be empty")


class EmptyTransactionIdError(TransactionError):
    """Raised when a transaction ID is empty."""

    def __init__(self):
        super().__init__("Transaction ID cannot be empty")


class TransactionNotFoundError(TransactionError):
    """Raised when a transaction is not found."""

    def __init__(self, identifier: str, identifier_type: str = "ID"):
        self.identifier = identifier
        self.identifier_type = identifier_type
        super().__init__(
            f"Transaction with {identifier_type.lower()} {identifier} not found"
        )


class InvalidPaginationError(TransactionError):
    """Raised when pagination parameters are invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class DatabaseError(TransactionError):
    """Raised when database operations fail."""

    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Database error during {operation}: {details}")


class EVMServiceError(TransactionError):
    """Raised when EVM service operations fail."""

    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"EVM service error during {operation}: {details}")


class InsufficientBalanceError(TransactionError):
    """Raised when the balance is insufficient."""

    def __init__(self, asset: str, balance: float, amount: float):
        self.asset = asset
        self.balance = balance
        self.amount = amount
        super().__init__(
            f"Insufficient balance for trading {asset}:"
            f"{balance} {asset} < {amount} {asset}"
        )
