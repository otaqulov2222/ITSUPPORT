from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ROOT_DIR
from app.db.models import Branch, Region
from app.services.org import get_or_create_default_company

LOCATION_CANDIDATES = [
    Path(__file__).resolve().parents[2] / "data" / "lokatsiyalar.txt",  # backend/data
    ROOT_DIR / "lokatsiyalar.txt",
    ROOT_DIR / "data" / "lokatsiyalar.txt",
    Path("/app/data/lokatsiyalar.txt"),
]


@dataclass
class LocationRow:
    number: int | None
    name: str
    lat: float | None
    lon: float | None

    @property
    def code(self) -> str:
        if self.number is None:
            return "F-000"
        return f"F-{self.number:03d}"


def find_locations_file() -> Path | None:
    for path in LOCATION_CANDIDATES:
        if path.exists():
            return path
    return None


def parse_locations_file(path: Path) -> list[LocationRow]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [ln.strip() for ln in text.splitlines()]
    rows: list[LocationRow] = []
    i = 0
    name_re = re.compile(r"^(?:(\d+)\.\s*)?(.+)$")
    coord_re = re.compile(r"^([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)$")

    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue
        m = name_re.match(line)
        if not m:
            i += 1
            continue
        num = int(m.group(1)) if m.group(1) else None
        name = m.group(2).strip()
        lat = lon = None
        if i + 1 < len(lines):
            cm = coord_re.match(lines[i + 1].strip())
            if cm:
                lat = float(cm.group(1))
                lon = float(cm.group(2))
                i += 2
            else:
                i += 1
        else:
            i += 1
        if name:
            rows.append(LocationRow(number=num, name=name, lat=lat, lon=lon))
    return rows


async def seed_branches_from_locations(db: AsyncSession) -> int:
    path = find_locations_file()
    if not path:
        return 0

    company = await get_or_create_default_company(db, name="VAKSINAMED")
    region = (await db.execute(select(Region).where(Region.code == "UZ"))).scalar_one_or_none()
    if not region:
        region = Region(company_id=company.id, name="O'zbekiston", code="UZ", is_active=True)
        db.add(region)
        await db.flush()

    created = 0
    for loc in parse_locations_file(path):
        existing = (
            await db.execute(select(Branch).where(Branch.code == loc.code))
        ).scalar_one_or_none()
        meta = {
            "source": "lokatsiyalar.txt",
            "location_number": loc.number,
            "lat": loc.lat,
            "lon": loc.lon,
            "uses_fom": True,
        }
        if existing:
            existing.name = loc.name
            existing.is_active = True
            existing.metadata_json = meta
            if existing.deleted_at is not None:
                existing.deleted_at = None
            continue

        db.add(
            Branch(
                region_id=region.id,
                code=loc.code,
                name=loc.name,
                address=f"{loc.lat}, {loc.lon}" if loc.lat is not None else None,
                timezone="Asia/Tashkent",
                is_active=True,
                metadata_json=meta,
            )
        )
        created += 1

    await db.flush()
    return created
