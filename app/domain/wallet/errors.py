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


class WalletCreationError(WalletError):
    """Raised when wallet creation fails."""

    def __init__(self, details: str):
        self.details = details
        super().__init__(f"Failed to create wallet: {details}")


class InvalidPaginationError(WalletError):
    """Raised when pagination parameters are invalid."""

    def __init__(self, message: str):
        super().__init__(message)


class DatabaseError(WalletError):
    """Raised when database operations fail."""

    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Database error during {operation}: {details}")


class EVMServiceError(WalletError):
    """Raised when EVM service operations fail."""

    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"EVM service error during {operation}: {details}")


class BatchOperationError(WalletError):
    """Raised when batch operations fail."""

    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Batch {operation} failed: {details}")
