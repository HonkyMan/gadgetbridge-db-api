import aiosqlite
from contextlib import asynccontextmanager
from core.config import get_settings

_settings = get_settings()


@asynccontextmanager
async def db_conn():
    conn = await aiosqlite.connect(_settings.db_path)
    conn.row_factory = aiosqlite.Row
    try:
        yield conn
    finally:
        await conn.close()