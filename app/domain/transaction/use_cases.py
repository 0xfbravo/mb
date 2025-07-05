from typing import Any
from uuid import UUID

from app.data.database import TransactionRepository
from app.domain.transaction.models import (CreateTx, Pagination, Transaction,
                                           TransactionsPagination)


class TransactionUseCases:
    """Use cases for transaction operations."""

    def __init__(self, tx_repo: TransactionRepository, logger: Any):
        self.tx_repo = tx_repo
        self.logger = logger

    async def create(self, tx_data: CreateTx) -> Transaction:
        """Create a new transaction."""
        try:
            # TODO: Implement transaction creation
            db_transaction = await self.tx_repo.create(
                wallet_address=tx_data.from_address,
                amount=tx_data.amount,
                currency="ETH",
                gas_price=1000000000,
                gas_limit=21000,
            )
            return Transaction().from_data(db_transaction)
        except RuntimeError as e:
            self.logger.error(f"Database error creating transaction: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating transaction: {e}")
            raise

    async def get_by_id(self, transaction_id: UUID) -> Transaction:
        """Get transaction by ID."""
        try:
            db_transaction = await self.tx_repo.get_by_id(transaction_id)
            return Transaction().from_data(db_transaction)
        except RuntimeError as e:
            self.logger.error(
                f"Database error getting transaction {transaction_id}: {e}"
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting transaction {transaction_id}: {e}"
            )
            raise

    async def get_by_tx_hash(self, tx_hash: str) -> Transaction:
        """Get transaction by transaction hash."""
        try:
            db_transaction = await self.tx_repo.get_by_tx_hash(tx_hash)
            return Transaction().from_data(db_transaction)
        except RuntimeError as e:
            self.logger.error(
                f"Database error getting transaction by hash {tx_hash}: {e}"
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting transaction by hash {tx_hash}: {e}"
            )
            raise

    async def get_txs(
        self, wallet_address: str, page: int = 1, limit: int = 100
    ) -> TransactionsPagination:
        """Get all transactions for a wallet."""
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
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting txs for wallet {wallet_address}: {e}"
            )
            raise

    async def get_all(self, page: int = 1, limit: int = 100) -> TransactionsPagination:
        """Get all transactions."""
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
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting all transactions: {e}")
            raise
