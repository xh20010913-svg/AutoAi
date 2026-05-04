import json
from collections import defaultdict

from fastapi import WebSocket


class NotificationManager:
    """Manages WebSocket connections per user for real-time notification push."""

    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        self._connections[user_id].discard(websocket)
        if not self._connections[user_id]:
            del self._connections[user_id]

    async def send_to_user(self, user_id: str, data: dict):
        dead = []
        for ws in self._connections.get(user_id, set()):
            try:
                await ws.send_text(json.dumps(data, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)


notification_manager = NotificationManager()
