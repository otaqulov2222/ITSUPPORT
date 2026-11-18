from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.realtime import realtime_hub
from app.core.security import safe_decode_token

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/admin")
async def admin_ws(websocket: WebSocket, token: str = Query(...)):
    payload = safe_decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4401)
        return

    channel = "admin:conversations"
    await realtime_hub.connect(channel, websocket)
    await realtime_hub.connect("admin:tickets", websocket)
    try:
        await websocket.send_json({"type": "connected", "channels": [channel, "admin:tickets"]})
        while True:
            # Keepalive / client pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await realtime_hub.disconnect(channel, websocket)
        await realtime_hub.disconnect("admin:tickets", websocket)
