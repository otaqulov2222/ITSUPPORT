import asyncio
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class RealtimeHub:
    """In-process WebSocket hub. Redis pub/sub fans out across workers later."""

    def __init__(self) -> None:
        self._clients: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients[channel].add(websocket)

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients[channel].discard(websocket)

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        payload = json.dumps(event, default=str)
        async with self._lock:
            clients = list(self._clients.get(channel, set()))
        dead: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(channel, ws)

    async def publish_conversation(self, conversation_id: UUID, event: dict[str, Any]) -> None:
        await self.publish("admin:conversations", event)
        await self.publish(f"conversation:{conversation_id}", event)

    async def publish_ticket(self, ticket_id: UUID, event: dict[str, Any]) -> None:
        await self.publish("admin:tickets", event)
        await self.publish(f"ticket:{ticket_id}", event)


realtime_hub = RealtimeHub()
