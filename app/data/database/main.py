from typing import Any, Optional

from psycopg_pool import AsyncConnectionPool
from tortoise import Tortoise


class DatabaseManager:
    """Manager responsible for managing the database connection pool."""

    def __init__(self, logger: Any):
        """Initialize the database manager."""
        self.logger = logger
        self._pool: Optional[AsyncConnectionPool] = None

    async def initialize(
        self,
        db_name: str,
        db_user: str,
        db_password: str,
        db_host: str,
        db_port: int,
        min_size: int = 1,
        max_size: int = 10,
        max_idle: float = 300.0,
        timeout: float = 30.0,
    ):
        """Initialize the database connection with connection pooling."""
        self.logger.info(f"Initializing database connection pool to {db_name}")

        # Close any existing connections first
        await self.close()

        # Build connection URL
        url = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        # Create connection
        self._pool = AsyncConnectionPool(
            conninfo=url,
            min_size=min_size,
            max_size=max_size,
            max_idle=max_idle,
            timeout=timeout,
            open=False,  # Don't open automatically to avoid deprecation warning
        )

        # Open the pool explicitly
        await self._pool.open()

        # Initialize Tortoise ORM with the pool
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

        self.logger.info("Database connection pool initialized successfully ")

    async def close(self):
        """Close all database connections and the connection pool."""
        self.logger.info("Closing database connection pool")

        # Close Tortoise connections
        try:
            await Tortoise.close_connections()
        except Exception as e:
            self.logger.warning(f"Error closing Tortoise connections: {e}")

        # Close the connection pool
        if self._pool:
            try:
                await self._pool.close()
                self._pool = None
                self.logger.info("Database connection pool closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing connection pool: {e}")

    async def is_healthy(self) -> bool:
        """Check if the connection pool is healthy by performing a simple query."""
        self.logger.info("Checking if database connection pool is healthy")

        if not self._pool:
            self.logger.error("Connection pool is not initialized")
            return False

        try:
            # Test the connection pool with a simple query
            async with self._pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    result = await cur.fetchone()
                    if result and result[0] == 1:
                        self.logger.info("Database connection pool is healthy")
                        return True
                    else:
                        self.logger.error(
                            "Database health check returned unexpected result"
                        )
                        return False
        except Exception as e:
            self.logger.error(f"Database connection pool is not healthy: {e}")
            return False

    async def get_pool_stats(self) -> dict:
        """Get connection pool statistics."""
        if not self._pool:
            return {"error": "Connection pool not initialized"}

        try:
            stats = self._pool.get_stats()
            return {
                "pool_size": stats.get("pool_size", 0),
                "checked_in": stats.get("checked_in", 0),
                "checked_out": stats.get("checked_out", 0),
                "overflow": stats.get("overflow", 0),
                "checkedout_overflows": stats.get("checkedout_overflows", 0),
                "returned_overflows": stats.get("returned_overflows", 0),
            }
        except Exception as e:
            self.logger.error(f"Error getting pool stats: {e}")
            return {"error": str(e)}
