from enum import Enum


class WalletStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    @classmethod
    def from_str(cls, value: str) -> "WalletStatus":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid wallet status: {value}")
