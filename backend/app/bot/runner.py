from __future__ import annotations

import asyncio
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.bot import handlers
from app.core.config import get_settings
from app.db.base import Base
from app.db.schema_patch import ensure_schema_patches
from app.db.seed import seed_reference_data
from app.db.session import SessionLocal, engine
import app.db.models  # noqa: F401

logging.basicConfig(
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("bot")


async def prepare_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_schema_patches(engine)
    async with SessionLocal() as db:
        await seed_reference_data(db)
    logger.info("DB seed tugadi (FOM KB + lokatsiyalar)")


def build_application() -> Application:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN topilmadi")

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .build()
    )
    app.add_handler(CommandHandler("start", handlers.cmd_start))
    app.add_handler(CommandHandler("help", handlers.cmd_help))
    app.add_handler(CommandHandler("ticket", handlers.cmd_ticket))
    app.add_handler(CommandHandler("operator", handlers.cmd_operator))
    app.add_handler(MessageHandler(filters.CONTACT, handlers.handle_contact))
    app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handlers.handle_document))
    app.add_handler(MessageHandler(filters.VOICE, handlers.handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))
    return app


async def main() -> None:
    settings = get_settings()
    if settings.telegram_mode == "off":
        logger.info("TELEGRAM_MODE=off — bot ishga tushirilmadi")
        return

    await prepare_db()
    application = build_application()
    logger.info("Telegram bot polling boshlandi")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
