from typing import Any

from app.data.database import TransactionRepository
from app.domain.transaction.models import CreateTx, Transaction


class TransactionUseCases:
    """Use cases for transaction operations."""

    def __init__(self, tx_repo: TransactionRepository, logger: Any):
        self.tx_repo = tx_repo
        self.logger = logger

    async def create(self, tx_data: CreateTx) -> Transaction:
        """Create a new transaction."""
        return Transaction()

    async def get_by_id(self, transaction_id: str) -> Transaction:
        """Get transaction by ID."""
        db_transaction = await self.tx_repo.get_by_id(transaction_id)
        return Transaction().from_data(db_transaction)

    async def get_by_tx_hash(self, tx_hash: str) -> Transaction:
        """Get transaction by transaction hash."""
        db_transaction = await self.tx_repo.get_by_tx_hash(tx_hash)
        return Transaction().from_data(db_transaction)

    async def get_txs(self, wallet_address: str) -> list[Transaction]:
        """Get all transactions for a wallet."""
        db_transactions = await self.tx_repo.get_by_wallet(wallet_address)
        return [Transaction().from_data(tx) for tx in db_transactions]
