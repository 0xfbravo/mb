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
