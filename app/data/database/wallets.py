import uuid
from enum import Enum
from typing import Any

from tortoise import fields
from tortoise.models import Model

from app.data.database.main import DatabaseManager


class WalletStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Wallet(Model):
    """Wallet model for database operations."""

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    address = fields.CharField(max_length=255, unique=True)
    private_key = fields.CharField(max_length=255)
    balance = fields.FloatField(default=0.0)
    status = fields.CharEnumField(enum_type=WalletStatus)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)


class WalletRepository:
    """Repository for wallet operations."""

    def __init__(self, db_manager: DatabaseManager, logger: Any):
        self.db_manager = db_manager
        self.logger = logger

    async def create(self, address: str, private_key: str) -> Wallet:
        """Create a new wallet."""
        return await Wallet.create(
            address=address,
            private_key=private_key,
            status=WalletStatus.ACTIVE,
        )

    async def get_by_address(self, address: str) -> Wallet:
        """Get wallet by address."""
        return await Wallet.get(address=address)

    async def get_by_id(self, wallet_id: str) -> Wallet:
        """Get wallet by ID."""
        return await Wallet.get(id=wallet_id)

    async def update_balance(self, address: str, balance: float) -> Wallet:
        """Update wallet balance."""
        wallet = await Wallet.get(address=address)
        wallet.balance = balance
        await wallet.save()
        return wallet

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Wallet]:
        """Get all wallets with pagination."""
        return await Wallet.all().offset(offset).limit(limit)

    async def get_count(self) -> int:
        """Get total count of wallets."""
        return await Wallet.all().count()
