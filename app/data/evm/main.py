from typing import Any

from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from eth_typing import Address
from eth_typing.evm import Hash32
from hexbytes import HexBytes
from web3 import EthereumTesterProvider, Web3
from web3.types import TxParams, TxReceipt


class EVMService:
    """EVM service for interacting with the EVM network."""

    def __init__(self, use_test_provider: bool, rpc_url: str, logger: Any):
        """
        Initialize the EVM service.
        """
        self.w3 = (
            Web3(EthereumTesterProvider())
            if use_test_provider
            else Web3(Web3.HTTPProvider(rpc_url))
        )
        self.logger = logger

    # Create a new wallet
    def create_wallet(self) -> LocalAccount:
        """
        Create a new wallet.

        Returns:
            The new wallet created.
        """
        account = self.w3.eth.account.create()

        if not account.address or not account.key:
            raise RuntimeError("Failed to create wallet")

        return account

    # Get the balance of a wallet
    def get_wallet_balance(self, wallet_address: Address) -> float:
        """
        Get the balance of a wallet.

        Args:
            wallet_address: The address of the wallet.

        Returns:
            The balance of the wallet.
        """
        balance_wei = self.w3.eth.get_balance(wallet_address)
        balance_eth = balance_wei / 10**18
        return balance_eth

    # Sign transaction
    def sign_transaction(self, tx: TxParams, private_key: str) -> SignedTransaction:
        """
        Sign a transaction with a private key.

        Args:
            tx: The transaction to sign.
            private_key: The private key of the wallet.

        Returns:
            The signed transaction.
        """
        return self.w3.eth.account.sign_transaction(tx, private_key=private_key)

    # Send a transaction
    def send_transaction(self, tx: TxParams, private_key: str) -> HexBytes:
        """
        Send a transaction to the EVM network.

        Args:
            tx: The transaction to send.
            private_key: The private key of the wallet.

        Returns:
            The transaction hash.
        """
        signed_tx = self.sign_transaction(tx, private_key)
        return self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Get the transaction receipt
    def get_transaction_receipt(self, transaction_hash: Hash32) -> TxReceipt:
        """
        Get the transaction receipt.

        Args:
            transaction_hash: The hash of the transaction.

        Returns:
            The transaction receipt.
        """
        receipt = self.w3.eth.get_transaction_receipt(transaction_hash)
        if receipt is None:
            raise RuntimeError("Transaction receipt not found")
        return receipt
