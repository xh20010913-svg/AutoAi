from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Agent, Task
from app.runtime_utils import get_system_metrics
from app.schemas.runtime import RuntimeResponse, TaskStats
from app.ws import ws_manager

router = APIRouter(tags=["runtime"])


@router.get("/runtime", response_model=RuntimeResponse)
async def get_runtime(
    session: AsyncSession = Depends(get_session),
):
    agent_result = await session.execute(select(func.count(Agent.id)))
    agent_count = agent_result.scalar() or 0

    total_result = await session.execute(select(func.count(Task.id)))
    total_tasks = total_result.scalar() or 0

    status_result = await session.execute(
        select(Task.status, func.count(Task.id)).group_by(Task.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    sys_data = get_system_metrics()

    return RuntimeResponse(
        active_agents=agent_count,
        total_tasks=TaskStats(total=total_tasks, by_status=by_status),
        cpu_usage=sys_data["cpu_usage"],
        memory_usage=sys_data["memory_usage"],
        uptime=sys_data["uptime"],
    )


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_json({"event": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)
