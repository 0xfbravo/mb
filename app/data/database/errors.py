"""Centralized database error definitions."""


class DatabaseError(Exception):
    """Base exception for all database-related errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when there's a database connection issue."""

    def __init__(self, operation: str, original_error: Exception):
        self.operation = operation
        self.original_error = original_error
        super().__init__(
            f"Database connection error during {operation}: {original_error}"
        )


class NotFoundError(DatabaseError):
    """Base exception for not found errors."""

    def __init__(self, entity_type: str, identifier: str):
        self.entity_type = entity_type
        self.identifier = identifier
        super().__init__(f"{entity_type} not found with identifier: {identifier}")


class CreationError(DatabaseError):
    """Base exception for creation errors."""

    def __init__(self, entity_type: str, details: str, original_error: Exception):
        self.entity_type = entity_type
        self.details = details
        self.original_error = original_error
        super().__init__(f"Error creating {entity_type} {details}: {original_error}")


class RetrievalError(DatabaseError):
    """Base exception for retrieval errors."""

    def __init__(
        self,
        entity_type: str,
        operation: str,
        identifier: str,
        original_error: Exception,
    ):
        self.entity_type = entity_type
        self.operation = operation
        self.identifier = identifier
        self.original_error = original_error
        super().__init__(
            f"Error {operation} {entity_type} w/ {identifier}: {original_error}"
        )


class UpdateError(DatabaseError):
    """Base exception for update errors."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        original_error: Exception,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.operation = operation
        self.original_error = original_error
        super().__init__(
            f"Error {operation} {entity_type} {entity_id}: {original_error}"
        )


class DeletionError(DatabaseError):
    """Base exception for deletion errors."""

    def __init__(self, entity_type: str, identifier: str, original_error: Exception):
        self.entity_type = entity_type
        self.identifier = identifier
        self.original_error = original_error
        super().__init__(
            f"Error deleting {entity_type} w/ {identifier}: {original_error}"
        )


# Transaction-specific errors
class TransactionError(DatabaseError):
    """Base exception for transaction-related errors."""

    pass


class TransactionNotFoundError(NotFoundError):
    """Raised when a transaction is not found."""

    def __init__(self, identifier: str):
        super().__init__("Transaction", identifier)


class TransactionCreationError(CreationError):
    """Raised when there's an error creating a transaction."""

    def __init__(
        self,
        from_address: str,
        to_address: str,
        asset: str,
        amount: float,
        original_error: Exception,
    ):
        details = f"for wallet {from_address}, amount {amount} {asset}"
        super().__init__("Transaction", details, original_error)


class TransactionRetrievalError(RetrievalError):
    """Raised when there's an error retrieving transaction data."""

    def __init__(self, operation: str, identifier: str, original_error: Exception):
        super().__init__("Transaction", operation, identifier, original_error)


class TransactionUpdateError(UpdateError):
    """Raised when there's an error updating a transaction."""

    def __init__(self, transaction_id: str, operation: str, original_error: Exception):
        super().__init__("Transaction", transaction_id, operation, original_error)


# Wallet-specific errors
class WalletError(DatabaseError):
    """Base exception for wallet-related errors."""

    pass


class WalletNotFoundError(NotFoundError):
    """Raised when a wallet is not found."""

    def __init__(self, identifier: str):
        super().__init__("Wallet", identifier)


class WalletCreationError(CreationError):
    """Raised when there's an error creating a wallet."""

    def __init__(self, address: str, original_error: Exception):
        details = f"with address {address}"
        super().__init__("Wallet", details, original_error)


class WalletRetrievalError(RetrievalError):
    """Raised when there's an error retrieving wallet data."""

    def __init__(self, operation: str, identifier: str, original_error: Exception):
        super().__init__("Wallet", operation, identifier, original_error)


class WalletDeletionError(DeletionError):
    """Raised when there's an error deleting a wallet."""

    def __init__(self, address: str, original_error: Exception):
        super().__init__("Wallet", address, original_error)
