from app.domain.transaction.models import Transaction


class PostgresRepository:
    # Create a new wallet
    def create_wallet(self, wallet_name: str):
        pass

    # Get the balance of a wallet
    def get_wallet_balance(self, wallet_address: str):
        pass

    # Get the transactions of a wallet
    def get_wallet_transactions(self, wallet_address: str):
        pass

    # Create a new transaction
    def create_transaction(self, transaction: Transaction):
        pass

    # Get the transaction history of a wallet
    def get_transaction_history(self, wallet_address: str):
        pass


class WalletRepository:
    def __init__(self, postgres_repository: PostgresRepository):
        self.postgres_repository = postgres_repository

    def create_wallet(self, wallet_name: str):
        self.postgres_repository.create_wallet(wallet_name)

    def get_wallet_balance(self, wallet_address: str):
        return self.postgres_repository.get_wallet_balance(wallet_address)


class TransactionRepository:
    def __init__(self, postgres_repository: PostgresRepository):
        self.postgres_repository = postgres_repository

    def create_transaction(self, transaction: Transaction):
        self.postgres_repository.create_transaction(transaction)

    def get_transaction_history(self, wallet_address: str):
        return self.postgres_repository.get_transaction_history(wallet_address)
