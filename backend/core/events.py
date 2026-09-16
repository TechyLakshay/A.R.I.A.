"""Server event bus: one set of connected WebSocket clients + broadcast."""

from fastapi import WebSocket

clients: set[WebSocket] = set()


async def broadcast(event: dict) -> None:
    dead: list[WebSocket] = []
    for sock in clients:
        try:
            await sock.send_json(event)
        except Exception:
            dead.append(sock)
    for sock in dead:
        clients.discard(sock)
