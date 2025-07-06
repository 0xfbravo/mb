from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.data.database.transactions import Transaction as DBTransaction
from app.domain.transaction.enum import Status


class CreateTx(BaseModel):
    """Create transaction model for blockchain transactions"""

    from_address: str = Field(
        ..., min_length=1, description="The address of the sender"
    )
    to_address: str = Field(
        ..., min_length=1, description="The address of the receiver"
    )
    asset: str = Field(..., min_length=1, description="The asset of the transaction")
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

    id: Optional[UUID] = None
    asset: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount: Optional[float] = None
    gas_price: Optional[int] = None
    gas_limit: Optional[int] = None
    status: Optional[Status] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_data(cls, db_transaction: DBTransaction) -> "Transaction":
        """Convert a data layer model to a domain layer model"""
        return Transaction(
            id=db_transaction.id,
            asset=db_transaction.asset,
            from_address=db_transaction.from_address,
            to_address=db_transaction.to_address,
            amount=db_transaction.amount,
            gas_price=db_transaction.gas_price,
            gas_limit=db_transaction.gas_limit,
            status=db_transaction.status,
            created_at=db_transaction.created_at,
            updated_at=db_transaction.updated_at,
        )

    def to_presentation(self):
        """Convert the transaction model to a presentation layer model"""
        return {
            "id": self.id,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "gas_price": self.gas_price,
            "gas_limit": self.gas_limit,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
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
            "prev_page": self.prev_page,
        }


class TransactionsPagination(BaseModel):
    """Transactions pagination model"""

    pagination: Pagination
    transactions: list[Transaction]
