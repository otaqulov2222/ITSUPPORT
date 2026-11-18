from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RegionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=64)


class RegionOut(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    code: str
    is_active: bool

    model_config = {"from_attributes": True}


class BranchCreate(BaseModel):
    region_id: UUID
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    address: str | None = None
    phone: str | None = None


class BranchOut(BaseModel):
    id: UUID
    region_id: UUID
    code: str
    name: str
    address: str | None
    phone: str | None
    timezone: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeCreate(BaseModel):
    branch_id: UUID
    employee_code: str = Field(min_length=1, max_length=64)
    full_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=7, max_length=64)
    position: str | None = None
    role_code: str = "PHARMACIST"


class EmployeeOut(BaseModel):
    id: UUID
    branch_id: UUID
    employee_code: str
    full_name: str
    phone: str
    position: str | None
    role_code: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditOut(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    branch_id: UUID | None
    created_at: datetime
    before: dict | None
    after: dict | None

    model_config = {"from_attributes": True}
