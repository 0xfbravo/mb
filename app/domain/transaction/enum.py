from enum import Enum


class Status(str, Enum):
    """Transaction status enum"""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    @classmethod
    def from_str(cls, value: str) -> "Status":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid transaction status: {value}")
