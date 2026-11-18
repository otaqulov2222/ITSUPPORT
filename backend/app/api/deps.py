from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.rate_limit import rate_limiter
from app.core.security import safe_decode_token
from app.db.models import User
from app.db.session import get_db
from app.domain.enums import PermissionCode
from app.services.rbac import AccessContext, load_access_context

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autentifikatsiya kerak")

    payload = safe_decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token yaroqsiz")

    user_id = UUID(payload["sub"])
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Foydalanuvchi topilmadi")
    return user


async def get_access_context(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccessContext:
    return await load_access_context(db, user)


def require_permission(code: PermissionCode):
    async def _checker(access: AccessContext = Depends(get_access_context)) -> AccessContext:
        if not access.has_permission(code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")
        return access

    return _checker


async def enforce_auth_rate_limit(request: Request) -> None:
    settings = get_settings()
    client = request.client.host if request.client else "unknown"
    key = f"auth:{client}"
    if not rate_limiter.allow(key, settings.rate_limit_auth_per_minute, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Juda ko'p urinish. Biroz kuting.",
        )
