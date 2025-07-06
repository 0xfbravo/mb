from typing import Any
from uuid import UUID

from eth_typing import HexAddress
from web3.types import TxParams, Wei

from app.data.database import TransactionRepository
from app.data.evm.main import EVMService
from app.domain.assets_use_cases import AssetsUseCases
from app.domain.errors import (DatabaseError, EmptyAddressError,
                               EmptyTransactionIdError, EVMServiceError,
                               InsufficientBalanceError, InvalidAmountError,
                               InvalidNetworkError, InvalidPaginationError,
                               InvalidTxAssetError,
                               InvalidWalletPrivateKeyError, SameAddressError,
                               WalletNotFoundError)
from app.domain.tx_models import (CreateTx, Pagination, Transaction,
                                  TransactionsPagination)
from app.domain.wallet_use_cases import WalletUseCases
from app.utils.config_manager import ConfigManager


class TransactionUseCases:
    """Use cases for transaction operations."""

    def __init__(
        self,
        config_manager: ConfigManager,
        wallet_use_cases: WalletUseCases,
        assets_use_cases: AssetsUseCases,
        evm_service: EVMService,
        tx_repo: TransactionRepository,
        logger: Any,
    ):
        self.config_manager = config_manager
        self.wallet_use_cases = wallet_use_cases
        self.assets_use_cases = assets_use_cases
        self.evm_service = evm_service
        self.tx_repo = tx_repo
        self.logger = logger

    async def create(self, create_tx: CreateTx) -> Transaction:
        """Create a new transaction."""
        self.logger.info(f"Creating a new transaction for {create_tx.asset}")

        try:
            # Validate the transaction data
            current_network = self.config_manager.get_current_network()
            if current_network not in self.config_manager.get_networks():
                self.logger.error(f"Network {current_network} not available")
                raise InvalidNetworkError(current_network)

            if create_tx.amount <= 0:
                self.logger.error("Amount must be greater than 0")
                raise InvalidAmountError(create_tx.amount)

            if create_tx.from_address == create_tx.to_address:
                self.logger.error("From address and to address cannot be the same")
                raise SameAddressError(create_tx.from_address)

            if create_tx.from_address == "":
                self.logger.error("From address cannot be empty")
                raise EmptyAddressError("From")

            if create_tx.to_address == "":
                self.logger.error("To address cannot be empty")
                raise EmptyAddressError("To")

            asset_config = {}
            is_native_asset = self.assets_use_cases.is_native_asset(create_tx.asset)
            if not is_native_asset:
                asset_config = self.config_manager.get_asset(create_tx.asset)

            if current_network not in asset_config and not is_native_asset:
                self.logger.error(
                    f"Unable to transfer {create_tx.asset} on {current_network}"
                )
                raise EVMServiceError(
                    "transfer",
                    f"Unable to transfer {create_tx.asset} on {current_network}",
                )

            self.logger.info("Validating balance")
            await self.validate_balance(
                create_tx.asset,
                create_tx.from_address,
                create_tx.amount,
            )

            self.logger.info("Creating transaction data")
            tx_params = self._create_tx_params(create_tx, current_network, asset_config)
            from_wallet_private_key = await self._validate_wallet_private_key(
                create_tx.from_address
            )
            tx_hash = self.evm_service.send_transaction(
                tx_params, from_wallet_private_key
            )

            self.logger.info("Saving transaction to database in pending state")
            db_transaction = await self.tx_repo.create(
                tx_hash=tx_hash.hex(),
                asset=create_tx.asset,
                network=current_network,
                from_address=create_tx.from_address,
                to_address=create_tx.to_address,
                amount=create_tx.amount,
                gas_price=1000000000,
                gas_limit=21000,
            )

            return Transaction().from_data(db_transaction)
        except (
            InvalidTxAssetError,
            InvalidAmountError,
            SameAddressError,
            EmptyAddressError,
            InsufficientBalanceError,
            InvalidNetworkError,
            InvalidWalletPrivateKeyError,
            WalletNotFoundError,
        ):
            # Re-raise domain-specific errors as they are already properly typed
            raise
        except RuntimeError as e:
            self.logger.error(f"Database error creating transaction: {e}")
            raise DatabaseError("creating transaction", str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error creating transaction: {e}")
            raise

    async def _validate_wallet_private_key(self, from_address: str) -> str:
        """Validate that the wallet exists and has a valid private key."""
        self.logger.info(f"Validating wallet {from_address}")
        from_wallet = await self.wallet_use_cases.get_by_address(from_address)
        if from_wallet is None:
            self.logger.error(f"Wallet {from_address} not found")
            raise WalletNotFoundError(from_address)

        from_wallet_private_key = from_wallet.private_key
        if from_wallet_private_key is None or from_wallet_private_key == "":
            self.logger.error(f"Wallet {from_address} has no private key")
            raise InvalidWalletPrivateKeyError(from_address)

        self.logger.info(f"Wallet {from_address} exists and has a valid private key")
        return from_wallet_private_key

    def _create_tx_params(
        self,
        create_tx: CreateTx,
        current_network: str,
        asset_config: dict,
    ) -> TxParams:
        """Create transaction parameters for the given transaction data."""
        self.logger.info("Creating transaction parameters")
        if self.assets_use_cases.is_native_asset(create_tx.asset):
            self.logger.info("Creating native asset transaction parameters")
            return TxParams(
                to=create_tx.to_address,
                value=Wei(int(create_tx.amount * 10**18)),
            )
        else:
            self.logger.info("Getting token contract")
            contract = self.evm_service.get_token_contract(
                HexAddress(asset_config[current_network])
            )
            self.logger.info("Creating token transaction parameters")
            return contract.functions.transfer(
                create_tx.to_address, create_tx.amount * 10**18
            ).build_transaction()

    async def validate_balance(
        self,
        asset: str,
        from_address: HexAddress,
        amount: float,
    ) -> None:
        """Validate that the wallet has sufficient balance for the transaction."""
        self.logger.info(
            f"Validating user balance for transaction"
            f" of {asset} from {from_address} with amount {amount}"
        )
        balance = 0.0
        if self.assets_use_cases.is_native_asset(asset):
            balance = await self.wallet_use_cases.get_native_balance(from_address)
        else:
            balance = await self.wallet_use_cases.get_token_balance(asset, from_address)

        if balance < amount:
            self.logger.error(f"Insufficient balance for {asset}")
            raise InsufficientBalanceError(asset, balance, amount)

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
