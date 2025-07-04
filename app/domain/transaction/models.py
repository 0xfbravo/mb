from typing import Optional

from pydantic import BaseModel


class CreateTransaction(BaseModel):
    """Create transaction model for blockchain transactions"""

    from_address: str
    to_address: str
    amount: float


class Transaction(BaseModel):
    """Transaction model for blockchain transactions"""

    from_address: str
    to_address: str
    amount: float
    gas_price: Optional[float] = None
    gas_limit: Optional[int] = None
    data: Optional[str] = None

    def to_data_layer(self) -> dict:
        """Convert the transaction model to a data layer model"""
        return {
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "gas_price": self.gas_price,
            "gas_limit": self.gas_limit,
            "data": self.data,
        }

    def to_presentation_layer(self):
        """Convert the transaction model to a presentation layer model"""
        return {
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "gas_price": self.gas_price,
            "gas_limit": self.gas_limit,
            "data": self.data,
        }


def tx_to_domain(tx: dict) -> Transaction:
    """Convert a transaction model to a domain layer model"""
    return Transaction(
        from_address=tx["from_address"],
        to_address=tx["to_address"],
        amount=tx["amount"],
        gas_price=tx["gas_price"],
        gas_limit=tx["gas_limit"],
        data=tx["data"],
    )
