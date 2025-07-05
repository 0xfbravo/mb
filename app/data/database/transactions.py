import uuid
from enum import Enum
from typing import Any

from asyncpg.exceptions import ConnectionDoesNotExistError
from tortoise import fields
from tortoise.exceptions import OperationalError
from tortoise.models import Model

from app.data.database.errors import (DatabaseConnectionError,
                                      TransactionCreationError,
                                      TransactionNotFoundError,
                                      TransactionRetrievalError,
                                      TransactionUpdateError)
from app.data.database.main import DatabaseManager


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Transaction(Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    wallet_address = fields.CharField(max_length=255)
    amount = fields.FloatField()
    currency = fields.CharField(max_length=255)
    status = fields.CharEnumField(enum_type=TransactionStatus)
    gas_price = fields.IntField()
    gas_limit = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class TransactionRepository:
    """Repository for transaction operations."""

    def __init__(self, db_manager: DatabaseManager, logger: Any):
        self.db_manager = db_manager
        self.logger = logger

    async def create(
        self,
        wallet_address: str,
        amount: float,
        currency: str,
        gas_price: int,
        gas_limit: int,
    ) -> Transaction:
        """Create a new transaction."""
        try:
            return await Transaction.create(
                wallet_address=wallet_address,
                amount=amount,
                currency=currency,
                status=TransactionStatus.PENDING,
                gas_price=gas_price,
                gas_limit=gas_limit,
            )
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in create: {e}")
            raise DatabaseConnectionError("create", e)
        except Exception as e:
            self.logger.error(f"Error creating transaction: {e}")
            raise TransactionCreationError(wallet_address, amount, currency, e)

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction:
        """Get transaction by ID."""
        try:
            transaction = await Transaction.get(id=transaction_id)
            if not transaction:
                raise TransactionNotFoundError(f"id: {transaction_id}")
            return transaction
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_by_id: {e}")
            raise DatabaseConnectionError("get_by_id", e)
        except TransactionNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting transaction by ID: {e}")
            raise TransactionRetrievalError("getting by ID", str(transaction_id), e)

    async def get_by_tx_hash(self, tx_hash: str) -> Transaction:
        """Get transaction by transaction hash."""
        try:
            transaction = await Transaction.get(tx_hash=tx_hash)
            if not transaction:
                raise TransactionNotFoundError(f"hash: {tx_hash}")
            return transaction
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_by_tx_hash: {e}")
            raise DatabaseConnectionError("get_by_tx_hash", e)
        except TransactionNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting transaction by hash: {e}")
            raise TransactionRetrievalError("getting by hash", tx_hash, e)

    async def get_by_wallet(
        self, wallet_address: str, offset: int = 0, limit: int = 100
    ) -> list[Transaction]:
        """Get all transactions for a wallet."""
        try:
            return (
                await Transaction.filter(wallet_address=wallet_address)
                .offset(offset)
                .limit(limit)
            )
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_by_wallet: {e}")
            raise DatabaseConnectionError("get_by_wallet", e)
        except Exception as e:
            self.logger.error(f"Error getting transactions by wallet: {e}")
            raise TransactionRetrievalError("getting by wallet", wallet_address, e)

    async def update_status(
        self, transaction_id: str, status: TransactionStatus
    ) -> Transaction:
        """Update transaction status."""
        try:
            transaction = await Transaction.get(id=transaction_id)
            if not transaction:
                raise TransactionNotFoundError(f"id: {transaction_id}")
            transaction.status = status
            await transaction.save()
            return transaction
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in update_status: {e}")
            raise DatabaseConnectionError("update_status", e)
        except TransactionNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating transaction status: {e}")
            raise TransactionUpdateError(transaction_id, "updating status", e)

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Transaction]:
        """Get all transactions."""
        try:
            return (
                await Transaction.all()
                .order_by("-created_at")
                .offset(offset)
                .limit(limit)
            )
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_all: {e}")
            raise DatabaseConnectionError("get_all", e)
        except Exception as e:
            self.logger.error(f"Error getting all transactions: {e}")
            raise TransactionRetrievalError("getting all transactions", "all", e)
