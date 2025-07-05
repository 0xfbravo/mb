import uuid
from enum import Enum
from typing import Any

from tortoise import fields
from tortoise.models import Model

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
        return await Transaction.create(
            wallet_address=wallet_address,
            amount=amount,
            currency=currency,
            status=TransactionStatus.PENDING,
            gas_price=gas_price,
            gas_limit=gas_limit,
        )

    async def get_by_id(self, transaction_id: str) -> Transaction:
        """Get transaction by ID."""
        return await Transaction.get(id=transaction_id)

    async def get_by_tx_hash(self, tx_hash: str) -> Transaction:
        """Get transaction by transaction hash."""
        return await Transaction.get(tx_hash=tx_hash)

    async def get_by_wallet(self, wallet_address: str, offset: int = 0, limit: int = 100) -> list[Transaction]:
        """Get all transactions for a wallet."""
        return await Transaction.filter(wallet_address=wallet_address).offset(offset).limit(limit)

    async def update_status(
        self, transaction_id: str, status: TransactionStatus
    ) -> Transaction:
        """Update transaction status."""
        transaction = await Transaction.get(id=transaction_id)
        transaction.status = status
        await transaction.save()
        return transaction

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Transaction]:
        """Get all transactions."""
        return await Transaction.all().offset(offset).limit(limit)
