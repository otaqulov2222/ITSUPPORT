import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.models import Role, User, UserRole
from app.db.seed import seed_reference_data
from app.db.session import get_db
from app.domain.enums import RoleCode, ScopeType
import app.db.models  # noqa: F401


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine(tmp_path: Path):
    db_path = tmp_path / "test.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as bootstrap:
        await seed_reference_data(bootstrap)

    settings = get_settings()
    app = FastAPI(title="test")
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok", "env": "test"}

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    settings = get_settings()
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": settings.bootstrap_admin_email,
            "password": settings.bootstrap_admin_password,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def limited_user_token(db_engine, client: AsyncClient) -> str:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        from sqlalchemy import select

        role = (
            await session.execute(select(Role).where(Role.code == RoleCode.BRANCH_MANAGER.value))
        ).scalar_one()
        user = User(
            email="manager@example.com",
            password_hash=hash_password("ManagerPass!123"),
            full_name="Branch Manager",
            is_active=True,
        )
        session.add(user)
        await session.flush()
        session.add(
            UserRole(
                user_id=user.id,
                role_id=role.id,
                scope_type=ScopeType.BRANCH.value,
                scope_id=None,
            )
        )
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "manager@example.com", "password": "ManagerPass!123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
