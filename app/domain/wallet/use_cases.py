import uuid
from typing import Any

from app.data.database import WalletRepository
from app.domain.wallet.models import Wallet


class WalletUseCases:
    """Use cases for wallet operations."""

    def __init__(self, wallet_repo: WalletRepository, logger: Any):
        self.wallet_repo = wallet_repo
        self.logger = logger

    async def create(self) -> Wallet:
        """Create a new wallet."""

        self.logger.info("Creating wallet")
        # TODO: Generate a real address and private key
        address = f"0x{uuid.uuid4().hex[:40]}"
        private_key = f"private_key_for_{address}"

        db_wallet = await self.wallet_repo.create(
            address=address,
            private_key=private_key,
        )

        self.logger.info(f"Successfully created wallet: {address}")
        return Wallet(
            address=db_wallet.address,
            private_key=db_wallet.private_key,
        )

    async def get_all(self) -> list[Wallet]:
        """Get all wallets."""
        self.logger.info("Getting all wallets")
        db_wallets = await self.wallet_repo.get_all()
        self.logger.info(f"Successfully retrieved {len(db_wallets)} wallets")
        return [Wallet(address=wallet.address, private_key=wallet.private_key) for wallet in db_wallets]

    async def get_by_address(self, address: str) -> Wallet:
        """Get wallet by address."""

        self.logger.info(f"Getting wallet by address: {address}")
        db_wallet = await self.wallet_repo.get_by_address(address)
        self.logger.info(f"Successfully retrieved wallet: {address}")
        return Wallet(
            address=db_wallet.address,
            private_key=db_wallet.private_key,
        )

    async def update_balance(self, address: str, balance: float) -> Wallet:
        """Update wallet balance."""

        self.logger.info(f"Updating wallet balance: {address} to {balance}")
        db_wallet = await self.wallet_repo.update_balance(address, balance)
        self.logger.info(f"Successfully updated wallet balance: {address}")

        return Wallet(
            address=db_wallet.address,
            private_key=db_wallet.private_key,
        )
