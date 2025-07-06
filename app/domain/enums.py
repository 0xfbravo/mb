from enum import Enum


class TransactionStatus(str, Enum):
    """Transaction status enum"""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    @classmethod
    def from_str(cls, value: str) -> "TransactionStatus":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid transaction status: {value}")


class WalletStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    @classmethod
    def from_str(cls, value: str) -> "WalletStatus":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid wallet status: {value}")
