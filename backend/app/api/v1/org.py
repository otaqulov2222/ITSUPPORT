from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_access_context, require_permission
from app.db.models import Region
from app.db.session import get_db
from app.domain.enums import PermissionCode
from app.schemas.org import (
    BranchCreate,
    BranchOut,
    EmployeeCreate,
    EmployeeOut,
    RegionCreate,
    RegionOut,
)
from app.services import org as org_service
from app.services.rbac import AccessContext

router = APIRouter(tags=["organization"])


@router.post("/regions", response_model=RegionOut)
async def create_region(
    payload: RegionCreate,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(require_permission(PermissionCode.BRANCHES_WRITE)),
):
    company = await org_service.get_or_create_default_company(db)
    return await org_service.create_region(
        db,
        company_id=company.id,
        name=payload.name,
        code=payload.code,
        actor=access,
    )


@router.get("/regions", response_model=list[RegionOut])
async def list_regions(
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(require_permission(PermissionCode.BRANCHES_READ)),
):
    result = await db.execute(select(Region).where(Region.deleted_at.is_(None)).order_by(Region.name))
    regions = list(result.scalars().all())
    if access.global_access:
        return regions
    return [r for r in regions if r.id in access.region_ids]


@router.post("/branches", response_model=BranchOut)
async def create_branch(
    payload: BranchCreate,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await org_service.create_branch(
        db,
        region_id=payload.region_id,
        code=payload.code,
        name=payload.name,
        address=payload.address,
        phone=payload.phone,
        actor=access,
    )


@router.get("/branches", response_model=list[BranchOut])
async def list_branches(
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await org_service.list_branches(db, access)


@router.get("/branches/{branch_id}", response_model=BranchOut)
async def get_branch(
    branch_id: UUID,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await org_service.get_branch_for_actor(db, branch_id, access)


@router.post("/employees", response_model=EmployeeOut)
async def create_employee(
    payload: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await org_service.create_employee(
        db,
        branch_id=payload.branch_id,
        employee_code=payload.employee_code,
        full_name=payload.full_name,
        phone=payload.phone,
        position=payload.position,
        role_code=payload.role_code,
        actor=access,
    )


@router.get("/employees", response_model=list[EmployeeOut])
async def list_employees(
    branch_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    access: AccessContext = Depends(get_access_context),
):
    return await org_service.list_employees(db, access, branch_id=branch_id)
