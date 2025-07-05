from typing import Optional

from pydantic import BaseModel

from app.data.database import Wallet as DBWallet


class Wallet(BaseModel):
    """Wallet model"""

    address: Optional[str] = None
    private_key: Optional[str] = None

    def from_data(self, db_wallet: DBWallet) -> "Wallet":
        """Convert a data layer model to a domain layer model"""
        return Wallet(
            address=db_wallet.address,
            private_key=db_wallet.private_key,
        )

    def to_presentation(self) -> dict:
        """Convert the wallet model to a presentation layer model"""
        return {
            "address": self.address,
            "private_key": self.private_key,
        }

class Pagination(BaseModel):
    """Pagination model"""

    total: int
    page: int
    next_page: Optional[int] = None
    prev_page: Optional[int] = None

    def to_presentation(self) -> dict:
        """Convert the pagination model to a presentation layer model"""
        return {
            "total": self.total,
            "page": self.page,
            "next_page": self.next_page,
            "prev_page": self.prev_page
        }
class WalletsPagination(BaseModel):
    """Wallets pagination model"""

    pagination: Pagination
    wallets: list[Wallet]
