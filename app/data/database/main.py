import asyncio
from typing import Any

from tortoise import Tortoise, connections


class DatabaseManager:
    """Manager responsible for managing the database connection using Tortoise ORM."""

    def __init__(self, logger: Any):
        """Initialize the database manager."""
        self.logger = logger
        self._tortoise_initialized = False

    async def initialize(
        self,
        db_name: str,
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        min_size: int = 1,
        max_size: int = 10,
        max_idle: int = 300,
        timeout: int = 30,
    ):
        """Initialize the database connection with Tortoise ORM connection pooling."""
        self.logger.info(f"Initializing database connection to {db_name}")

        # Close any existing connections first
        await self.close()

        # Build connection URL with connection pool parameters
        url = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/"
        url += f"{db_name}?minsize={min_size}&maxsize={max_size}&"
        url += f"max_inactive_connection_lifetime={max_idle}&timeout={timeout}"

        # Create connection pool with retry logic
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Initialize Tortoise ORM with connection pooling
                await Tortoise.init(
                    db_url=url,
                    modules={
                        "models": [
                            "app.data.database.transactions",
                            "app.data.database.wallets",
                        ]
                    },
                    use_tz=False,
                    _create_db=False,
                )

                # Generate schemas
                await Tortoise.generate_schemas()
                self._tortoise_initialized = True

                self.logger.info(
                    "Tortoise ORM initialized successfully with connection pooling"
                )
                return

            except Exception as e:
                self.logger.error(
                    f"Database initialization attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error("All database initialization attempts failed")
                    raise

    async def close(self):
        """Close all database connections."""
        self.logger.info("Closing database connections")

        if self._tortoise_initialized:
            try:
                await Tortoise.close_connections()
                self.logger.info("Tortoise connections closed successfully")
                self._tortoise_initialized = False
            except Exception as e:
                # Expected if Tortoise was never initialized or already closed
                self.logger.debug(
                    f"Tortoise connections already closed or not initialized: {e}"
                )
        else:
            self.logger.info("No Tortoise connections to close")

    async def get_pool_stats(self) -> dict:
        """Get connection pool statistics from Tortoise."""
        if not self._tortoise_initialized:
            return {"error": "Tortoise ORM not initialized"}

        try:
            # Get connection pool info from Tortoise
            connection = connections.get("default")
            pool = connection._pool

            if hasattr(pool, "get_stats"):
                stats = pool.get_stats()
                return {
                    "pool_size": stats.get("pool_size", 0),
                    "checked_in": stats.get("checked_in", 0),
                    "checked_out": stats.get("checked_out", 0),
                    "overflow": stats.get("overflow", 0),
                    "checkedout_overflows": stats.get("checkedout_overflows", 0),
                    "returned_overflows": stats.get("returned_overflows", 0),
                    "tortoise_initialized": self._tortoise_initialized,
                }
            else:
                # Fallback for when pool stats are not available
                return {
                    "pool_size": "unknown",
                    "checked_in": "unknown",
                    "checked_out": "unknown",
                    "overflow": "unknown",
                    "checkedout_overflows": "unknown",
                    "returned_overflows": "unknown",
                    "tortoise_initialized": self._tortoise_initialized,
                    "note": "Pool statistics not available for this connection type",
                }
        except Exception as e:
            self.logger.error(f"Error getting pool stats: {e}")
            return {"error": str(e)}

    async def is_healthy(self) -> bool:
        from app.data.database.wallets import Wallet
        try:
            await Wallet.all().limit(1)
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def is_initialized(self) -> bool:
        """Check if the database manager is properly initialized."""
        return self._tortoise_initialized
