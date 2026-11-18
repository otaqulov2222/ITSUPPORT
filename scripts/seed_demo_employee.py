"""Demo filial + xodim yaratish (Telegram telefon bog'lash uchun)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db.seed import seed_reference_data
from app.db.session import SessionLocal, engine
from app.services.org import get_or_create_default_company
from app.db.models import Branch, Employee, Region
from sqlalchemy import select
import app.db.models  # noqa: F401


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        await seed_reference_data(db)
        company = await get_or_create_default_company(db)

        region = (
            await db.execute(select(Region).where(Region.code == "TAS"))
        ).scalar_one_or_none()
        if not region:
            region = Region(company_id=company.id, name="Toshkent", code="TAS", is_active=True)
            db.add(region)
            await db.flush()

        branch = (
            await db.execute(select(Branch).where(Branch.code == "TAS-001"))
        ).scalar_one_or_none()
        if not branch:
            branch = Branch(
                region_id=region.id,
                code="TAS-001",
                name="Chilonzor demo filial",
                address="Toshkent, Chilonzor",
                phone="+998711112233",
                is_active=True,
                metadata_json={},
            )
            db.add(branch)
            await db.flush()

        employee = (
            await db.execute(select(Employee).where(Employee.phone == "+998901234567"))
        ).scalar_one_or_none()
        if not employee:
            employee = Employee(
                branch_id=branch.id,
                employee_code="EMP-001",
                full_name="Demo Farmatsevt",
                phone="+998901234567",
                position="Farmatsevt",
                role_code="PHARMACIST",
                is_active=True,
            )
            db.add(employee)

        await db.commit()
        print("OK")
        print("Filial:", branch.name, branch.code)
        print("Xodim telefon (Telegramda ulashing): +998901234567")
        print("Admin login: admin@pharmacy.uz / ChangeMeNow!123")


if __name__ == "__main__":
    asyncio.run(main())
