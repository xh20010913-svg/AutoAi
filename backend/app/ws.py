import asyncio
import logging
from datetime import datetime

from fastapi import WebSocket

from app.runtime_utils import get_system_metrics

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._broadcast_task: asyncio.Task | None = None

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.remove(ws)

    async def broadcast(self, data: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)

    def start_broadcast_loop(self, interval: float = 5.0) -> None:
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._broadcast_loop(interval))

    def stop_broadcast_loop(self) -> None:
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()

    async def _broadcast_loop(self, interval: float) -> None:
        while True:
            try:
                if self._connections:
                    from app.database import async_session
                    from app.models.project import Agent, Task
                    from sqlalchemy import func, select

                    sys_data = get_system_metrics()

                    async with async_session() as session:
                        agent_result = await session.execute(select(func.count(Agent.id)))
                        agent_count = agent_result.scalar() or 0

                        total_result = await session.execute(select(func.count(Task.id)))
                        total_tasks = total_result.scalar() or 0

                        status_result = await session.execute(
                            select(Task.status, func.count(Task.id)).group_by(Task.status)
                        )
                        by_status = {row[0]: row[1] for row in status_result.all()}

                    payload = {
                        "event": "runtime_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "active_agents": agent_count,
                        "total_tasks": {"total": total_tasks, "by_status": by_status},
                        "cpu_usage": sys_data["cpu_usage"],
                        "memory_usage": sys_data["memory_usage"],
                        "uptime": sys_data["uptime"],
                    }
                    await self.broadcast(payload)
            except Exception:
                logger.exception("Error in runtime broadcast loop")
            await asyncio.sleep(interval)


ws_manager = ConnectionManager()
