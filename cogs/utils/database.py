import os
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, Optional
import asyncpg

class DatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

class Database:
    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None

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
        )

    async def close_pool(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def _require_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise DatabaseError("Database pool is not initialized. Call db.init_pool() first.")
        return self._pool

    async def execute(self, query: str, *args: Any) -> str:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, args_iter: Iterable[Iterable[Any]]) -> None:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            await conn.executemany(query, args_iter)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return list(rows)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        pool = self._require_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
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

    async def ensure_schema(self, schema_path: str | os.PathLike[str] = "schema.sql") -> None:
        pool = self._require_pool()
        path = Path(schema_path)
        if not path.exists():
            return

        sql_text = path.read_text(encoding="utf-8")
        statements = [s.strip() for s in sql_text.split(";")]

        async with pool.acquire() as conn:
            for stmt in statements:
                if not stmt:
                    continue
                await conn.execute(stmt + ";")


db = Database()


async def startup() -> None:
    await db.init_pool()


async def shutdown() -> None:
    await db.close_pool()
