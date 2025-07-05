import asyncio
from typing import Any

from app.data.database import WalletRepository
from app.data.evm.main import EVMService
from app.domain.wallet.models import Pagination, Wallet, WalletsPagination


class WalletUseCases:
    """Use cases for wallet operations."""

    def __init__(
        self, wallet_repo: WalletRepository, evm_service: EVMService, logger: Any
    ):
        self.wallet_repo = wallet_repo
        self.evm_service = evm_service
        self.logger = logger

    async def create(self, number_of_wallets: int) -> list[Wallet]:
        """Create a new wallet."""

        self.logger.info("Creating wallet")

        # Create wallet creation tasks
        async def create_single_wallet():
            wallet = self.evm_service.create_wallet()
            try:
                db_wallet = await self.wallet_repo.create(
                    address=wallet.address,
                    private_key=wallet.key.hex(),
                )
                self.logger.info(f"Successfully created wallet: {wallet.address}")
                return Wallet.from_data(db_wallet=db_wallet)
            except RuntimeError as e:
                self.logger.error(
                    f"Database error creating wallet {wallet.address}: {e}"
                )
                raise
            except Exception as e:
                self.logger.error(
                    f"Unexpected error creating wallet {wallet.address}: {e}"
                )
                raise

        # Create all wallets concurrently using asyncio.gather
        try:
            wallets = await asyncio.gather(
                *[create_single_wallet() for _ in range(number_of_wallets)]
            )
            self.logger.info(f"Successfully created {number_of_wallets} wallets")
            return wallets
        except Exception as e:
            self.logger.error(f"Error in batch wallet creation: {e}")
            raise

    async def get_all(self, page: int = 1, limit: int = 100) -> WalletsPagination:
        """Get all wallets with pagination."""
        self.logger.info(f"Getting wallets with pagination: page={page}, limit={limit}")

        try:
            # Get paginated wallets and total count
            db_wallets, total_count = await asyncio.gather(
                self.wallet_repo.get_all(offset=(page - 1) * limit, limit=limit),
                self.wallet_repo.get_count(),
            )

            wallets = [Wallet.from_data(wallet) for wallet in db_wallets]

            # Calculate pagination metadata
            total_pages = (total_count + limit - 1) // limit
            current_page = page

            self.logger.info(
                f"Successfully retrieved {len(wallets)} of {total_count} wallets"
            )

            return WalletsPagination(
                wallets=wallets,
                pagination=Pagination(
                    total=total_count,
                    page=current_page,
                    next_page=current_page + 1 if current_page < total_pages else None,
                    prev_page=current_page - 1 if current_page > 1 else None,
                ),
            )
        except RuntimeError as e:
            self.logger.error(f"Database error getting wallets: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting wallets: {e}")
            raise

    async def get_by_address(self, address: str) -> Wallet:
        """Get wallet by address."""

        self.logger.info(f"Getting wallet by address: {address}")
        try:
            db_wallet = await self.wallet_repo.get_by_address(address)
            self.logger.info(f"Successfully retrieved wallet: {address}")
            return Wallet.from_data(db_wallet)
        except RuntimeError as e:
            self.logger.error(f"Database error getting wallet {address}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting wallet {address}: {e}")
            raise

    async def update_balance(self, address: str, balance: float) -> Wallet:
        """Update wallet balance."""

        self.logger.info(f"Updating wallet balance: {address} to {balance}")
        db_wallet = await self.wallet_repo.update_balance(address, balance)
        self.logger.info(f"Successfully updated wallet balance: {address}")

        return Wallet.from_data(db_wallet)
