from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Permission, Role, RolePermission, User, UserRole
from app.domain.enums import PermissionCode, RoleCode, ScopeType


@dataclass
class AccessContext:
    user: User
    role_codes: set[str]
    permission_codes: set[str]
    global_access: bool
    region_ids: set[UUID]
    branch_ids: set[UUID]

    def has_permission(self, code: PermissionCode | str) -> bool:
        return str(code) in self.permission_codes

    def can_access_branch(self, branch_id: UUID) -> bool:
        if self.global_access or RoleCode.SUPER_ADMIN in self.role_codes:
            return True
        return branch_id in self.branch_ids

    def can_access_region(self, region_id: UUID) -> bool:
        if self.global_access or RoleCode.SUPER_ADMIN in self.role_codes:
            return True
        return region_id in self.region_ids


async def load_access_context(db: AsyncSession, user: User) -> AccessContext:
    result = await db.execute(
        select(UserRole)
        .where(UserRole.user_id == user.id)
        .options(
            selectinload(UserRole.role).selectinload(Role.permissions).selectinload(RolePermission.permission)
        )
    )
    user_roles = list(result.scalars().all())

    role_codes: set[str] = set()
    permission_codes: set[str] = set()
    region_ids: set[UUID] = set()
    branch_ids: set[UUID] = set()
    global_access = False

    for ur in user_roles:
        role_codes.add(ur.role.code)
        for rp in ur.role.permissions:
            permission_codes.add(rp.permission.code)
        if ur.scope_type == ScopeType.GLOBAL:
            global_access = True
        elif ur.scope_type == ScopeType.REGION and ur.scope_id:
            region_ids.add(ur.scope_id)
        elif ur.scope_type == ScopeType.BRANCH and ur.scope_id:
            branch_ids.add(ur.scope_id)

    if RoleCode.SUPER_ADMIN in role_codes:
        global_access = True
        permission_codes.update(code.value for code in PermissionCode)

    return AccessContext(
        user=user,
        role_codes=role_codes,
        permission_codes=permission_codes,
        global_access=global_access,
        region_ids=region_ids,
        branch_ids=branch_ids,
    )


async def ensure_role(db: AsyncSession, code: str, name: str, description: str = "") -> Role:
    result = await db.execute(select(Role).where(Role.code == code))
    role = result.scalar_one_or_none()
    if role:
        return role
    role = Role(code=code, name=name, description=description)
    db.add(role)
    await db.flush()
    return role


async def ensure_permission(db: AsyncSession, code: str, description: str = "") -> Permission:
    result = await db.execute(select(Permission).where(Permission.code == code))
    perm = result.scalar_one_or_none()
    if perm:
        return perm
    perm = Permission(code=code, description=description)
    db.add(perm)
    await db.flush()
    return perm


async def bind_role_permissions(db: AsyncSession, role: Role, permission_codes: list[str]) -> None:
    for code in permission_codes:
        perm = await ensure_permission(db, code)
        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id,
            )
        )
        if result.scalar_one_or_none() is None:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    await db.flush()
