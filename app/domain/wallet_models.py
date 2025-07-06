from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.data.database import Wallet as DBWallet
from app.domain.enums import WalletStatus
from app.domain.models import Pagination


class Wallet(BaseModel):
    """Wallet model"""

    id: Optional[UUID] = None
    address: Optional[str] = None
    private_key: Optional[str] = None
    status: Optional[WalletStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @classmethod
    def from_data(cls, db_wallet: DBWallet) -> "Wallet":
        """Convert a data layer model to a domain layer model"""
        return Wallet(
            id=db_wallet.id,
            address=db_wallet.address,
            private_key=db_wallet.private_key,
            status=db_wallet.status,
            created_at=db_wallet.created_at,
            updated_at=db_wallet.updated_at,
            deleted_at=db_wallet.deleted_at,
        )

    def to_presentation(self) -> dict:
        """Convert the wallet model to a presentation layer model"""
        return {
            "id": self.id,
            "address": self.address,
            "private_key": self.private_key,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }


class WalletsPagination(BaseModel):
    """Wallets pagination model"""

    pagination: Pagination
    wallets: list[Wallet]
