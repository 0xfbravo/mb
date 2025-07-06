from datetime import datetime
from typing import List, Optional
from uuid import UUID

from eth_typing import HexAddress
from pydantic import BaseModel, Field, field_validator

from app.data.database.transactions import Transaction as DBTransaction
from app.domain.enums import TransactionStatus
from app.domain.models import Pagination


class CreateTx(BaseModel):
    """Create transaction model for blockchain transactions"""

    from_address: HexAddress = Field(
        ...,
        min_length=1,
        description="The address of the sender",
        examples=["0x1234567890123456789012345678901234567890"],
        pattern="^0x[a-fA-F0-9]{40}$",
    )
    to_address: HexAddress = Field(
        ...,
        min_length=1,
        description="The address of the receiver",
        examples=["0x1234567890123456789012345678901234567890"],
        pattern="^0x[a-fA-F0-9]{40}$",
    )
    asset: str = Field(
        ..., min_length=1, description="The asset of the transaction", examples=["USDC"]
    )
    amount: float = Field(
        ..., gt=0, description="The amount of the transaction", examples=[100.0]
    )

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


class TransferInfo(BaseModel):
    """Model for transfer information extracted from transaction"""

    asset: str = Field(..., description="The asset being transferred (ETH, USDC, etc.)")
    destination_address: str = Field(..., description="The destination address")
    amount: float = Field(..., description="The amount transferred in decimal format")
    token_address: Optional[str] = Field(
        None, description="Token contract address for ERC-20 transfers"
    )


class TransactionValidation(BaseModel):
    """Model for transaction validation response"""

    is_valid: bool = Field(
        ...,
        description="Whether the transaction is valid and safe for credit generation",
    )
    transaction_hash: str = Field(
        ..., description="The transaction hash being validated"
    )
    transfers: List[TransferInfo] = Field(
        ..., description="List of transfers identified in the transaction"
    )
    validation_message: str = Field(
        ..., description="Human-readable validation message"
    )
    network: str = Field(..., description="The network where the transaction occurred")


class Transaction(BaseModel):
    """Transaction model for blockchain transactions"""

    id: Optional[UUID] = None
    tx_hash: Optional[str] = None
    asset: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount: Optional[float] = None
    gas_price: Optional[int] = None
    gas_limit: Optional[int] = None
    status: Optional[TransactionStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_data(cls, db_transaction: DBTransaction) -> "Transaction":
        """Convert a data layer model to a domain layer model"""
        return Transaction(
            id=db_transaction.id,
            tx_hash=db_transaction.tx_hash,
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
            "tx_hash": self.tx_hash,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": self.amount,
            "gas_price": self.gas_price,
            "gas_limit": self.gas_limit,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TransactionsPagination(BaseModel):
    """Model for paginated transactions response"""

    transactions: List[Transaction]
    pagination: Pagination
