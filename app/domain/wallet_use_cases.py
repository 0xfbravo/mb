import asyncio
from typing import Any

from eth_typing import HexAddress

from app.data.database import WalletRepository
from app.data.evm.main import EVMService
from app.domain.assets_use_cases import AssetsUseCases
from app.domain.errors import (BatchOperationError, DatabaseError,
                               EVMServiceError, InvalidPaginationError,
                               InvalidWalletAddressError, WalletCreationError)
from app.domain.wallet_models import Pagination, Wallet, WalletsPagination


class WalletUseCases:
    """Use cases for wallet operations."""

    def __init__(
        self,
        wallet_repo: WalletRepository,
        evm_service: EVMService,
        assets_use_cases: AssetsUseCases,
        logger: Any,
    ):
        self._wallet_repo = wallet_repo
        self._evm_service = evm_service
        self._assets_use_cases = assets_use_cases
        self._logger = logger

    async def create(self, number_of_wallets: int) -> list[Wallet]:
        """Create a new wallet.
        Args:
            number_of_wallets: The number of wallets to create.
        Returns:
            The created wallets.
        """

        self._logger.info("Creating wallet")

        # Create wallet creation tasks
        async def create_single_wallet():
            try:
                wallet = self._evm_service.create_wallet()
            except Exception as e:
                self._logger.error(f"EVM service error creating wallet: {e}")
                raise EVMServiceError("creating wallet", str(e))

            try:
                db_wallet = await self._wallet_repo.create(
                    address=wallet.address,
                    private_key=wallet.key.hex(),
                )
                self._logger.info(f"Successfully created wallet: {wallet.address}")
                return Wallet.from_data(db_wallet=db_wallet)
            except RuntimeError as e:
                self._logger.error(
                    f"Database error creating wallet {wallet.address}: {e}"
                )
                raise DatabaseError("creating wallet", str(e))
            except Exception as e:
                self._logger.error(
                    f"Unexpected error creating wallet {wallet.address}: {e}"
                )
                raise WalletCreationError(str(e))

        # Create all wallets concurrently using asyncio.gather
        try:
            wallets = await asyncio.gather(
                *[create_single_wallet() for _ in range(number_of_wallets)]
            )
            self._logger.info(f"Successfully created {number_of_wallets} wallets")
            return wallets
        except Exception as e:
            self._logger.error(f"Error in batch wallet creation: {e}")
            raise BatchOperationError("wallet creation", str(e))

    async def get_all(self, page: int = 1, limit: int = 100) -> WalletsPagination:
        """Get all wallets with pagination.
        Args:
            page: The page number.
            limit: The number of wallets per page.
        Returns:
            The wallets.
        """
        self._logger.info(
            f"Getting wallets with pagination: page={page}, limit={limit}"
        )

        # Validate pagination parameters
        if page < 1:
            self._logger.error("Page must be greater than 0")
            raise InvalidPaginationError("Page must be greater than 0")

        if limit < 1:
            self._logger.error("Limit must be greater than 0")
            raise InvalidPaginationError("Limit must be greater than 0")

        if limit > 1000:
            self._logger.error("Limit must be less than 1000")
            raise InvalidPaginationError("Limit must be less than 1000")

        try:
            # Get paginated wallets and total count
            db_wallets, total_count = await asyncio.gather(
                self._wallet_repo.get_all(offset=(page - 1) * limit, limit=limit),
                self._wallet_repo.get_count(),
            )

            wallets = [Wallet.from_data(wallet) for wallet in db_wallets]

            # Calculate pagination metadata
            total_pages = (total_count + limit - 1) // limit
            current_page = page

            self._logger.info(
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
            self._logger.error(f"Database error getting wallets: {e}")
            raise DatabaseError("getting wallets", str(e))
        except Exception as e:
            self._logger.error(f"Unexpected error getting wallets: {e}")
            raise

    async def get_by_address(self, address: str) -> Wallet:
        """Get wallet by address.
        Args:
            address: The address of the wallet.
        Returns:
            The wallet.
        """

        self._logger.info(f"Getting wallet by address: {address}")

        if not address or address.strip() == "":
            self._logger.error("Wallet address is required")
            raise InvalidWalletAddressError("empty address")

        try:
            db_wallet = await self._wallet_repo.get_by_address(address)
            self._logger.info(f"Successfully retrieved wallet: {address}")
            return Wallet.from_data(db_wallet)
        except RuntimeError as e:
            self._logger.error(f"Database error getting wallet {address}: {e}")
            raise DatabaseError("getting wallet by address", str(e))
        except Exception as e:
            self._logger.error(f"Unexpected error getting wallet {address}: {e}")
            raise

    async def delete_wallet(self, address: str) -> Wallet:
        """Delete wallet by address.
        Args:
            address: The address of the wallet.
        Returns:
            The deleted wallet.
        """

        self._logger.info(f"Deleting wallet: {address}")

        if not address or address.strip() == "":
            self._logger.error("Wallet address is required")
            raise InvalidWalletAddressError("empty address")

        try:
            db_wallet = await self._wallet_repo.delete(address)
            self._logger.info(f"Successfully deleted wallet: {address}")
            return Wallet.from_data(db_wallet)
        except RuntimeError as e:
            self._logger.error(f"Database error deleting wallet {address}: {e}")
            raise DatabaseError("deleting wallet", str(e))
        except Exception as e:
            self._logger.error(f"Unexpected error deleting wallet {address}: {e}")
            raise

    async def get_native_balance(self, address: HexAddress) -> float:
        """Get native balance of a wallet.
        Args:
            address: The address of the wallet.
        Returns:
            The balance of the native asset in the wallet.
        """

        self._logger.info(f"Getting balance of wallet: {address}")

        if not address or address.strip() == "":
            self._logger.error("Wallet address is required")
            raise InvalidWalletAddressError("empty address")

        try:
            balance = self._evm_service.get_wallet_balance(address)
            self._logger.info(f"Successfully retrieved balance: {balance}")
            return balance
        except Exception as e:
            self._logger.error(f"Unexpected error getting balance: {e}")
            raise

    async def get_token_balance(
        self, asset: str, address: HexAddress, abi_name: str = "erc20"
    ) -> float:
        """Get token balance of a wallet.
        Args:
            asset: The asset to get the balance of.
            address: The address of the wallet.
        Returns:
            The balance of the asset in the wallet.
        """
        self._logger.info(
            f"Getting token balance of wallet: {address} for asset: {asset}"
        )
        try:
            asset_address = self._assets_use_cases.get_asset_address(asset)
            balance = self._evm_service.get_token_balance(
                address, asset_address, abi_name
            )
            self._logger.info(f"Successfully retrieved token balance: {balance}")
            return balance
        except Exception as e:
            self._logger.error(f"Unexpected error getting token balance: {e}")
            raise
