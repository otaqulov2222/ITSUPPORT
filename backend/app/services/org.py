from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Branch, Company, Employee, Region
from app.services.audit import write_audit
from app.services.rbac import AccessContext


async def get_or_create_default_company(db: AsyncSession, name: str = "Pharmacy Network") -> Company:
    result = await db.execute(select(Company).where(Company.deleted_at.is_(None)).limit(1))
    company = result.scalar_one_or_none()
    if company:
        return company
    company = Company(name=name, settings={})
    db.add(company)
    await db.flush()
    return company


async def create_region(
    db: AsyncSession,
    *,
    company_id: UUID,
    name: str,
    code: str,
    actor: AccessContext,
) -> Region:
    if not actor.has_permission("branches.write"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")

    region = Region(company_id=company_id, name=name, code=code.upper(), is_active=True)
    db.add(region)
    await db.flush()
    await write_audit(
        db,
        action="region.create",
        resource_type="region",
        resource_id=region.id,
        actor_user_id=actor.user.id,
        after={"name": name, "code": code.upper()},
    )
    await db.commit()
    await db.refresh(region)
    return region


async def create_branch(
    db: AsyncSession,
    *,
    region_id: UUID,
    code: str,
    name: str,
    address: str | None,
    phone: str | None,
    actor: AccessContext,
) -> Branch:
    if not actor.has_permission("branches.write"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")

    if not actor.can_access_region(region_id) and not actor.global_access:
        # Super admin covered by global_access; regional admins must match region
        if region_id not in actor.region_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Regionga ruxsat yo'q")

    region = await db.get(Region, region_id)
    if not region or region.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region topilmadi")

    branch = Branch(
        region_id=region_id,
        code=code.upper(),
        name=name,
        address=address,
        phone=phone,
        is_active=True,
        metadata_json={},
    )
    db.add(branch)
    await db.flush()
    await write_audit(
        db,
        action="branch.create",
        resource_type="branch",
        resource_id=branch.id,
        actor_user_id=actor.user.id,
        branch_id=branch.id,
        after={"name": name, "code": code.upper(), "region_id": str(region_id)},
    )
    await db.commit()
    await db.refresh(branch)
    return branch


async def list_branches(db: AsyncSession, actor: AccessContext) -> list[Branch]:
    if not actor.has_permission("branches.read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")

    stmt = (
        select(Branch)
        .where(Branch.deleted_at.is_(None))
        .options(selectinload(Branch.region))
        .order_by(Branch.name)
    )
    result = await db.execute(stmt)
    branches = list(result.scalars().all())

    if actor.global_access:
        return branches

    allowed: list[Branch] = []
    for branch in branches:
        if branch.id in actor.branch_ids or branch.region_id in actor.region_ids:
            allowed.append(branch)
    return allowed


async def get_branch_for_actor(db: AsyncSession, branch_id: UUID, actor: AccessContext) -> Branch:
    if not actor.has_permission("branches.read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")

    branch = await db.get(Branch, branch_id)
    if not branch or branch.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filial topilmadi")

    if not actor.can_access_branch(branch_id) and branch.region_id not in actor.region_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Filialga ruxsat yo'q")

    return branch


async def create_employee(
    db: AsyncSession,
    *,
    branch_id: UUID,
    employee_code: str,
    full_name: str,
    phone: str,
    position: str | None,
    role_code: str,
    actor: AccessContext,
) -> Employee:
    if not actor.has_permission("employees.write"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")

    branch = await get_branch_for_actor(db, branch_id, actor)

    employee = Employee(
        branch_id=branch.id,
        employee_code=employee_code,
        full_name=full_name,
        phone=phone,
        position=position,
        role_code=role_code,
        is_active=True,
    )
    db.add(employee)
    await db.flush()
    await write_audit(
        db,
        action="employee.create",
        resource_type="employee",
        resource_id=employee.id,
        actor_user_id=actor.user.id,
        branch_id=branch.id,
        after={
            "full_name": full_name,
            "phone": phone,
            "employee_code": employee_code,
            "branch_id": str(branch.id),
        },
    )
    await db.commit()
    await db.refresh(employee)
    return employee


async def list_employees(
    db: AsyncSession,
    actor: AccessContext,
    branch_id: UUID | None = None,
) -> list[Employee]:
    if not actor.has_permission("employees.read"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")

    stmt = select(Employee).where(Employee.deleted_at.is_(None)).order_by(Employee.full_name)
    if branch_id:
        await get_branch_for_actor(db, branch_id, actor)
        stmt = stmt.where(Employee.branch_id == branch_id)

    result = await db.execute(stmt)
    employees = list(result.scalars().all())

    if actor.global_access:
        return employees if not branch_id else employees

    # Filter by accessible branches
    branches = await list_branches(db, actor)
    allowed_ids = {b.id for b in branches}
    return [e for e in employees if e.branch_id in allowed_ids]


async def soft_delete_branch(db: AsyncSession, branch_id: UUID, actor: AccessContext) -> Branch:
    branch = await get_branch_for_actor(db, branch_id, actor)
    if not actor.has_permission("branches.write"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat yo'q")

    before = {"name": branch.name, "is_active": branch.is_active}
    branch.deleted_at = datetime.now(UTC)
    branch.is_active = False
    await write_audit(
        db,
        action="branch.soft_delete",
        resource_type="branch",
        resource_id=branch.id,
        actor_user_id=actor.user.id,
        branch_id=branch.id,
        before=before,
        after={"deleted": True},
    )
    await db.commit()
    await db.refresh(branch)
    return branch
