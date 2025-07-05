import uuid
from enum import Enum
from typing import Any

from asyncpg.exceptions import ConnectionDoesNotExistError
from tortoise import fields
from tortoise.exceptions import OperationalError
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
        try:
            new_wallet = await Wallet.create(
                address=address,
                private_key=private_key,
                status=WalletStatus.ACTIVE,
            )
            return await self.get_by_id(str(new_wallet.id))
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in create: {e}")
            raise RuntimeError("Database connection error")
        except Exception as e:
            self.logger.error(f"Error creating wallet: {e}")
            raise

    async def get_by_address(self, address: str) -> Wallet:
        """Get wallet by address."""
        try:
            return await Wallet.get(address=address)
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_by_address: {e}")
            raise RuntimeError("Database connection error")
        except Exception as e:
            self.logger.error(f"Error getting wallet by address: {e}")
            raise

    async def get_by_id(self, wallet_id: str) -> Wallet:
        """Get wallet by ID."""
        try:
            return await Wallet.get(id=wallet_id)
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_by_id: {e}")
            raise RuntimeError("Database connection error")
        except Exception as e:
            self.logger.error(f"Error getting wallet by ID: {e}")
            raise

    async def update_balance(self, address: str, balance: float) -> Wallet:
        """Update wallet balance."""
        try:
            wallet = await Wallet.get(address=address)
            wallet.balance = balance
            await wallet.save()
            return wallet
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in update_balance: {e}")
            raise RuntimeError("Database connection error")
        except Exception as e:
            self.logger.error(f"Error updating wallet balance: {e}")
            raise

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Wallet]:
        """Get all wallets with pagination."""
        try:
            return (
                await Wallet.all().order_by("-created_at").offset(offset).limit(limit)
            )
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_all: {e}")
            raise RuntimeError("Database connection error")
        except Exception as e:
            self.logger.error(f"Error getting all wallets: {e}")
            raise

    async def get_count(self) -> int:
        """Get total count of wallets."""
        try:
            return await Wallet.all().count()
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_count: {e}")
            raise RuntimeError("Database connection error")
        except Exception as e:
            self.logger.error(f"Error getting wallet count: {e}")
            raise
