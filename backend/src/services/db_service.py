# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
CockroachDB database connection service
PostgreSQL-compatible connection using asyncpg
"""
import os
import logging
from typing import Optional
import asyncpg

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class DatabaseService:
    """
    CockroachDB connection manager
    Provides async PostgreSQL-compatible database access
    """

    def __init__(self, dsn: Optional[str] = None):
        self._dsn = dsn or os.getenv("DATABASE_URL", "")
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Initialize the connection pool"""
        if not self._dsn:
            raise ValueError("DATABASE_URL is not configured")
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=1,
                max_size=5,
                command_timeout=30
            )
            logger.info("Database connection pool established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def close(self) -> None:
        """Close the connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")

    async def execute(self, query: str, *args) -> str:
        """Execute a SQL query"""
        if not self._pool:
            raise RuntimeError("Database not connected")
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """Execute a SELECT query and return results"""
        if not self._pool:
            raise RuntimeError("Database not connected")
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[dict]:
        """Execute a SELECT query and return first row"""
        if not self._pool:
            raise RuntimeError("Database not connected")
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    @property
    def is_connected(self) -> bool:
        return self._pool is not None and not self._pool._closed


# Global database service instance
db_service = DatabaseService()


async def run_migrations() -> None:
    """Execute pending database migrations"""
    from src.models.db_migrations import MIGRATIONS

    for query in MIGRATIONS:
        await db_service.execute(query)
    logger.info("Database migrations completed successfully")


async def initialize_database(dsn: Optional[str] = None) -> None:
    """Connect to database and run migrations"""
    if dsn:
        db_service._dsn = dsn
    await db_service.connect()
    await run_migrations()

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
