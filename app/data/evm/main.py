import json
import os
from typing import Any, Dict

from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from eth_typing import HexAddress
from eth_typing.evm import Hash32
from hexbytes import HexBytes
from web3 import EthereumTesterProvider, Web3
from web3.contract import Contract
from web3.gas_strategies.time_based import fast_gas_price_strategy
from web3.types import TxParams, TxReceipt


class EVMService:
    """EVM service for interacting with the EVM network."""

    def __init__(self, use_test_provider: bool, rpc_url: str, logger: Any):
        """
        Initialize the EVM service.
        """
        self.logger = logger

        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        abi_path = os.path.join(project_root, "data/evm/abi")

        # Load all ABI files from the abi folder
        self.abis: Dict[str, list] = {}
        self._load_abi_files(abi_path)

        self.w3 = (
            Web3(EthereumTesterProvider())
            if use_test_provider
            else Web3(Web3.HTTPProvider(rpc_url))
        )
        self.w3.eth.set_gas_price_strategy(fast_gas_price_strategy)

    def _load_abi_files(self, abi_path: str) -> None:
        """
        Load all JSON files from the ABI directory.

        Args:
            abi_path: Path to the ABI directory.
        """
        if not os.path.exists(abi_path):
            self.logger.warning(f"ABI directory not found: {abi_path}")
            return

        for filename in os.listdir(abi_path):
            if filename.endswith(".json"):
                file_path = os.path.join(abi_path, filename)
                try:
                    with open(file_path, "r") as f:
                        abi_name = filename.replace(".json", "")
                        self.abis[abi_name] = json.load(f)
                        self.logger.info(f"Loaded ABI: {abi_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load ABI file {filename}: {e}")

    def get_abi(self, abi_name: str) -> list:
        """
        Get an ABI by name.

        Args:
            abi_name: Name of the ABI (without .json extension).

        Returns:
            The ABI as a list.

        Raises:
            KeyError: If the ABI is not found.
        """
        if abi_name not in self.abis:
            raise KeyError(
                f"ABI '{abi_name}' not found. Available ABIs: {list(self.abis.keys())}"
            )
        return self.abis[abi_name]

    def list_available_abis(self) -> list:
        """
        Get a list of all available ABI names.

        Returns:
            List of available ABI names.
        """
        return list(self.abis.keys())

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
    def get_wallet_balance(self, wallet_address: HexAddress) -> float:
        """
        Get the balance of a wallet in network native currency.

        Args:
            wallet_address: The address of the wallet.

        Returns:
            The balance of the wallet.
        """
        balance_wei = self.w3.eth.get_balance(
            self.w3.to_checksum_address(wallet_address)
        )
        balance_eth = balance_wei / 10**18
        return balance_eth

    def get_token_contract(
        self, token_address: HexAddress, abi_name: str = "erc20"
    ) -> Contract:
        """
        Get the contract of a token.

        Args:
            token_address: The address of the token.
            abi_name: Name of the ABI to use (default: "erc20").

        Returns:
            The contract of the token.
        """
        abi = self.get_abi(abi_name)
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(token_address), abi=abi
        )

    def get_token_balance(
        self,
        wallet_address: HexAddress,
        token_address: HexAddress,
        abi_name: str = "erc20",
    ) -> float:
        """
        Get the balance of any token for a wallet using a specific ABI.
        The balance is returned in the smallest unit of the token.

        Args:
            wallet_address: The address of the wallet.
            token_address: The address of the token.
            abi_name: Name of the ABI to use (default: "erc20").

        Returns:
            The balance of the wallet.
        """
        contract = self.get_token_contract(token_address, abi_name)
        balance = contract.functions.balanceOf(wallet_address).call()
        return balance / 10**18

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

    # Get the nonce of a wallet
    def get_nonce(self, wallet_address: HexAddress) -> int:
        """
        Get the nonce of a wallet.

        Args:
            wallet_address: The address of the wallet.
        """
        return self.w3.eth.get_transaction_count(
            self.w3.to_checksum_address(wallet_address)
        )
