from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    safe_decode_token,
    verify_password,
)
from app.db.models import User
from app.services.audit import write_audit


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email.lower(), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> dict[str, str]:
    user = await authenticate_user(db, email, password)
    if not user:
        await write_audit(
            db,
            action="auth.login_failed",
            resource_type="user",
            resource_id=email.lower(),
            ip=ip,
            user_agent=user_agent,
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login yoki parol xato")

    user.last_login_at = datetime.now(UTC)
    await write_audit(
        db,
        action="auth.login",
        resource_type="user",
        resource_id=user.id,
        actor_user_id=user.id,
        ip=ip,
        user_agent=user_agent,
    )
    await db.commit()

    return {
        "access_token": create_access_token(user.id, user.email),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict[str, str]:
    payload = safe_decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token yaroqsiz")

    user_id = UUID(payload["sub"])
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Foydalanuvchi topilmadi")

    return {
        "access_token": create_access_token(user.id, user.email),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    phone: str | None = None,
) -> User:
    existing = await db.execute(select(User).where(User.email == email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email band")

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
        phone=phone,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user
