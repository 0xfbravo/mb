"""
Pytest configuration file.

This file sets up the Python path to include the project root directory,
allowing tests to import modules from the main application.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_data():
    """Provide test data for all tests."""
    return {
        "wallet": {
            "address": "0x1234567890abcdef",
            "private_key": "test_private_key_1234567890abcdef",
        },
        "transaction": {
            "from_address": "0x1234567890abcdef",
            "to_address": "0xfedcba0987654321",
            "amount": 1.5,
            "gas_price": 20000000000,
            "gas_limit": 21000,
        },
        "create_tx": {
            "from_address": "0x1234567890abcdef",
            "to_address": "0xfedcba0987654321",
            "amount": 1.5,
        },
    }


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager for testing."""
    db_manager = MagicMock()
    db_manager.initialize = AsyncMock()
    db_manager.close = AsyncMock()
    db_manager.get_pool_stats = AsyncMock(
        return_value={
            "pool_size": 5,
            "checked_in": 3,
            "checked_out": 2,
            "overflow": 0,
            "checkedout_overflows": 0,
            "returned_overflows": 0,
        }
    )
    db_manager.is_initialized = True
    return db_manager


@pytest.fixture
def mock_wallet_repository():
    """Create a mock wallet repository for testing."""
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_by_address = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_count = AsyncMock(return_value=1)
    repo.get_native_balance = AsyncMock()
    repo.get_token_balance = AsyncMock()
    return repo


@pytest.fixture
def mock_transaction_repository():
    """Create a mock transaction repository for testing."""
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_tx_hash = AsyncMock()
    repo.get_by_wallet = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_count = AsyncMock(return_value=1)
    repo.get_count_by_wallet = AsyncMock(return_value=1)
    return repo


@pytest.fixture
def mock_evm_service():
    """Create a mock EVM service for testing."""
    evm_service = MagicMock()
    evm_service.send_transaction = MagicMock()
    evm_service.get_token_contract = MagicMock()
    evm_service.get_native_balance = AsyncMock()
    evm_service.get_token_balance = AsyncMock()
    return evm_service


@pytest.fixture
def mock_assets_use_cases():
    """Create a mock assets use cases for testing."""
    assets_use_cases = MagicMock()
    assets_use_cases.is_native_asset = MagicMock(return_value=False)
    assets_use_cases.get_asset_config = MagicMock()
    return assets_use_cases


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager for testing."""
    config_manager = MagicMock()
    config_manager.get_current_network = MagicMock(return_value="ethereum")
    config_manager.get_networks = MagicMock(return_value=["ethereum", "polygon"])
    config_manager.get_asset = MagicMock(
        return_value={"ethereum": "0x1234567890abcdef1234567890abcdef1234567890"}
    )
    return config_manager


@pytest.fixture
def mock_dependency_injection(
    mock_logger, mock_db_manager, mock_wallet_repository, mock_transaction_repository
):
    """Create a mock dependency injection container for testing."""
    di = MagicMock()
    di.initialize = AsyncMock()
    di.shutdown = AsyncMock()
    di.logger = mock_logger
    di.db_manager = mock_db_manager
    di.wallet_repo = mock_wallet_repository
    di.tx_repo = mock_transaction_repository
    di.wallet_uc = MagicMock()
    di.tx_uc = MagicMock()
    di.assets_uc = MagicMock()
    di.is_database_initialized = MagicMock(return_value=True)
    return di


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Mark tests based on their file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark slow tests based on certain patterns
        if any(pattern in item.name for pattern in ["slow", "integration", "e2e"]):
            item.add_marker(pytest.mark.slow)
