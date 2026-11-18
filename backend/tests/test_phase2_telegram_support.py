from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Branch, Employee, Region
from app.services import conversation as conversation_service
from app.services.tickets import create_ticket_from_conversation
from app.db.seed import seed_reference_data
from app.services.org import get_or_create_default_company


async def _seed_employee(db_engine, phone: str = "+998901112233"):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        await seed_reference_data(db)
        company = await get_or_create_default_company(db)
        region = Region(company_id=company.id, name="Toshkent", code=f"T{uuid4().hex[:4].upper()}")
        db.add(region)
        await db.flush()
        branch = Branch(
            region_id=region.id,
            code=f"B{uuid4().hex[:4].upper()}",
            name="Test filial",
            is_active=True,
            metadata_json={},
        )
        db.add(branch)
        await db.flush()
        employee = Employee(
            branch_id=branch.id,
            employee_code=f"E{uuid4().hex[:4]}",
            full_name="Test Xodim",
            phone=phone,
            role_code="PHARMACIST",
            is_active=True,
        )
        db.add(employee)
        await db.commit()
        return employee.id, branch.id, phone


@pytest.mark.asyncio
async def test_telegram_text_and_ticket_flow(db_engine, client: AsyncClient, admin_token: str):
    employee_id, branch_id, phone = await _seed_employee(db_engine)
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=123456789,
            chat_id=123456789,
            username="test_user",
            language_code="uz",
        )
        employee = await conversation_service.bind_employee_by_phone(db, account, phone)
        conversation = await conversation_service.get_open_conversation(
            db,
            employee_id=employee.id,
            branch_id=employee.branch_id,
            telegram_account_id=account.id,
        )
        message = await conversation_service.add_message(
            db,
            conversation=conversation,
            sender_type="EMPLOYEE",
            content_text="Chek chiqmayapti",
            content_type="TEXT",
            sender_employee_id=employee.id,
            telegram_update_id=1001,
            idempotency_key="tg:1001",
        )
        # duplicate should not create second row
        dup = await conversation_service.add_message(
            db,
            conversation=conversation,
            sender_type="EMPLOYEE",
            content_text="Chek chiqmayapti",
            content_type="TEXT",
            sender_employee_id=employee.id,
            telegram_update_id=1001,
            idempotency_key="tg:1001",
        )
        assert dup.id == message.id

        ticket = await create_ticket_from_conversation(
            db,
            conversation=conversation,
            title="Chek chiqmayapti",
            description="Printerdan chiqmayapti",
            actor_type="EMPLOYEE",
            actor_id=str(employee_id),
        )
        await db.commit()
        ticket_id = ticket.id

    headers = {"Authorization": f"Bearer {admin_token}"}
    conversations = await client.get("/api/v1/conversations", headers=headers)
    assert conversations.status_code == 200
    assert len(conversations.json()) >= 1

    tickets = await client.get("/api/v1/tickets", headers=headers)
    assert tickets.status_code == 200
    assert any(t["id"] == str(ticket_id) for t in tickets.json())

    me = await client.get("/api/v1/auth/me", headers=headers)
    admin_id = me.json()["id"]
    assigned = await client.post(
        f"/api/v1/tickets/{ticket_id}/assign",
        headers=headers,
        json={"assignee_id": admin_id},
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["status"] == "IN_PROGRESS"

    escalated = await client.post(
        f"/api/v1/tickets/{ticket_id}/escalate",
        headers=headers,
        json={"comment": "Kerak bo'ldi"},
    )
    assert escalated.status_code == 200
    assert escalated.json()["status"] == "HUMAN_SUPPORT"


@pytest.mark.asyncio
async def test_screenshot_upload_bytes(db_engine):
    employee_id, branch_id, phone = await _seed_employee(db_engine, phone="+998909998877")
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        account = await conversation_service.get_or_create_telegram_account(
            db,
            telegram_user_id=222,
            chat_id=222,
            username="shot",
            language_code="uz",
        )
        employee = await conversation_service.bind_employee_by_phone(db, account, phone)
        conversation = await conversation_service.get_open_conversation(
            db,
            employee_id=employee.id,
            branch_id=branch_id,
            telegram_account_id=account.id,
        )
        message = await conversation_service.add_message(
            db,
            conversation=conversation,
            sender_type="EMPLOYEE",
            content_text="screenshot",
            content_type="IMAGE",
            sender_employee_id=employee_id,
            idempotency_key="tg:img:1",
        )
        att = await conversation_service.save_attachment_bytes(
            db,
            message=message,
            data=b"\xff\xd8\xff\xd9",
            kind="IMAGE",
            mime_type="image/jpeg",
            original_name="err.jpg",
        )
        await db.commit()
        assert att.size_bytes > 0
        assert att.kind == "IMAGE"
