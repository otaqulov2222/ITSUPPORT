import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from app.core.rate_limit import rate_limiter


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_and_me(client: AsyncClient, admin_token: str):
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == get_settings().bootstrap_admin_email
    assert "SUPER_ADMIN" in body["roles"]


@pytest.mark.asyncio
async def test_employee_registration_and_branch_assignment(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    region = await client.post(
        "/api/v1/regions",
        headers=headers,
        json={"name": "Toshkent", "code": "TAS"},
    )
    assert region.status_code == 200, region.text
    region_id = region.json()["id"]

    branch = await client.post(
        "/api/v1/branches",
        headers=headers,
        json={
            "region_id": region_id,
            "code": "TAS-001",
            "name": "Chilonzor filiali",
            "address": "Chilonzor",
            "phone": "+998901112233",
        },
    )
    assert branch.status_code == 200, branch.text
    branch_id = branch.json()["id"]

    employee = await client.post(
        "/api/v1/employees",
        headers=headers,
        json={
            "branch_id": branch_id,
            "employee_code": "EMP-001",
            "full_name": "Ali Valiyev",
            "phone": "+998901234567",
            "position": "Farmatsevt",
            "role_code": "PHARMACIST",
        },
    )
    assert employee.status_code == 200, employee.text
    assert employee.json()["branch_id"] == branch_id

    listed = await client.get(
        f"/api/v1/employees?branch_id={branch_id}",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_unauthorized_branch_access_denied(
    client: AsyncClient,
    admin_token: str,
    limited_user_token: str,
):
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    region = await client.post(
        "/api/v1/regions",
        headers=headers_admin,
        json={"name": "Samarqand", "code": "SAM"},
    )
    branch = await client.post(
        "/api/v1/branches",
        headers=headers_admin,
        json={
            "region_id": region.json()["id"],
            "code": "SAM-001",
            "name": "Registon filiali",
        },
    )
    branch_id = branch.json()["id"]

    denied = await client.get(
        f"/api/v1/branches/{branch_id}",
        headers={"Authorization": f"Bearer {limited_user_token}"},
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_audit_log_created_on_branch_create(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    region = await client.post(
        "/api/v1/regions",
        headers=headers,
        json={"name": "Andijon", "code": "AND"},
    )
    await client.post(
        "/api/v1/branches",
        headers=headers,
        json={
            "region_id": region.json()["id"],
            "code": "AND-001",
            "name": "Andijon markaz",
        },
    )

    logs = await client.get("/api/v1/audit/logs", headers=headers)
    assert logs.status_code == 200
    actions = {item["action"] for item in logs.json()}
    assert "branch.create" in actions
    assert "region.create" in actions


@pytest.mark.asyncio
async def test_auth_rate_limiting(client: AsyncClient):
    # Reset limiter buckets for deterministic test
    rate_limiter._events.clear()
    settings = get_settings()
    original = settings.rate_limit_auth_per_minute
    settings.rate_limit_auth_per_minute = 3

    try:
        last_status = 200
        for _ in range(5):
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "nobody@example.com", "password": "wrong-password"},
            )
            last_status = response.status_code
            if last_status == 429:
                break
        assert last_status == 429
    finally:
        settings.rate_limit_auth_per_minute = original
        rate_limiter._events.clear()
