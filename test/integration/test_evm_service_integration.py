"""
Integration tests for the EVM service.

These tests verify that the EVM service works correctly with the test provider,
testing all major functionality including wallet creation, balance checking,
transaction signing, and sending.
"""

import pytest
from eth_account.datastructures import SignedTransaction
from hexbytes import HexBytes

from app.data.evm.main import EVMService
from app.utils.setup_log import setup_loguru


class TestEVMServiceIntegration:
    """Integration test cases for the EVM service with test provider."""

    @pytest.fixture
    def evm_service(self):
        """Create an EVM service instance with test provider."""
        setup_loguru()
        from loguru import logger
        return EVMService(use_test_provider=True, rpc_url="", logger=logger)

    @pytest.fixture
    def test_wallet(self, evm_service):
        """Create a test wallet for transaction testing."""
        return evm_service.create_wallet()

    @pytest.fixture
    def test_wallet_2(self, evm_service):
        """Create a second test wallet for transaction testing."""
        return evm_service.create_wallet()

    def test_evm_service_initialization(self, evm_service):
        """Test that the EVM service is properly initialized with test provider."""
        assert evm_service is not None
        assert evm_service.w3 is not None
        assert evm_service.logger is not None
        # Verify we're using the test provider
        assert "EthereumTesterProvider" in str(type(evm_service.w3.provider))

    def test_wallet_creation(self, evm_service):
        """Test wallet creation functionality."""
        wallet = evm_service.create_wallet()
        
        assert wallet is not None
        assert wallet.address is not None
        assert wallet.key is not None
        assert len(wallet.address) == 42  # 0x + 40 hex chars
        assert len(wallet.key.hex()) == 64  # 32 bytes = 64 hex chars

    def test_wallet_balance_initial(self, evm_service, test_wallet):
        """Test getting initial wallet balance (should be 0 in test provider)."""
        balance = evm_service.get_wallet_balance(test_wallet.address)
        assert balance == 0.0

    def test_wallet_balance_after_funding(self, evm_service, test_wallet):
        """Test wallet balance after funding from test provider."""
        # Fund the wallet using test provider
        evm_service.w3.eth.send_transaction({
            'from': evm_service.w3.eth.accounts[0],
            'to': test_wallet.address,
            'value': evm_service.w3.to_wei(1, 'ether')
        })
        
        balance = evm_service.get_wallet_balance(test_wallet.address)
        assert balance == 1.0

    def test_transaction_signing(self, evm_service, test_wallet, test_wallet_2):
        """Test transaction signing functionality."""
        # Create a transaction
        tx = {
            'to': test_wallet_2.address,
            'value': evm_service.w3.to_wei(0.1, 'ether'),
            'gas': 21000,
            'gasPrice': evm_service.w3.eth.gas_price,
            'nonce': evm_service.w3.eth.get_transaction_count(test_wallet.address),
            'chainId': evm_service.w3.eth.chain_id
        }
        
        # Sign the transaction
        signed_tx = evm_service.sign_transaction(tx, test_wallet.key.hex())
        
        assert isinstance(signed_tx, SignedTransaction)
        assert signed_tx.raw_transaction is not None
        assert signed_tx.hash is not None
        assert signed_tx.r is not None
        assert signed_tx.s is not None
        assert signed_tx.v is not None

    def test_transaction_sending(self, evm_service, test_wallet, test_wallet_2):
        """Test transaction sending functionality."""
        # Fund the sender wallet first
        evm_service.w3.eth.send_transaction({
            'from': evm_service.w3.eth.accounts[0],
            'to': test_wallet.address,
            'value': evm_service.w3.to_wei(1, 'ether')
        })
        
        # Create and send a transaction
        tx = {
            'to': test_wallet_2.address,
            'value': evm_service.w3.to_wei(0.1, 'ether'),
            'gas': 21000,
            'gasPrice': evm_service.w3.eth.gas_price,
            'nonce': evm_service.w3.eth.get_transaction_count(test_wallet.address),
            'chainId': evm_service.w3.eth.chain_id
        }
        
        tx_hash = evm_service.send_transaction(tx, test_wallet.key.hex())
        
        assert isinstance(tx_hash, HexBytes)
        assert len(tx_hash.hex()) == 64  # 64 hex chars (without 0x prefix)

    def test_transaction_receipt(self, evm_service, test_wallet, test_wallet_2):
        """Test getting transaction receipt."""
        # Fund the sender wallet first
        evm_service.w3.eth.send_transaction({
            'from': evm_service.w3.eth.accounts[0],
            'to': test_wallet.address,
            'value': evm_service.w3.to_wei(1, 'ether')
        })
        
        # Create and send a transaction
        tx = {
            'to': test_wallet_2.address,
            'value': evm_service.w3.to_wei(0.1, 'ether'),
            'gas': 21000,
            'gasPrice': evm_service.w3.eth.gas_price,
            'nonce': evm_service.w3.eth.get_transaction_count(test_wallet.address),
            'chainId': evm_service.w3.eth.chain_id
        }
        
        tx_hash = evm_service.send_transaction(tx, test_wallet.key.hex())
        
        # Get the transaction receipt
        receipt = evm_service.get_transaction_receipt(tx_hash)
        
        assert receipt is not None
        assert receipt['transactionHash'] == tx_hash
        assert receipt['status'] == 1  # Success
        assert receipt['to'].lower() == test_wallet_2.address.lower()

    def test_complete_transaction_flow(self, evm_service):
        """Test a complete transaction flow from wallet creation to receipt."""
        # Create two wallets
        wallet1 = evm_service.create_wallet()
        wallet2 = evm_service.create_wallet()
        
        # Fund wallet1
        evm_service.w3.eth.send_transaction({
            'from': evm_service.w3.eth.accounts[0],
            'to': wallet1.address,
            'value': evm_service.w3.to_wei(2, 'ether')
        })
        
        # Verify wallet1 has funds
        balance1_before = evm_service.get_wallet_balance(wallet1.address)
        assert balance1_before == 2.0
        
        # Send transaction from wallet1 to wallet2
        tx = {
            'to': wallet2.address,
            'value': evm_service.w3.to_wei(0.5, 'ether'),
            'gas': 21000,
            'gasPrice': evm_service.w3.eth.gas_price,
            'nonce': evm_service.w3.eth.get_transaction_count(wallet1.address),
            'chainId': evm_service.w3.eth.chain_id
        }
        
        # Sign and send transaction
        signed_tx = evm_service.sign_transaction(tx, wallet1.key.hex())
        tx_hash = evm_service.send_transaction(tx, wallet1.key.hex())
        
        # Get receipt
        receipt = evm_service.get_transaction_receipt(tx_hash)
        
        # Verify transaction was successful
        assert receipt['status'] == 1
        assert receipt['transactionHash'] == tx_hash
        
        # Verify balances changed
        balance1_after = evm_service.get_wallet_balance(wallet1.address)
        balance2_after = evm_service.get_wallet_balance(wallet2.address)
        
        # Wallet1 should have less than 2.0 (due to gas fees)
        assert balance1_after < 2.0
        # Wallet2 should have 0.5
        assert balance2_after == 0.5

    def test_invalid_transaction_handling(self, evm_service, test_wallet):
        """Test handling of invalid transactions."""
        # Try to send transaction without funds
        tx = {
            'to': test_wallet.address,
            'value': evm_service.w3.to_wei(1, 'ether'),
            'gas': 21000,
            'gasPrice': evm_service.w3.eth.gas_price,
            'nonce': evm_service.w3.eth.get_transaction_count(test_wallet.address),
            'chainId': evm_service.w3.eth.chain_id
        }
        
        # This should raise an exception due to insufficient funds
        with pytest.raises(Exception):
            evm_service.send_transaction(tx, test_wallet.key.hex())

    def test_invalid_transaction_receipt(self, evm_service):
        """Test handling of invalid transaction hash."""
        invalid_hash = "0x" + "0" * 64
        
        with pytest.raises(Exception):  # TransactionNotFound or RuntimeError
            evm_service.get_transaction_receipt(invalid_hash)

    def test_multiple_wallets_and_transactions(self, evm_service):
        """Test creating multiple wallets and performing multiple transactions."""
        # Create multiple wallets
        wallets = [evm_service.create_wallet() for _ in range(3)]
        
        # Fund the first wallet
        evm_service.w3.eth.send_transaction({
            'from': evm_service.w3.eth.accounts[0],
            'to': wallets[0].address,
            'value': evm_service.w3.to_wei(3, 'ether')
        })
        
        # Perform chain of transactions: wallet0 -> wallet1 -> wallet2
        for i in range(2):
            sender = wallets[i]
            receiver = wallets[i + 1]
            
            # Calculate gas cost
            gas_price = evm_service.w3.eth.gas_price
            gas_limit = 21000
            gas_cost = gas_price * gas_limit
            sender_balance = evm_service.w3.eth.get_balance(sender.address)
            # Send almost all, but leave enough for gas
            tx_value = sender_balance - gas_cost - 1  # leave 1 wei buffer
            if tx_value <= 0:
                raise Exception("Not enough balance to send transaction including gas")
            
            tx = {
                'to': receiver.address,
                'value': tx_value,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': evm_service.w3.eth.get_transaction_count(sender.address),
                'chainId': evm_service.w3.eth.chain_id
            }
            
            tx_hash = evm_service.send_transaction(tx, sender.key.hex())
            receipt = evm_service.get_transaction_receipt(tx_hash)
            
            assert receipt['status'] == 1
            assert receipt['to'].lower() == receiver.address.lower()
        
        # Verify final balances
        balance0 = evm_service.get_wallet_balance(wallets[0].address)
        balance1 = evm_service.get_wallet_balance(wallets[1].address)
        balance2 = evm_service.get_wallet_balance(wallets[2].address)
        
        assert balance0 < 3.0  # Less than 3 due to gas fees
        assert balance1 > 0.0  # Should have some balance after receiving and sending
        assert balance2 > 0.0  # Should have received some ETH 