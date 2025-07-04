from pydantic import BaseModel


class Wallet(BaseModel):
    """Wallet model"""

    address: str
    name: str
    balance: float = 0.0

    def to_data_layer(self) -> dict:
        """Convert the wallet model to a data layer model"""
        return {
            "address": self.address,
            "name": self.name,
            "balance": self.balance,
        }

    def to_presentation_layer(self) -> dict:
        """Convert the wallet model to a presentation layer model"""
        return {
            "address": self.address,
            "name": self.name,
            "balance": self.balance,
        }


def wallet_to_domain(wallet: dict) -> Wallet:
    """Convert a wallet model to a domain layer model"""
    return Wallet(
        address=wallet["address"],
        name=wallet["name"],
        balance=wallet["balance"],
    )
