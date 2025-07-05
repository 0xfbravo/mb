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
