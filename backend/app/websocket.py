import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._counter = 0

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        self._counter += 1
        conn_id = f"ws-{self._counter}"
        self._connections[conn_id] = websocket
        logger.info("WS connected: %s (total: %d)", conn_id, len(self._connections))
        return conn_id

    def disconnect(self, conn_id: str) -> None:
        self._connections.pop(conn_id, None)
        logger.info("WS disconnected: %s (total: %d)", conn_id, len(self._connections))

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        if not self._connections:
            return
        message = json.dumps({"event": event_type, "data": data})
        dead: list[str] = []
        for conn_id, ws in self._connections.items():
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(conn_id)
        for conn_id in dead:
            self._connections.pop(conn_id, None)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
