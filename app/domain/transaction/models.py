from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.data.database import Transaction as DBTransaction


class CreateTx(BaseModel):
    """Create transaction model for blockchain transactions"""

    from_address: str = Field(
        ..., min_length=1, description="The address of the sender"
    )
    to_address: str = Field(
        ..., min_length=1, description="The address of the receiver"
    )
    amount: float = Field(..., gt=0, description="The amount of the transaction")

    @field_validator("from_address")
    @classmethod
    def validate_from_address(cls, v):
        if not v or v.strip() == "":
            raise ValueError("from_address cannot be empty")
        return v

    @field_validator("to_address")
    @classmethod
    def validate_to_address(cls, v):
        if not v or v.strip() == "":
            raise ValueError("to_address cannot be empty")
        return v


class Transaction(BaseModel):
    """Transaction model for blockchain transactions"""

    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount: Optional[float] = None
    gas_price: Optional[int] = None
    gas_limit: Optional[int] = None

    def from_data(self, db_transaction: DBTransaction) -> "Transaction":
        """Convert a data layer model to a domain layer model"""
        return Transaction(
            from_address=db_transaction.wallet_address,
            to_address=db_transaction.wallet_address,
            amount=db_transaction.amount,
            gas_price=db_transaction.gas_price,
            gas_limit=db_transaction.gas_limit,
        )

    def to_presentation(self):
        """Convert the transaction model to a presentation layer model"""
        return {
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "gas_price": self.gas_price,
            "gas_limit": self.gas_limit,
        }
