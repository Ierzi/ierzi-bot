import os
from typing import Any, AsyncIterator, Iterable, Optional
import asyncpg
from asyncpg import Record, Connection, Pool

class DatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

class Database:
    def __init__(self) -> None:
        self._pool: Optional[Pool] = None

    async def init_pool(
        self,
        *,
        min_size: int = 1,
        max_size: int = 10,
        timeout: float | None = 10.0,
    ) -> None:
        if self._pool is not None:
            return

        self._pool = await asyncpg.create_pool(
            host=os.getenv("PGHOST"),
            database=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            port=int(os.getenv("PGPORT") or 5432),
            min_size=min_size,
            max_size=max_size,
            timeout=timeout,
            max_inactive_connection_lifetime=60.0,
            statement_cache_size=0,
        )

    async def close_pool(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def _require_pool(self) -> Pool:
        if self._pool is None:
            raise DatabaseError("Database pool is not initialized. Call db.init_pool() first.")
        return self._pool

    async def _reconnect(self) -> None:
        await self.close_pool()
        await self.init_pool()

    async def _run_with_retry(self, method_name: str, query: str, *args: Any, attempts: int = 2):
        last_exc: Exception | None = None
        for _ in range(attempts):
            pool = self._require_pool()
            try:
                async with pool.acquire() as conn:
                    method = getattr(conn, method_name)
                    return await method(query, *args)
            except (asyncpg.PostgresConnectionError, asyncpg.CannotConnectNowError, ConnectionError, OSError) as exc:
                last_exc = exc
                await self._reconnect()
                continue
            
        assert last_exc is not None
        raise last_exc

    async def execute(self, query: str, *args: Any) -> str:
        return await self._run_with_retry("execute", query, *args)

    async def executemany(self, query: str, args_iter: Iterable[Iterable[Any]]) -> None:
        pool = self._require_pool()
        try:
            async with pool.acquire() as conn:
                await conn.executemany(query, args_iter)
        except (asyncpg.PostgresConnectionError, asyncpg.CannotConnectNowError, ConnectionError, OSError):
            await self._reconnect()
            pool = self._require_pool()
            async with pool.acquire() as conn:
                await conn.executemany(query, args_iter)

    async def fetch(self, query: str, *args: Any) -> list[Record]:
        rows = await self._run_with_retry("fetch", query, *args)
        return list(rows)

    async def fetchrow(self, query: str, *args: Any) -> Optional[Record]:
        return await self._run_with_retry("fetchrow", query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        return await self._run_with_retry("fetchval", query, *args)

    async def transaction(self) -> AsyncIterator[Connection]:
        pool = self._require_pool()
        conn = await pool.acquire()
        tx = conn.transaction()
        await tx.start()
        try:
            try:
                yield conn
            except Exception:
                await tx.rollback()
                raise
            else:
                await tx.commit()
        finally:
            await pool.release(conn)


db = Database()


async def startup() -> None:
    await db.init_pool()


async def shutdown() -> None:
    await db.close_pool()
