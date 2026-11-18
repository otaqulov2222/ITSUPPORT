from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.ws import router as ws_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.schema_patch import ensure_schema_patches
from app.db.seed import seed_reference_data
from app.db.session import SessionLocal, engine
import app.db.models  # noqa: F401 — register models


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.is_sqlite:
        Path(settings.database_url.split("///")[-1]).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_schema_patches(engine)

    async with SessionLocal() as db:
        await seed_reference_data(db)

    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(ws_router)

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "env": settings.app_env,
            "ai_provider": settings.ai_provider,
            "db": "sqlite" if settings.is_sqlite else "postgres",
            "telegram_mode": settings.telegram_mode,
        }

    return app


app = create_app()
