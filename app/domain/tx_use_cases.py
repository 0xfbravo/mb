import asyncio
from typing import Any, List, Sequence
from uuid import UUID

from eth_typing import Hash32, HexAddress, HexStr
from hexbytes import HexBytes
from web3.types import LogReceipt, TxParams, Wei

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
                                  TransactionsPagination,
                                  TransactionValidation, TransferInfo)
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

    async def validate_transaction(self, tx_hash: str) -> TransactionValidation:
        """
        Validate a transaction hash to determine if it's safe for credit generation.

        This method:
        1. Fetches the transaction receipt from the blockchain
        2. Identifies if it's an ETH or ERC-20 transfer
        3. Validates if the destination address is one of our generated addresses
        4. Extracts transfer information
        5. Stores valid transactions in the database

        Args:
            tx_hash: The transaction hash to validate

        Returns:
            TransactionValidation object with validation results and transfer details
        """
        self.logger.info(f"Validating transaction {tx_hash}")

        if not tx_hash or tx_hash.strip() == "":
            self.logger.error("Transaction hash is required")
            raise EmptyAddressError("Transaction hash")

        try:
            # Check if transaction already exists in database
            try:
                existing_tx = await self.tx_repo.get_by_tx_hash(tx_hash)
                self.logger.info(f"Transaction {tx_hash} already exists in database")
                return TransactionValidation(
                    is_valid=True,
                    transaction_hash=tx_hash,
                    transfers=[
                        TransferInfo(
                            asset=existing_tx.asset,
                            destination_address=existing_tx.to_address,
                            amount=existing_tx.amount,
                            token_address=(
                                None
                                if self.assets_use_cases.is_native_asset(
                                    existing_tx.asset
                                )
                                else self.assets_use_cases.get_asset_address(
                                    existing_tx.asset
                                )
                            ),
                        )
                    ],
                    validation_message="Transaction already validated and stored",
                    network=existing_tx.network,
                )
            except Exception:
                # Transaction not found in database, continue with validation
                pass

            # Convert string to Hash32 for EVM service
            tx_hash_bytes = Hash32(HexBytes(tx_hash))

            # Get transaction receipt from blockchain
            tx_receipt = self.evm_service.get_transaction_receipt(tx_hash_bytes)
            self.logger.info(f"Retrieved transaction receipt for {tx_hash}")

            # Get transaction details
            tx = self.evm_service.w3.eth.get_transaction(tx_hash_bytes)

            current_network = self.config_manager.get_current_network()
            transfers: List[TransferInfo] = []
            is_valid = False
            validation_message = ""

            # Check if transaction was successful
            if tx_receipt.get("status") != 1:
                validation_message = "Transaction failed or was reverted"
                return TransactionValidation(
                    is_valid=False,
                    transaction_hash=tx_hash,
                    transfers=transfers,
                    validation_message=validation_message,
                    network=current_network,
                )

            # Check if it's a native ETH transfer
            if tx.get("to") and (not tx.get("input") or tx.get("input") == "0x"):
                # Native ETH transfer
                to_address = tx.get("to")
                if to_address:
                    amount_wei = tx.get("value", 0)
                    amount_eth = amount_wei / 10**18

                    # Check if destination is one of our addresses
                    try:
                        await self.wallet_use_cases.get_by_address(str(to_address))
                        is_valid = True
                        validation_message = (
                            f"Valid ETH transfer of {amount_eth} ETH to our address"
                        )
                        transfers.append(
                            TransferInfo(
                                asset="ETH",
                                destination_address=str(to_address),
                                amount=amount_eth,
                                token_address=None,
                            )
                        )
                    except Exception:
                        validation_message = f"ETH transfer destination {to_address} is not one of our addresses"  # noqa: E501

            else:
                # ERC-20 or other contract interaction
                # Parse Transfer events from logs
                transfer_events = self._parse_transfer_events(
                    tx_receipt.get("logs", [])
                )

                for event in transfer_events:
                    to_address = event["to"]
                    token_address = event["token_address"]
                    amount = event["amount"]

                    # Try to identify the asset
                    asset_name = self._identify_asset(token_address)

                    # Check if destination is one of our addresses
                    try:
                        await self.wallet_use_cases.get_by_address(to_address)
                        is_valid = True
                        validation_message = (
                            f"Valid {asset_name} transfer of {amount} to our address"
                        )
                        transfers.append(
                            TransferInfo(
                                asset=asset_name,
                                destination_address=to_address,
                                amount=amount,
                                token_address=token_address,
                            )
                        )
                    except Exception:
                        validation_message = f"{asset_name} transfer destination {to_address} is not one of our addresses"  # noqa: E501
                        break

            # Store valid transaction in database
            if is_valid and transfers:
                try:
                    transfer = transfers[0]  # Take the first transfer for storage
                    await self.tx_repo.create(
                        tx_hash=tx_hash,
                        asset=transfer.asset,
                        network=current_network,
                        from_address=str(tx.get("from", "")),
                        to_address=transfer.destination_address,
                        amount=transfer.amount,
                        gas_price=tx.get("gasPrice", 0),
                        gas_limit=tx.get("gas", 0),
                    )
                    self.logger.info(f"Stored valid transaction {tx_hash} in database")
                except Exception as e:
                    self.logger.error(f"Failed to store transaction {tx_hash}: {e}")
                    # Don't fail validation if storage fails

            return TransactionValidation(
                is_valid=is_valid,
                transaction_hash=tx_hash,
                transfers=transfers,
                validation_message=validation_message,
                network=current_network,
            )

        except Exception as e:
            self.logger.error(f"Error validating transaction {tx_hash}: {e}")
            raise

    def _parse_transfer_events(self, logs: Sequence[LogReceipt]) -> List[dict]:
        """
        Parse Transfer events from transaction logs.

        Args:
            logs: List of log entries from transaction receipt

        Returns:
            List of parsed transfer events
        """
        transfer_events = []

        # ERC-20 Transfer event signature: Transfer(address,address,uint256)
        transfer_event_signature = (
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        )

        for log in logs:
            if log.get("topics") and log["topics"][0] == transfer_event_signature:
                try:
                    # Parse Transfer event data
                    # topics[0] = event signature
                    # topics[1] = from address (indexed)
                    # topics[2] = to address (indexed)
                    # data = amount (not indexed)

                    from_address = "0x" + str(log["topics"][1])[-40:]  # Remove padding
                    to_address = "0x" + str(log["topics"][2])[-40:]  # Remove padding
                    amount_wei = int(log["data"], 16)

                    # Try to get decimals from token contract
                    token_address = log["address"]
                    try:
                        token_contract = self.evm_service.get_token_contract(
                            HexAddress(HexStr(token_address))
                        )
                        decimals = token_contract.functions.decimals().call()
                        amount = amount_wei / 10**decimals
                    except Exception:
                        # Default to 18 decimals if we can't get them
                        amount = amount_wei / 10**18

                    transfer_events.append(
                        {
                            "from": from_address,
                            "to": to_address,
                            "amount": amount,
                            "token_address": token_address,
                        }
                    )

                except Exception as e:
                    self.logger.warning(f"Failed to parse transfer event: {e}")
                    continue

        return transfer_events

    def _identify_asset(self, token_address: str) -> str:
        """
        Try to identify the asset name from token address.

        Args:
            token_address: The token contract address

        Returns:
            Asset name or token address if not recognized
        """
        try:
            # Check if it's a known asset in our config
            current_network = self.config_manager.get_current_network()
            assets = self.config_manager.get_assets()

            if isinstance(assets, dict):
                for asset_name, asset_config in assets.items():
                    if (
                        current_network in asset_config
                        and asset_config[current_network].lower()
                        == token_address.lower()
                    ):
                        return asset_name

            # Try to get symbol from contract
            token_contract = self.evm_service.get_token_contract(
                HexAddress(HexStr(token_address))
            )
            symbol = token_contract.functions.symbol().call()
            return symbol

        except Exception:
            # Return token address if we can't identify it
            return f"Token({token_address[:10]}...)"

    async def create(self, create_tx: CreateTx) -> Transaction:
        """
        Create a new transaction.

        Args:
            create_tx: The transaction data to create.

        Returns:
            The created transaction.
        """
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
        """
        Validate that the wallet exists and has a valid private key.

        Args:
            from_address: The address of the wallet to validate.

        Returns:
            The private key of the wallet.
        """
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
        """
        Create transaction parameters for the given transaction data.

        Args:
            create_tx: The transaction data to create the parameters for.
            current_network: The current network.
            asset_config: The asset configuration.

        Returns:
            The transaction parameters.
        """
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
        """
        Validate that the wallet has sufficient balance for the transaction.

        Args:
            asset: The asset to validate the balance for.
            from_address: The address of the wallet to validate the balance for.
            amount: The amount of the transaction.
        """
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
        """
        Get transaction by ID.

        Args:
            transaction_id: The ID of the transaction to get.

        Returns:
            The transaction if found.
        """
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
        """
        Get transaction by transaction hash.

        If the transaction is not found in our database
        we will try to get it from the blockchain.

        If the transaction is found in the blockchain,
        we will save it to our database.

        If none of the above is possible, we will raise an error.

        Args:
            tx_hash: The transaction hash to get.

        Returns:
            The transaction if found.
        """
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
        self, wallet: str, page: int = 1, limit: int = 100
    ) -> TransactionsPagination:
        """
        Get all transactions for a wallet.

        Args:
            wallet: The address of the wallet to get the transactions for.
            page: The page number to get.
            limit: The number of transactions to get per page.

        Returns:
            The transactions pagination.
        """
        self.logger.info(
            f"Getting all transactions for wallet {wallet}"
            f"from page {page} with limit {limit}"
        )

        if wallet == "":
            self.logger.error("Wallet address is required")
            raise EmptyAddressError("Wallet")

        if page < 1:
            self.logger.error("Page must be greater than 0")
            raise InvalidPaginationError("Page must be greater than 0")

        if limit < 1:
            self.logger.error("Limit must be greater than 0")
            raise InvalidPaginationError("Limit must be greater than 0")

        try:
            # Get paginated transactions and total count
            db_transactions, total = await asyncio.gather(
                self.tx_repo.get_by_wallet(
                    wallet, offset=(page - 1) * limit, limit=limit
                ),
                self.tx_repo.get_count_by_wallet(wallet),
            )

            transactions = [Transaction().from_data(tx) for tx in db_transactions]

            # Calculate pagination metadata
            total_pages = (total + limit - 1) // limit
            current_page = page
            tx_count = len(transactions)

            self.logger.info(
                f"Successfully retrieved {tx_count} of {total} txs for wallet {wallet}"
            )

            return TransactionsPagination(
                transactions=transactions,
                pagination=Pagination(
                    total=total,
                    page=current_page,
                    next_page=current_page + 1 if current_page < total_pages else None,
                    prev_page=current_page - 1 if current_page > 1 else None,
                ),
            )
        except RuntimeError as e:
            self.logger.error(f"Database error getting txs for wallet {wallet}: {e}")
            raise DatabaseError("getting transactions by wallet", str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error getting txs for wallet {wallet}: {e}")
            raise

    async def get_all(self, page: int = 1, limit: int = 100) -> TransactionsPagination:
        """
        Get all transactions.

        Args:
            page: The page number to get.
            limit: The number of transactions to get per page.

        Returns:
            The transactions pagination.
        """
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
            # Get paginated transactions and total count
            db_transactions, total = await asyncio.gather(
                self.tx_repo.get_all(offset=(page - 1) * limit, limit=limit),
                self.tx_repo.get_count(),
            )

            transactions = [Transaction().from_data(tx) for tx in db_transactions]

            # Calculate pagination metadata
            total_pages = (total + limit - 1) // limit
            current_page = page

            self.logger.info(
                f"Successfully retrieved {len(transactions)} of {total} txs"
            )

            return TransactionsPagination(
                transactions=transactions,
                pagination=Pagination(
                    total=total,
                    page=current_page,
                    next_page=current_page + 1 if current_page < total_pages else None,
                    prev_page=current_page - 1 if current_page > 1 else None,
                ),
            )
        except RuntimeError as e:
            self.logger.error(f"Database error getting all transactions: {e}")
            raise DatabaseError("getting all transactions", str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error getting all transactions: {e}")
            raise
