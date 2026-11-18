from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.fom_kb_seed import FOM_KB_SEED
from app.db.kb_seed_data import KB_SEED
from app.db.locations_loader import seed_branches_from_locations
from app.db.models import KnowledgeArticle, User, UserRole
from app.domain.enums import PermissionCode, RoleCode, ScopeType
from app.services.org import get_or_create_default_company
from app.services.rbac import bind_role_permissions, ensure_permission, ensure_role

ROLE_PERMISSIONS: dict[str, list[str]] = {
    RoleCode.SUPER_ADMIN: [p.value for p in PermissionCode],
    RoleCode.NETWORK_ADMIN: [
        PermissionCode.BRANCHES_READ.value,
        PermissionCode.BRANCHES_WRITE.value,
        PermissionCode.EMPLOYEES_READ.value,
        PermissionCode.EMPLOYEES_WRITE.value,
        PermissionCode.TICKETS_READ.value,
        PermissionCode.TICKETS_ASSIGN.value,
        PermissionCode.CONVERSATIONS_READ.value,
        PermissionCode.CONVERSATIONS_REPLY.value,
        PermissionCode.AUTOMATION_APPROVE.value,
        PermissionCode.AUDIT_READ.value,
    ],
    RoleCode.IT_SUPPORT: [
        PermissionCode.BRANCHES_READ.value,
        PermissionCode.EMPLOYEES_READ.value,
        PermissionCode.TICKETS_READ.value,
        PermissionCode.TICKETS_ASSIGN.value,
        PermissionCode.CONVERSATIONS_READ.value,
        PermissionCode.CONVERSATIONS_REPLY.value,
    ],
    RoleCode.REGIONAL_ADMIN: [
        PermissionCode.BRANCHES_READ.value,
        PermissionCode.BRANCHES_WRITE.value,
        PermissionCode.EMPLOYEES_READ.value,
        PermissionCode.EMPLOYEES_WRITE.value,
        PermissionCode.TICKETS_READ.value,
        PermissionCode.CONVERSATIONS_READ.value,
    ],
    RoleCode.BRANCH_MANAGER: [
        PermissionCode.BRANCHES_READ.value,
        PermissionCode.EMPLOYEES_READ.value,
        PermissionCode.TICKETS_READ.value,
        PermissionCode.CONVERSATIONS_READ.value,
    ],
    RoleCode.AUDITOR: [
        PermissionCode.BRANCHES_READ.value,
        PermissionCode.EMPLOYEES_READ.value,
        PermissionCode.AUDIT_READ.value,
        PermissionCode.TICKETS_READ.value,
        PermissionCode.CONVERSATIONS_READ.value,
    ],
    RoleCode.PHARMACIST: [],
}


async def seed_reference_data(db: AsyncSession) -> None:
    settings = get_settings()
    await get_or_create_default_company(db)

    for code in PermissionCode:
        await ensure_permission(db, code.value, description=code.value)

    roles = {
        RoleCode.SUPER_ADMIN: "Super Admin",
        RoleCode.NETWORK_ADMIN: "Network Administrator",
        RoleCode.IT_SUPPORT: "IT Support",
        RoleCode.REGIONAL_ADMIN: "Regional Administrator",
        RoleCode.BRANCH_MANAGER: "Branch Manager",
        RoleCode.PHARMACIST: "Pharmacist",
        RoleCode.AUDITOR: "Read-only Auditor",
    }
    for code, name in roles.items():
        role = await ensure_role(db, code.value, name)
        await bind_role_permissions(db, role, ROLE_PERMISSIONS.get(code, []))

    result = await db.execute(select(User).where(User.email == settings.bootstrap_admin_email))
    admin = result.scalar_one_or_none()
    if admin is None:
        admin = User(
            email=settings.bootstrap_admin_email,
            password_hash=hash_password(settings.bootstrap_admin_password),
            full_name=settings.bootstrap_admin_name,
            is_active=True,
        )
        db.add(admin)
        await db.flush()

        super_role = await ensure_role(db, RoleCode.SUPER_ADMIN.value, "Super Admin")
        db.add(
            UserRole(
                user_id=admin.id,
                role_id=super_role.id,
                scope_type=ScopeType.GLOBAL.value,
                scope_id=None,
            )
        )

    await seed_knowledge_articles(db)
    await seed_branches_from_locations(db)
    await db.commit()


async def seed_knowledge_articles(db: AsyncSession) -> None:
    for item in [*KB_SEED, *FOM_KB_SEED]:
        existing = await db.execute(
            select(KnowledgeArticle).where(KnowledgeArticle.title == item["title"])
        )
        if existing.scalar_one_or_none():
            continue
        db.add(
            KnowledgeArticle(
                title=item["title"],
                category=item["category"],
                problem=item["problem"],
                symptoms=item["symptoms"],
                root_cause=item["root_cause"],
                solution=item["solution"],
                steps=item["steps"],
                related_software=item["related_software"],
                status="APPROVED",
                version=1,
            )
        )
    await db.flush()
