from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import enforce_auth_rate_limit, get_access_context, get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginRequest, MeResponse, RefreshRequest, TokenResponse
from app.services import auth as auth_service
from app.services.rbac import AccessContext

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(enforce_auth_rate_limit)])
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    return await auth_service.login_user(
        db,
        payload.email,
        payload.password,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(enforce_auth_rate_limit)])
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_tokens(db, payload.refresh_token)


@router.get("/me", response_model=MeResponse)
async def me(
    user: User = Depends(get_current_user),
    access: AccessContext = Depends(get_access_context),
):
    return MeResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        roles=sorted(access.role_codes),
        permissions=sorted(access.permission_codes),
    )
