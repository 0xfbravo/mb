from typing import Any
from uuid import UUID

from app.data.database import TransactionRepository
from app.data.evm.main import EVMService
from app.domain.transaction.errors import (DatabaseError, EmptyAddressError,
                                           EmptyTransactionIdError,
                                           InvalidAmountError,
                                           InvalidAssetError,
                                           InvalidPaginationError,
                                           SameAddressError)
from app.domain.transaction.models import (CreateTx, Pagination, Transaction,
                                           TransactionsPagination)
from app.utils.config_manager import ConfigManager


class TransactionUseCases:
    """Use cases for transaction operations."""

    def __init__(
        self,
        config_manager: ConfigManager,
        evm_service: EVMService,
        tx_repo: TransactionRepository,
        logger: Any,
    ):
        self.config_manager = config_manager
        self.evm_service = evm_service
        self.tx_repo = tx_repo
        self.logger = logger

    async def create(self, tx_data: CreateTx) -> Transaction:
        """Create a new transaction."""
        self.logger.info(
            f"Creating transaction for {tx_data.asset}"
            f"from {tx_data.from_address} to {tx_data.to_address}"
        )

        try:
            # Validate the transaction data
            selected_network = self.config_manager.get_selected_network()
            assets = self.config_manager.get_assets()
            if (
                tx_data.asset not in assets
                or selected_network not in self.config_manager.get_networks()
            ):
                self.logger.error(
                    f"Unable to trade {tx_data.asset} on {selected_network}"
                )
                raise InvalidAssetError(tx_data.asset, selected_network)

            if tx_data.amount <= 0:
                self.logger.error("Amount must be greater than 0")
                raise InvalidAmountError(tx_data.amount)

            if tx_data.from_address == tx_data.to_address:
                self.logger.error("From address and to address cannot be the same")
                raise SameAddressError(tx_data.from_address)

            if tx_data.from_address == "":
                self.logger.error("From address cannot be empty")
                raise EmptyAddressError("From")

            if tx_data.to_address == "":
                self.logger.error("To address cannot be empty")
                raise EmptyAddressError("To")

            self.logger.info(
                f"Creating transaction for {tx_data.asset} on {selected_network}"
            )
            db_transaction = await self.tx_repo.create(
                asset=tx_data.asset,
                network=selected_network,
                from_address=tx_data.from_address,
                to_address=tx_data.to_address,
                amount=tx_data.amount,
                gas_price=1000000000,
                gas_limit=21000,
            )

            asset = self.config_manager.get_asset(tx_data.asset)
            if asset["native"]:
                # TODO: Implement native transfer
                pass
            else:
                # TODO: Implement ERC20 transfer
                pass

            return Transaction().from_data(db_transaction)
        except (
            InvalidAssetError,
            InvalidAmountError,
            SameAddressError,
            EmptyAddressError,
        ):
            # Re-raise domain-specific errors as they are already properly typed
            raise
        except RuntimeError as e:
            self.logger.error(f"Database error creating transaction: {e}")
            raise DatabaseError("creating transaction", str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error creating transaction: {e}")
            raise

    async def get_by_id(self, transaction_id: UUID) -> Transaction:
        """Get transaction by ID."""
        self.logger.info(f"Getting transaction by ID {transaction_id}")

        if transaction_id == "":
            self.logger.error("Transaction ID is required")
            raise EmptyTransactionIdError()

        try:
            db_transaction = await self.tx_repo.get_by_id(transaction_id)
            return Transaction().from_data(db_transaction)
        except RuntimeError as e:
            self.logger.error(
                f"Database error getting transaction {transaction_id}: {e}"
            )
            raise DatabaseError("getting transaction by ID", str(e))
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting transaction {transaction_id}: {e}"
            )
            raise

    async def get_by_tx_hash(self, tx_hash: str) -> Transaction:
        """Get transaction by transaction hash."""
        self.logger.info(f"Getting transaction by hash {tx_hash}")

        if tx_hash == "":
            self.logger.error("Transaction hash is required")
            raise EmptyAddressError("Transaction hash")

        try:
            db_transaction = await self.tx_repo.get_by_tx_hash(tx_hash)
            return Transaction().from_data(db_transaction)
        except RuntimeError as e:
            self.logger.error(
                f"Database error getting transaction by hash {tx_hash}: {e}"
            )
            raise DatabaseError("getting transaction by hash", str(e))
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting transaction by hash {tx_hash}: {e}"
            )
            raise

    async def get_txs(
        self, wallet_address: str, page: int = 1, limit: int = 100
    ) -> TransactionsPagination:
        """Get all transactions for a wallet."""
        self.logger.info(
            f"Getting all transactions for wallet {wallet_address}"
            f"from page {page} with limit {limit}"
        )

        if wallet_address == "":
            self.logger.error("Wallet address is required")
            raise EmptyAddressError("Wallet")

        if page < 1:
            self.logger.error("Page must be greater than 0")
            raise InvalidPaginationError("Page must be greater than 0")

        if limit < 1:
            self.logger.error("Limit must be greater than 0")
            raise InvalidPaginationError("Limit must be greater than 0")

        try:
            db_transactions = await self.tx_repo.get_by_wallet(
                wallet_address, offset=(page - 1) * limit, limit=limit
            )
            return TransactionsPagination(
                transactions=[Transaction().from_data(tx) for tx in db_transactions],
                pagination=Pagination(
                    total=len(db_transactions),
                    page=page,
                    next_page=page + 1 if page < len(db_transactions) else None,
                    prev_page=None,
                ),
            )
        except RuntimeError as e:
            self.logger.error(
                f"Database error getting txs for wallet {wallet_address}: {e}"
            )
            raise DatabaseError("getting transactions by wallet", str(e))
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting txs for wallet {wallet_address}: {e}"
            )
            raise

    async def get_all(self, page: int = 1, limit: int = 100) -> TransactionsPagination:
        """Get all transactions."""
        self.logger.info(
            f"Getting all transactions from page {page} with limit {limit}"
        )

        if page < 1:
            self.logger.error("Page must be greater than 0")
            raise InvalidPaginationError("Page must be greater than 0")

        if limit < 1:
            self.logger.error("Limit must be greater than 0")
            raise InvalidPaginationError("Limit must be greater than 0")

        if limit > 1000:
            self.logger.error("Limit must be less than 1000")
            raise InvalidPaginationError("Limit must be less than 1000")

        try:
            db_transactions = await self.tx_repo.get_all(
                offset=(page - 1) * limit, limit=limit
            )
            return TransactionsPagination(
                transactions=[Transaction().from_data(tx) for tx in db_transactions],
                pagination=Pagination(
                    total=len(db_transactions),
                    page=page,
                    next_page=page + 1 if page < len(db_transactions) else None,
                    prev_page=page - 1 if page > 1 else None,
                ),
            )
        except RuntimeError as e:
            self.logger.error(f"Database error getting all transactions: {e}")
            raise DatabaseError("getting all transactions", str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error getting all transactions: {e}")
            raise
