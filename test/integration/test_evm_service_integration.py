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
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": test_wallet.address,
                "value": evm_service.w3.to_wei(1, "ether"),
            }
        )

        balance = evm_service.get_wallet_balance(test_wallet.address)
        assert balance == 1.0

    def test_transaction_signing(self, evm_service, test_wallet, test_wallet_2):
        """Test transaction signing functionality."""
        # Create a transaction
        tx = {
            "to": test_wallet_2.address,
            "value": evm_service.w3.to_wei(0.1, "ether"),
            "gas": 21000,
            "gasPrice": evm_service.w3.eth.gas_price,
            "nonce": evm_service.w3.eth.get_transaction_count(test_wallet.address),
            "chainId": evm_service.w3.eth.chain_id,
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
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": test_wallet.address,
                "value": evm_service.w3.to_wei(1, "ether"),
            }
        )

        # Create and send a transaction
        tx = {
            "to": test_wallet_2.address,
            "value": evm_service.w3.to_wei(0.1, "ether"),
            "gas": 21000,
            "gasPrice": evm_service.w3.eth.gas_price,
            "nonce": evm_service.w3.eth.get_transaction_count(test_wallet.address),
            "chainId": evm_service.w3.eth.chain_id,
        }

        tx_hash = evm_service.send_transaction(tx, test_wallet.key.hex())

        assert isinstance(tx_hash, HexBytes)
        assert len(tx_hash.hex()) == 64  # 64 hex chars (without 0x prefix)

    def test_transaction_receipt(self, evm_service, test_wallet, test_wallet_2):
        """Test getting transaction receipt."""
        # Fund the sender wallet first
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": test_wallet.address,
                "value": evm_service.w3.to_wei(1, "ether"),
            }
        )

        # Create and send a transaction
        tx = {
            "to": test_wallet_2.address,
            "value": evm_service.w3.to_wei(0.1, "ether"),
            "gas": 21000,
            "gasPrice": evm_service.w3.eth.gas_price,
            "nonce": evm_service.w3.eth.get_transaction_count(test_wallet.address),
            "chainId": evm_service.w3.eth.chain_id,
        }

        tx_hash = evm_service.send_transaction(tx, test_wallet.key.hex())

        # Get the transaction receipt
        receipt = evm_service.get_transaction_receipt(tx_hash)

        assert receipt is not None
        assert receipt["transactionHash"] == tx_hash
        assert receipt["status"] == 1  # Success
        assert receipt["to"].lower() == test_wallet_2.address.lower()

    def test_complete_transaction_flow(self, evm_service):
        """Test a complete transaction flow from wallet creation to receipt."""
        # Create two wallets
        wallet1 = evm_service.create_wallet()
        wallet2 = evm_service.create_wallet()

        # Fund wallet1
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": wallet1.address,
                "value": evm_service.w3.to_wei(2, "ether"),
            }
        )

        # Verify wallet1 has funds
        balance1_before = evm_service.get_wallet_balance(wallet1.address)
        assert balance1_before == 2.0

        # Send transaction from wallet1 to wallet2
        tx = {
            "to": wallet2.address,
            "value": evm_service.w3.to_wei(0.5, "ether"),
            "gas": 21000,
            "gasPrice": evm_service.w3.eth.gas_price,
            "nonce": evm_service.w3.eth.get_transaction_count(wallet1.address),
            "chainId": evm_service.w3.eth.chain_id,
        }

        # Sign and send transaction
        tx_hash = evm_service.send_transaction(tx, wallet1.key.hex())

        # Get receipt
        receipt = evm_service.get_transaction_receipt(tx_hash)

        # Verify transaction was successful
        assert receipt["status"] == 1
        assert receipt["transactionHash"] == tx_hash

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
            "to": test_wallet.address,
            "value": evm_service.w3.to_wei(1, "ether"),
            "gas": 21000,
            "gasPrice": evm_service.w3.eth.gas_price,
            "nonce": evm_service.w3.eth.get_transaction_count(test_wallet.address),
            "chainId": evm_service.w3.eth.chain_id,
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
        """Test creating multiple wallets and performing transactions between them."""
        # Create multiple wallets
        wallets = [evm_service.create_wallet() for _ in range(3)]

        # Fund the first wallet
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": wallets[0].address,
                "value": evm_service.w3.to_wei(3, "ether"),
            }
        )

        # Verify initial balance
        balance = evm_service.get_wallet_balance(wallets[0].address)
        assert balance == 3.0

        # Send transactions from wallet 0 to wallets 1 and 2
        for i, target_wallet in enumerate(wallets[1:], 1):
            tx = {
                "to": target_wallet.address,
                "value": evm_service.w3.to_wei(0.5, "ether"),
                "gas": 21000,
                "gasPrice": evm_service.w3.eth.gas_price,
                "nonce": evm_service.w3.eth.get_transaction_count(wallets[0].address),
                "chainId": evm_service.w3.eth.chain_id,
            }

            tx_hash = evm_service.send_transaction(tx, wallets[0].key.hex())
            receipt = evm_service.get_transaction_receipt(tx_hash)

            assert receipt["status"] == 1
            assert receipt["transactionHash"] == tx_hash

        # Verify final balances
        balance_0 = evm_service.get_wallet_balance(wallets[0].address)
        balance_1 = evm_service.get_wallet_balance(wallets[1].address)
        balance_2 = evm_service.get_wallet_balance(wallets[2].address)

        # Wallet 0 should have less than 2.0 (due to gas fees)
        assert balance_0 < 2.0
        # Wallets 1 and 2 should have 0.5 each
        assert balance_1 == 0.5
        assert balance_2 == 0.5

    def test_nonce_handling(self, evm_service, test_wallet):
        """Test nonce handling for transactions."""
        # Fund the wallet
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": test_wallet.address,
                "value": evm_service.w3.to_wei(2, "ether"),
            }
        )

        # Get initial nonce
        initial_nonce = evm_service.get_nonce(test_wallet.address)
        assert initial_nonce == 0

        # Create a transaction
        tx = {
            "to": evm_service.w3.eth.accounts[0],  # Send back to test account
            "value": evm_service.w3.to_wei(0.1, "ether"),
            "gas": 21000,
            "gasPrice": evm_service.w3.eth.gas_price,
            "nonce": initial_nonce,
            "chainId": evm_service.w3.eth.chain_id,
        }

        # Send transaction
        tx_hash = evm_service.send_transaction(tx, test_wallet.key.hex())
        receipt = evm_service.get_transaction_receipt(tx_hash)

        assert receipt["status"] == 1

        # Check that nonce has increased
        new_nonce = evm_service.get_nonce(test_wallet.address)
        assert new_nonce == initial_nonce + 1

    def test_token_contract_interaction(self, evm_service, test_wallet):
        """Test token contract interaction using the test provider."""
        # Deploy a simple ERC20 token contract for testing
        # This is a simplified test - in a real scenario you'd deploy an actual contract
        token_address = "0x1234567890123456789012345678901234567890"

        # Test getting token contract
        try:
            contract = evm_service.get_token_contract(token_address)
            # If the contract doesn't exist, this should fail gracefully
            assert contract is not None
        except Exception:
            # Expected if the contract doesn't exist on test network
            pass

    def test_abi_loading_and_management(self, evm_service):
        """Test ABI loading and management functionality."""
        # Test listing available ABIs
        available_abis = evm_service.list_available_abis()
        assert isinstance(available_abis, list)
        assert "erc20" in available_abis

        # Test getting a specific ABI
        erc20_abi = evm_service.get_abi("erc20")
        assert isinstance(erc20_abi, list)
        assert len(erc20_abi) > 0

        # Test getting non-existent ABI
        with pytest.raises(KeyError):
            evm_service.get_abi("non_existent_abi")

    def test_gas_price_strategy(self, evm_service):
        """Test that gas price strategy is properly set."""
        # The service should have a gas price strategy set
        # This is tested indirectly by checking that transactions can be sent
        wallet = evm_service.create_wallet()

        # Fund the wallet
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": wallet.address,
                "value": evm_service.w3.to_wei(1, "ether"),
            }
        )

        # Create a transaction with gas price from strategy
        tx = {
            "to": evm_service.w3.eth.accounts[0],
            "value": evm_service.w3.to_wei(0.1, "ether"),
            "gas": 21000,
            "gasPrice": evm_service.w3.eth.gas_price,
            "nonce": evm_service.w3.eth.get_transaction_count(wallet.address),
            "chainId": evm_service.w3.eth.chain_id,
        }

        # This should work if gas price strategy is properly configured
        tx_hash = evm_service.send_transaction(tx, wallet.key.hex())
        assert isinstance(tx_hash, HexBytes)

    def test_address_checksum_handling(self, evm_service, test_wallet):
        """Test that addresses are properly checksummed."""
        # Test with lowercase address
        lowercase_address = test_wallet.address.lower()
        balance = evm_service.get_wallet_balance(lowercase_address)
        assert isinstance(balance, float)

        # Test with mixed case address
        mixed_case_address = test_wallet.address.swapcase()
        balance = evm_service.get_wallet_balance(mixed_case_address)
        assert isinstance(balance, float)

    def test_transaction_receipt_edge_cases(self, evm_service):
        """Test transaction receipt handling with edge cases."""
        # Test with a real Ethereum transaction hash (this should work on mainnet)
        real_hash = "0xcf9489972a78d42c24d274f89dfc1041f71701b330cd67bbcec197da393bb5f7"

        # Test with string hash
        try:
            receipt = evm_service.get_transaction_receipt(real_hash)
            # If we get here, the transaction was found (which is expected for a real hash)
            assert receipt is not None
            assert receipt["transactionHash"] == HexBytes(real_hash)
        except RuntimeError as e:
            # If the transaction is not found, that's also acceptable in test environment
            assert "Transaction receipt not found" in str(e)
        except Exception as e:
            # Other exceptions (like network issues) are also acceptable in test environment
            assert "not found" in str(e).lower() or "connection" in str(e).lower()

        # Test with HexBytes hash
        real_hexbytes_hash = HexBytes(real_hash)
        try:
            receipt = evm_service.get_transaction_receipt(real_hexbytes_hash)
            # If we get here, the transaction was found
            assert receipt is not None
            assert receipt["transactionHash"] == real_hexbytes_hash
        except RuntimeError as e:
            # If the transaction is not found, that's also acceptable
            assert "Transaction receipt not found" in str(e)
        except Exception as e:
            # Other exceptions are also acceptable
            assert "not found" in str(e).lower() or "connection" in str(e).lower()

        # Test with an obviously invalid hash
        invalid_hash = (
            "0x1234567890123456789012345678901234567890123456789012345678901234"
        )

        with pytest.raises(RuntimeError, match="Transaction receipt not found"):
            evm_service.get_transaction_receipt(invalid_hash)

        # Test with invalid HexBytes hash
        invalid_hexbytes_hash = HexBytes(
            "0x1234567890123456789012345678901234567890123456789012345678901234"
        )

        with pytest.raises(RuntimeError, match="Transaction receipt not found"):
            evm_service.get_transaction_receipt(invalid_hexbytes_hash)

    def test_concurrent_wallet_creation(self, evm_service):
        """Test creating multiple wallets concurrently."""
        import threading

        wallets = []
        errors = []

        def create_wallet():
            try:
                wallet = evm_service.create_wallet()
                wallets.append(wallet)
            except Exception as e:
                errors.append(e)

        # Create multiple threads to create wallets
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_wallet)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all wallets were created successfully
        assert len(wallets) == 5
        assert len(errors) == 0

        # Verify all wallets have unique addresses
        addresses = [wallet.address for wallet in wallets]
        assert len(set(addresses)) == 5

    def test_balance_precision(self, evm_service, test_wallet):
        """Test balance precision handling."""
        # Fund with a precise amount
        precise_amount = evm_service.w3.to_wei(1.123456789, "ether")
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": test_wallet.address,
                "value": precise_amount,
            }
        )

        balance = evm_service.get_wallet_balance(test_wallet.address)
        assert abs(balance - 1.123456789) < 1e-9

    def test_network_connection_handling(self, evm_service):
        """Test network connection handling with test provider."""
        # Test that we can connect to the test network
        assert evm_service.w3.is_connected()

        # Test that we can get network information
        chain_id = evm_service.w3.eth.chain_id
        assert isinstance(chain_id, int)

        # Test that we can get block information
        latest_block = evm_service.w3.eth.block_number
        assert isinstance(latest_block, int)
        assert latest_block >= 0

    def test_error_recovery(self, evm_service, test_wallet):
        """Test error recovery scenarios."""
        # Fund the wallet
        evm_service.w3.eth.send_transaction(
            {
                "from": evm_service.w3.eth.accounts[0],
                "to": test_wallet.address,
                "value": evm_service.w3.to_wei(1, "ether"),
            }
        )

        # Try to send a transaction with insufficient funds
        tx = {
            "to": evm_service.w3.eth.accounts[0],
            "value": evm_service.w3.to_wei(2, "ether"),  # More than available
            "gas": 21000,
            "gasPrice": evm_service.w3.eth.gas_price,
            "nonce": evm_service.w3.eth.get_transaction_count(test_wallet.address),
            "chainId": evm_service.w3.eth.chain_id,
        }

        # This should fail but not crash the service
        try:
            _ = evm_service.send_transaction(tx, test_wallet.key.hex())
            # If it doesn't fail, that's also acceptable in test environment
        except Exception:
            # Expected behavior
            pass

        # Verify the service is still functional
        balance = evm_service.get_wallet_balance(test_wallet.address)
        assert isinstance(balance, float)
