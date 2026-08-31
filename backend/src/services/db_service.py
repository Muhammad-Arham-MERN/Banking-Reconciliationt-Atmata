# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
CockroachDB database connection service
PostgreSQL-compatible connection using asyncpg
"""
import asyncio
import os
import logging
from typing import Optional
import asyncpg

logger = logging.getLogger(__name__)

# The event loop the connection pool lives on (the app's main loop, captured
# at connect time). asyncpg connections are bound to the loop they were
# created on, so ANY code that touches the pool - including sync tool workers
# running in SDK threads - must schedule its coroutine onto THIS loop, never a
# fresh one (a new loop would raise "Future attached to a different loop").
_main_loop: Optional[asyncio.AbstractEventLoop] = None


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def get_main_loop() -> Optional[asyncio.AbstractEventLoop]:
    """Return the loop the DB pool is bound to (None when not connected)."""
    return _main_loop


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def run_on_main_loop(coro_factory):
    """Run an async DB coroutine on the main loop from ANY thread.

    The OpenAI Agents SDK runs sync tools in worker threads with no running
    event loop. asyncpg pools are bound to the loop they were created on, so
    those threads must NOT spin up their own loop - they schedule the work
    onto the main loop (via run_coroutine_threadsafe) and block until it
    finishes. Safe to call from the main loop thread itself too.
    """
    loop = _main_loop
    if loop is None:
        raise RuntimeError("Database not connected")
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None
    if running_loop is loop:
        return loop.run_until_complete(coro_factory())
    future = asyncio.run_coroutine_threadsafe(coro_factory(), loop)
    return future.result(timeout=30)


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
        global _main_loop
        if not self._dsn:
            raise ValueError("DATABASE_URL is not configured")
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=1,
                max_size=5,
                command_timeout=30
            )
            # Capture the loop the pool is bound to (the app's main loop).
            try:
                _main_loop = asyncio.get_running_loop()
            except RuntimeError:
                _main_loop = asyncio.get_event_loop()
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
