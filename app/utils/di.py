"""Dependency injection for the application."""

import os
from typing import Optional

from loguru import logger

from app.data.database import (DatabaseManager, TransactionRepository,
                               WalletRepository)
from app.data.evm.main import EVMService
from app.domain.transaction.use_cases import TransactionUseCases
from app.domain.wallet.use_cases import WalletUseCases
from app.utils.config_manager import ConfigManager


def get_dependency_injection() -> "DependencyInjection":
    """Get the singleton dependency injection instance.

    This function is used by FastAPI's dependency injection system.
    """
    return DependencyInjection()


class DependencyInjection:
    """Dependency injection for the application."""

    _instance = None

    def __new__(cls):
        """Create a new instance of the dependency injection as a singleton."""
        if cls._instance is None:
            cls._instance = super(DependencyInjection, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        """Initialize the dependency injection on first instance creation.

        This is done to avoid multiple instances of the dependency injection.
        """
        if not hasattr(self, "_initialized"):
            logger.info("Initializing dependency injection")
            self.logger = logger
            self.db_manager = DatabaseManager(self.logger)
            self.config_manager = ConfigManager()
            self.evm_service = EVMService(
                self.config_manager.get_selected_network() == "TEST",
                self.config_manager.get_rpc_url(
                    self.config_manager.get_selected_network()
                ),
                self.logger,
            )
            self.wallet_repo = WalletRepository(self.db_manager, self.logger)
            self.wallet_uc = WalletUseCases(
                self.wallet_repo, self.evm_service, self.logger
            )
            self.tx_repo = TransactionRepository(self.db_manager, self.logger)
            self.tx_uc = TransactionUseCases(
                self.config_manager, self.evm_service, self.tx_repo, self.logger
            )
            logger.info("Dependency injection initialized successfully")
            self._initialized = True

    async def initialize(
        self,
        db_name: str,
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        max_idle: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """Initialize the dependency injection."""
        # Always initialize to handle test scenarios where we need fresh connections
        self.logger.info(f"Initializing database: {db_name}")

        # Use environment variables for pool configuration if not provided
        if min_size is None:
            min_size = int(os.getenv("DB_POOL_MIN_SIZE", "1").split("#")[0].strip())
        if max_size is None:
            max_size = int(os.getenv("DB_POOL_MAX_SIZE", "10").split("#")[0].strip())
        if max_idle is None:
            max_idle = int(os.getenv("DB_POOL_MAX_IDLE", "300").split("#")[0].strip())
        if timeout is None:
            timeout = int(os.getenv("DB_POOL_TIMEOUT", "30").split("#")[0].strip())

        await self.db_manager.initialize(
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            db_host=db_host,
            db_port=db_port,
            min_size=min_size,
            max_size=max_size,
            max_idle=max_idle,
            timeout=timeout,
        )
        self._db_initialized = True

    async def shutdown(self):
        """Shutdown the dependency injection."""
        self.logger.info("Shutting down dependency injection")
        await self.db_manager.close()
        self.logger.info("Dependency injection shut down")

    def is_database_initialized(self) -> bool:
        """Check if the database has been initialized."""
        return (
            hasattr(self, "_db_initialized")
            and self._db_initialized
            and self.db_manager.is_initialized()
        )
