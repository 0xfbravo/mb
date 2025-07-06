"""Tests for centralized database errors."""

from app.data.database.errors import (DatabaseConnectionError, DatabaseError,
                                      TransactionCreationError,
                                      TransactionError,
                                      TransactionNotFoundError,
                                      TransactionRetrievalError,
                                      TransactionUpdateError,
                                      WalletCreationError, WalletDeletionError,
                                      WalletError, WalletNotFoundError,
                                      WalletRetrievalError)


class TestDatabaseErrors:
    """Test database error classes."""

    def test_database_error_inheritance(self):
        """Test that all database errors inherit from DatabaseError."""
        assert issubclass(TransactionError, DatabaseError)
        assert issubclass(WalletError, DatabaseError)
        assert issubclass(DatabaseConnectionError, DatabaseError)

    def test_transaction_error_inheritance(self):
        """Test that transaction-specific errors inherit from DatabaseError."""
        assert issubclass(TransactionNotFoundError, DatabaseError)
        assert issubclass(TransactionCreationError, DatabaseError)
        assert issubclass(TransactionRetrievalError, DatabaseError)
        assert issubclass(TransactionUpdateError, DatabaseError)

    def test_wallet_error_inheritance(self):
        """Test that wallet-specific errors inherit from DatabaseError."""
        assert issubclass(WalletNotFoundError, DatabaseError)
        assert issubclass(WalletCreationError, DatabaseError)
        assert issubclass(WalletRetrievalError, DatabaseError)
        assert issubclass(WalletDeletionError, DatabaseError)

    def test_database_connection_error(self):
        """Test DatabaseConnectionError creation and attributes."""
        original_error = Exception("Connection failed")
        error = DatabaseConnectionError("test_operation", original_error)

        assert error.operation == "test_operation"
        assert error.original_error == original_error
        assert "Database connection error during test_operation" in str(error)

    def test_transaction_not_found_error(self):
        """Test TransactionNotFoundError creation and attributes."""
        error = TransactionNotFoundError("test_id")

        assert error.entity_type == "Transaction"
        assert error.identifier == "test_id"
        assert "Transaction not found with identifier: test_id" in str(error)

    def test_transaction_creation_error(self):
        """Test TransactionCreationError creation and attributes."""
        original_error = Exception("Creation failed")
        error = TransactionCreationError("0x123", "0x456", "ETH", 1.5, original_error)

        assert error.entity_type == "Transaction"
        assert error.details == "for wallet 0x123, amount 1.5 ETH"
        assert error.original_error == original_error
        assert "Error creating Transaction for wallet 0x123, amount 1.5 ETH" in str(
            error
        )

    def test_transaction_retrieval_error(self):
        """Test TransactionRetrievalError creation and attributes."""
        original_error = Exception("Retrieval failed")
        error = TransactionRetrievalError("getting by ID", "test_id", original_error)

        assert error.entity_type == "Transaction"
        assert error.operation == "getting by ID"
        assert error.identifier == "test_id"
        assert error.original_error == original_error
        assert "Error getting by ID Transaction w/ test_id" in str(error)

    def test_transaction_update_error(self):
        """Test TransactionUpdateError creation and attributes."""
        original_error = Exception("Update failed")
        error = TransactionUpdateError("test_id", "updating status", original_error)

        assert error.entity_type == "Transaction"
        assert error.entity_id == "test_id"
        assert error.operation == "updating status"
        assert error.original_error == original_error
        assert "Error updating status Transaction test_id" in str(error)

    def test_wallet_not_found_error(self):
        """Test WalletNotFoundError creation and attributes."""
        error = WalletNotFoundError("test_address")

        assert error.entity_type == "Wallet"
        assert error.identifier == "test_address"
        assert "Wallet not found with identifier: test_address" in str(error)

    def test_wallet_creation_error(self):
        """Test WalletCreationError creation and attributes."""
        original_error = Exception("Creation failed")
        error = WalletCreationError("0x123", original_error)

        assert error.entity_type == "Wallet"
        assert error.details == "with address 0x123"
        assert error.original_error == original_error
        assert "Error creating Wallet with address 0x123" in str(error)

    def test_wallet_retrieval_error(self):
        """Test WalletRetrievalError creation and attributes."""
        original_error = Exception("Retrieval failed")
        error = WalletRetrievalError("getting by address", "0x123", original_error)

        assert error.entity_type == "Wallet"
        assert error.operation == "getting by address"
        assert error.identifier == "0x123"
        assert error.original_error == original_error
        assert "Error getting by address Wallet w/ 0x123" in str(error)

    def test_wallet_deletion_error(self):
        """Test WalletDeletionError creation and attributes."""
        original_error = Exception("Deletion failed")
        error = WalletDeletionError("0x123", original_error)

        assert error.entity_type == "Wallet"
        assert error.identifier == "0x123"
        assert error.original_error == original_error
        assert "Error deleting Wallet w/ 0x123" in str(error)
