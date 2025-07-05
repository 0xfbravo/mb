import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from asyncpg.exceptions import ConnectionDoesNotExistError
from tortoise import fields
from tortoise.exceptions import OperationalError
from tortoise.models import Model

from app.data.database.errors import (DatabaseConnectionError,
                                      WalletCreationError, WalletDeletionError,
                                      WalletNotFoundError,
                                      WalletRetrievalError)
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
            return await Wallet.create(
                address=address,
                private_key=private_key,
                status=WalletStatus.ACTIVE,
            )
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in create: {e}")
            raise DatabaseConnectionError("create", e)
        except Exception as e:
            self.logger.error(f"Error creating wallet: {e}")
            raise WalletCreationError(address, e)

    async def get_by_address(self, address: str) -> Wallet:
        """Get wallet by address."""
        try:
            wallet = await Wallet.get(address=address)
            if not wallet:
                raise WalletNotFoundError(f"address: {address}")
            return wallet
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_by_address: {e}")
            raise DatabaseConnectionError("get_by_address", e)
        except WalletNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting wallet by address: {e}")
            raise WalletRetrievalError("getting by address", address, e)

    async def get_by_id(self, wallet_id: str) -> Wallet:
        """Get wallet by ID."""
        try:
            wallet = await Wallet.get(id=wallet_id)
            if not wallet:
                raise WalletNotFoundError(f"id: {wallet_id}")
            return wallet
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_by_id: {e}")
            raise DatabaseConnectionError("get_by_id", e)
        except WalletNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting wallet by ID: {e}")
            raise WalletRetrievalError("getting by ID", wallet_id, e)

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Wallet]:
        """Get all wallets with pagination."""
        try:
            return (
                await Wallet.filter(status=WalletStatus.ACTIVE, deleted_at=None)
                .order_by("-created_at")
                .offset(offset)
                .limit(limit)
            )
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_all: {e}")
            raise DatabaseConnectionError("get_all", e)
        except Exception as e:
            self.logger.error(f"Error getting all wallets: {e}")
            raise WalletRetrievalError("getting all wallets", "all", e)

    async def get_count(self) -> int:
        """Get total count of wallets."""
        try:
            return await Wallet.filter(
                status=WalletStatus.ACTIVE, deleted_at=None
            ).count()
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in get_count: {e}")
            raise DatabaseConnectionError("get_count", e)
        except Exception as e:
            self.logger.error(f"Error getting wallet count: {e}")
            raise WalletRetrievalError("getting wallet count", "count", e)

    async def delete(self, address: str) -> Wallet:
        """Delete wallet by address."""
        try:
            wallet = await Wallet.filter(
                address=address, status=WalletStatus.ACTIVE, deleted_at=None
            ).first()
            if not wallet:
                raise WalletNotFoundError(f"address: {address}")
            await Wallet.filter(id=wallet.id).update(
                status=WalletStatus.INACTIVE, deleted_at=datetime.now()
            )
            return wallet
        except (OperationalError, ConnectionDoesNotExistError) as e:
            self.logger.error(f"Database connection error in delete: {e}")
            raise DatabaseConnectionError("delete", e)
        except WalletNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting wallet: {e}")
            raise WalletDeletionError(address, e)
