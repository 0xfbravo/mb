"""
Unit tests for the EVM service module.

These tests verify individual functions and components in isolation.
"""

from unittest.mock import MagicMock, patch

import pytest
from eth_account.datastructures import SignedTransaction
from eth_account.signers.local import LocalAccount
from hexbytes import HexBytes
from web3.types import TxReceipt

from app.data.evm.main import EVMService


class TestEVMService:
    """Unit test cases for the EVMService class."""

    @pytest.fixture
    def mock_web3(self):
        """Create a mock Web3 instance."""
        with patch("app.data.evm.main.Web3") as mock_web3_class:
            mock_web3 = MagicMock()
            mock_web3_class.return_value = mock_web3
            mock_web3_class.HTTPProvider.return_value = MagicMock()
            yield mock_web3

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock()

    @pytest.fixture
    def evm_service(self, mock_web3, mock_logger):
        """Create an EVMService instance with mocked dependencies."""
        return EVMService(True, "http://test-rpc-url", mock_logger)

    def test_init(self, mock_web3, mock_logger):
        """Test EVMService initialization."""
        service = EVMService(True, "http://test-rpc-url", mock_logger)

        assert service.w3 == mock_web3
        assert service.logger == mock_logger

    def test_create_wallet_success(self, evm_service, mock_web3):
        """Test successful wallet creation."""
        # Mock account creation
        mock_account = MagicMock(spec=LocalAccount)
        mock_account.address = "0x1234567890123456789012345678901234567890"
        mock_account.key = b"test_private_key"

        mock_web3.eth.account.create.return_value = mock_account

        result = evm_service.create_wallet()

        assert result == mock_account
        mock_web3.eth.account.create.assert_called_once()

    def test_create_wallet_failure_no_address(self, evm_service, mock_web3):
        """Test wallet creation failure when address is None."""
        # Mock account creation with None address
        mock_account = MagicMock(spec=LocalAccount)
        mock_account.address = None
        mock_account.key = b"test_private_key"

        mock_web3.eth.account.create.return_value = mock_account

        with pytest.raises(RuntimeError, match="Failed to create wallet"):
            evm_service.create_wallet()

    def test_create_wallet_failure_no_key(self, evm_service, mock_web3):
        """Test wallet creation failure when key is None."""
        # Mock account creation with None key
        mock_account = MagicMock(spec=LocalAccount)
        mock_account.address = "0x1234567890123456789012345678901234567890"
        mock_account.key = None

        mock_web3.eth.account.create.return_value = mock_account

        with pytest.raises(RuntimeError, match="Failed to create wallet"):
            evm_service.create_wallet()

    def test_get_wallet_balance(self, evm_service, mock_web3):
        """Test getting wallet balance."""
        wallet_address = "0x1234567890123456789012345678901234567890"
        balance_wei = 1000000000000000000  # 1 ETH in wei

        mock_web3.eth.get_balance.return_value = balance_wei

        result = evm_service.get_wallet_balance(wallet_address)

        assert result == 1.0  # 1 ETH
        mock_web3.eth.get_balance.assert_called_once_with(wallet_address)

    def test_get_wallet_balance_zero(self, evm_service, mock_web3):
        """Test getting wallet balance when it's zero."""
        wallet_address = "0x1234567890123456789012345678901234567890"
        balance_wei = 0

        mock_web3.eth.get_balance.return_value = balance_wei

        result = evm_service.get_wallet_balance(wallet_address)

        assert result == 0.0
        mock_web3.eth.get_balance.assert_called_once_with(wallet_address)

    def test_get_wallet_balance_fractional(self, evm_service, mock_web3):
        """Test getting wallet balance with fractional ETH."""
        wallet_address = "0x1234567890123456789012345678901234567890"
        balance_wei = 500000000000000000  # 0.5 ETH in wei

        mock_web3.eth.get_balance.return_value = balance_wei

        result = evm_service.get_wallet_balance(wallet_address)

        assert result == 0.5
        mock_web3.eth.get_balance.assert_called_once_with(wallet_address)

    def test_sign_transaction(self, evm_service, mock_web3):
        """Test transaction signing."""
        tx_params = {
            "to": "0x1234567890123456789012345678901234567890",
            "value": 1000000000000000000,  # 1 ETH
            "gas": 21000,
            "gasPrice": 20000000000,
            "nonce": 0,
        }
        private_key = (
            "0x1234567890123456789012345678901234567890123456789012345678901234"
        )

        mock_signed_tx = MagicMock(spec=SignedTransaction)
        mock_web3.eth.account.sign_transaction.return_value = mock_signed_tx

        result = evm_service.sign_transaction(tx_params, private_key)

        assert result == mock_signed_tx
        mock_web3.eth.account.sign_transaction.assert_called_once_with(
            tx_params, private_key=private_key
        )

    def test_send_transaction(self, evm_service, mock_web3):
        """Test sending a transaction."""
        tx_params = {
            "to": "0x1234567890123456789012345678901234567890",
            "value": 1000000000000000000,  # 1 ETH
            "gas": 21000,
            "gasPrice": 20000000000,
            "nonce": 0,
        }
        private_key = (
            "0x1234567890123456789012345678901234567890123456789012345678901234"
        )

        mock_signed_tx = MagicMock(spec=SignedTransaction)
        mock_signed_tx.raw_transaction = b"raw_transaction_bytes"
        mock_web3.eth.account.sign_transaction.return_value = mock_signed_tx

        expected_hash = HexBytes(
            "0x1234567890123456789012345678901234567890123456789012345678901234"
        )
        mock_web3.eth.send_raw_transaction.return_value = expected_hash

        result = evm_service.send_transaction(tx_params, private_key)

        assert result == expected_hash
        mock_web3.eth.account.sign_transaction.assert_called_once_with(
            tx_params, private_key=private_key
        )
        mock_web3.eth.send_raw_transaction.assert_called_once_with(
            mock_signed_tx.raw_transaction
        )

    def test_get_transaction_receipt_success(self, evm_service, mock_web3):
        """Test getting transaction receipt successfully."""
        transaction_hash = (
            "0x1234567890123456789012345678901234567890123456789012345678901234"
        )

        mock_receipt = MagicMock(spec=TxReceipt)
        mock_receipt.transactionHash = transaction_hash
        mock_receipt.status = 1
        mock_web3.eth.get_transaction_receipt.return_value = mock_receipt

        result = evm_service.get_transaction_receipt(transaction_hash)

        assert result == mock_receipt
        mock_web3.eth.get_transaction_receipt.assert_called_once_with(transaction_hash)

    def test_get_transaction_receipt_not_found(self, evm_service, mock_web3):
        """Test getting transaction receipt when not found."""
        transaction_hash = (
            "0x1234567890123456789012345678901234567890123456789012345678901234"
        )

        mock_web3.eth.get_transaction_receipt.return_value = None

        with pytest.raises(RuntimeError, match="Transaction receipt not found"):
            evm_service.get_transaction_receipt(transaction_hash)

        mock_web3.eth.get_transaction_receipt.assert_called_once_with(transaction_hash)

    def test_get_transaction_receipt_with_different_hash(self, evm_service, mock_web3):
        """Test getting transaction receipt with a different hash format."""
        transaction_hash = (
            "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )

        mock_receipt = MagicMock(spec=TxReceipt)
        mock_receipt.transactionHash = transaction_hash
        mock_receipt.status = 1
        mock_web3.eth.get_transaction_receipt.return_value = mock_receipt

        result = evm_service.get_transaction_receipt(transaction_hash)

        assert result == mock_receipt
        mock_web3.eth.get_transaction_receipt.assert_called_once_with(transaction_hash)


class TestEVMServiceIntegration:
    """Integration-style tests for EVMService with more realistic scenarios."""

    @pytest.fixture
    def mock_web3(self):
        """Create a mock Web3 instance for integration tests."""
        with patch("app.data.evm.main.Web3") as mock_web3_class:
            mock_web3 = MagicMock()
            mock_web3_class.return_value = mock_web3
            mock_web3_class.HTTPProvider.return_value = MagicMock()
            yield mock_web3

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock()

    @pytest.fixture
    def evm_service(self, mock_web3, mock_logger):
        """Create an EVMService instance with mocked dependencies."""
        return EVMService(True, "http://test-rpc-url", mock_logger)

    def test_complete_transaction_flow(self, evm_service, mock_web3):
        """Test a complete transaction flow from creation to receipt."""
        # 1. Create wallet
        mock_account = MagicMock(spec=LocalAccount)
        mock_account.address = "0x1234567890123456789012345678901234567890"
        mock_account.key = b"test_private_key"
        mock_web3.eth.account.create.return_value = mock_account

        wallet = evm_service.create_wallet()
        assert wallet == mock_account

        # 2. Check initial balance
        mock_web3.eth.get_balance.return_value = 2000000000000000000  # 2 ETH
        balance = evm_service.get_wallet_balance(wallet.address)
        assert balance == 2.0

        # 3. Prepare transaction
        tx_params = {
            "to": "0xabcdef1234567890abcdef1234567890abcdef12",
            "value": 1000000000000000000,  # 1 ETH
            "gas": 21000,
            "gasPrice": 20000000000,
            "nonce": 0,
        }

        # 4. Sign transaction
        mock_signed_tx = MagicMock(spec=SignedTransaction)
        mock_signed_tx.raw_transaction = b"raw_transaction_bytes"
        mock_web3.eth.account.sign_transaction.return_value = mock_signed_tx

        signed_tx = evm_service.sign_transaction(tx_params, wallet.key.hex())
        assert signed_tx == mock_signed_tx

        # 5. Send transaction
        expected_hash = HexBytes(
            "0x1234567890123456789012345678901234567890123456789012345678901234"
        )
        mock_web3.eth.send_raw_transaction.return_value = expected_hash

        tx_hash = evm_service.send_transaction(tx_params, wallet.key.hex())
        assert tx_hash == expected_hash

        # 6. Get transaction receipt
        mock_receipt = MagicMock(spec=TxReceipt)
        mock_receipt.transactionHash = tx_hash
        mock_receipt.status = 1
        mock_receipt.blockNumber = 12345
        mock_web3.eth.get_transaction_receipt.return_value = mock_receipt

        receipt = evm_service.get_transaction_receipt(tx_hash)
        assert receipt == mock_receipt
        assert receipt.status == 1
        assert receipt.blockNumber == 12345

    def test_error_handling_scenarios(self, evm_service, mock_web3):
        """Test various error handling scenarios."""
        # Test Web3 connection error during balance check
        mock_web3.eth.get_balance.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            evm_service.get_wallet_balance("0x1234567890123456789012345678901234567890")

        # Reset the side effect
        mock_web3.eth.get_balance.side_effect = None

        # Test transaction signing error
        mock_web3.eth.account.sign_transaction.side_effect = Exception(
            "Invalid private key"
        )

        with pytest.raises(Exception, match="Invalid private key"):
            evm_service.sign_transaction({}, "invalid_key")

        # Reset the side effect
        mock_web3.eth.account.sign_transaction.side_effect = None

        # Test transaction sending error
        mock_web3.eth.send_raw_transaction.side_effect = Exception("Insufficient funds")

        with pytest.raises(Exception, match="Insufficient funds"):
            evm_service.send_transaction({}, "valid_key")

    def test_edge_cases(self, evm_service, mock_web3):
        """Test edge cases and boundary conditions."""
        # Test very large balance
        large_balance_wei = 1000000000000000000000000  # 1,000,000 ETH
        mock_web3.eth.get_balance.return_value = large_balance_wei

        balance = evm_service.get_wallet_balance(
            "0x1234567890123456789012345678901234567890"
        )
        assert balance == 1000000.0

        # Test very small balance
        small_balance_wei = 1  # 1 wei
        mock_web3.eth.get_balance.return_value = small_balance_wei

        balance = evm_service.get_wallet_balance(
            "0x1234567890123456789012345678901234567890"
        )
        assert balance == 1e-18  # 1 wei in ETH

        # Test zero balance
        mock_web3.eth.get_balance.return_value = 0
        balance = evm_service.get_wallet_balance(
            "0x1234567890123456789012345678901234567890"
        )
        assert balance == 0.0
