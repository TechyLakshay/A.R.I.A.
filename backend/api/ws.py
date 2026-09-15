from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
clients: set[WebSocket] = set()


@router.websocket("/ws")
async def ws_endpoint(sock: WebSocket) -> None:
    await sock.accept()
    clients.add(sock)
    await sock.send_json({"type": "hello", "user_id": 1})
    try:
        while True:
            msg = await sock.receive_json()
            await sock.send_json({"type": "echo", "data": msg})
    except WebSocketDisconnect:
        clients.discard(sock)
