"""Lightweight schema patches for expand-only column adds (dev/prod safe)."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def ensure_schema_patches(engine: AsyncEngine) -> None:
    statements = [
        # Telegram self-registration pending name
        "ALTER TABLE telegram_accounts ADD COLUMN IF NOT EXISTS pending_full_name VARCHAR(255)",
    ]
    async with engine.begin() as conn:
        dialect = conn.dialect.name
        for stmt in statements:
            if dialect == "sqlite":
                # SQLite has no IF NOT EXISTS for ADD COLUMN in older versions — check pragma
                col = "pending_full_name"
                result = await conn.execute(text("PRAGMA table_info(telegram_accounts)"))
                cols = {row[1] for row in result.fetchall()}
                if col not in cols:
                    await conn.execute(
                        text("ALTER TABLE telegram_accounts ADD COLUMN pending_full_name VARCHAR(255)")
                    )
            else:
                await conn.execute(text(stmt))
