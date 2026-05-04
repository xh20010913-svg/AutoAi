from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, get_session
from app.models.run import Run, RunLog
from app.schemas.run import RunCreate, RunListResponse, RunLogResponse, RunResponse
from app.ws import manager

router = APIRouter(prefix="/runs", tags=["runs"])

# run_id -> subprocess.Process
_active_processes: dict[str, asyncio.subprocess.Process] = {}

# Session factory used by background tasks; overridable in tests.
_bg_session_factory = async_session


async def _read_stream(
    run_id: str,
    stream: asyncio.StreamReader,
    stream_name: str,
    session_factory,
    seq_counter: list[int],
) -> None:
    """Read lines from a subprocess stream, persist to DB, and broadcast."""
    while True:
        line = await stream.readline()
        if not line:
            break
        content = line.decode(errors="replace").rstrip("\n").rstrip("\r")
        seq_counter[0] += 1
        async with session_factory() as session:
            log = RunLog(
                run_id=run_id,
                seq=seq_counter[0],
                stream=stream_name,
                content=content,
            )
            session.add(log)
            await session.commit()
        await manager.broadcast(
            {
                "event": "run_log",
                "run_id": run_id,
                "stream": stream_name,
                "seq": seq_counter[0],
                "content": content,
            }
        )


async def _execute_run(run_id: str, command: str, timeout: int, session_factory) -> None:
    """Run a subprocess, capture output, update status on completion."""
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _active_processes[run_id] = proc

        async with session_factory() as session:
            run = await session.get(Run, run_id)
            if run:
                run.status = "running"
                run.started_at = datetime.now(UTC)
                await session.commit()

        await manager.broadcast({"event": "run_started", "run_id": run_id})

        seq_counter = [0]

        stdout_task = asyncio.create_task(
            _read_stream(run_id, proc.stdout, "stdout", session_factory, seq_counter)
        )
        stderr_task = asyncio.create_task(
            _read_stream(run_id, proc.stderr, "stderr", session_factory, seq_counter)
        )

        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

        await stdout_task
        await stderr_task

        exit_code = proc.returncode
        final_status = "succeeded" if exit_code == 0 else "failed"

        async with session_factory() as session:
            run = await session.get(Run, run_id)
            if run and run.status != "stopped":
                run.status = final_status
                run.exit_code = exit_code
                run.finished_at = datetime.now(UTC)
                await session.commit()

        await manager.broadcast(
            {
                "event": "run_finished",
                "run_id": run_id,
                "status": final_status,
                "exit_code": exit_code,
            }
        )

    except Exception as exc:
        async with session_factory() as session:
            run = await session.get(Run, run_id)
            if run and run.status not in ("stopped", "succeeded", "failed"):
                run.status = "failed"
                run.finished_at = datetime.now(UTC)
                await session.commit()
        await manager.broadcast(
            {"event": "run_finished", "run_id": run_id, "status": "failed", "error": str(exc)}
        )
    finally:
        _active_processes.pop(run_id, None)


@router.post("", response_model=RunResponse, status_code=201)
async def start_run(
    body: RunCreate,
    session: AsyncSession = Depends(get_session),
):
    run = Run(
        agent_id=body.agent_id,
        task_id=body.task_id,
        command=body.command,
        timeout=body.timeout,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    asyncio.create_task(_execute_run(run.id, body.command, body.timeout, _bg_session_factory))

    return run


@router.post("/{run_id}/stop", response_model=RunResponse)
async def stop_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    run = await session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail=f"Run is already {run.status}")

    proc = _active_processes.get(run_id)
    if proc:
        proc.kill()

    run.status = "stopped"
    run.finished_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(run)

    await manager.broadcast({"event": "run_finished", "run_id": run_id, "status": "stopped"})
    return run


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    run = await session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/logs", response_model=list[RunLogResponse])
async def get_run_logs(
    run_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    run = await session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    stmt = (
        select(RunLog)
        .where(RunLog.run_id == run_id)
        .order_by(RunLog.seq)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("", response_model=RunListResponse)
async def list_runs(
    agent_id: str | None = Query(None),
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Run)
    count_stmt = select(func.count()).select_from(Run)

    if agent_id:
        stmt = stmt.where(Run.agent_id == agent_id)
        count_stmt = count_stmt.where(Run.agent_id == agent_id)
    if status:
        stmt = stmt.where(Run.status == status)
        count_stmt = count_stmt.where(Run.status == status)

    stmt = stmt.order_by(Run.created_at.desc()).offset(offset).limit(limit)

    result = await session.execute(stmt)
    count_result = await session.execute(count_stmt)

    return RunListResponse(
        items=result.scalars().all(),
        total=count_result.scalar() or 0,
    )


@router.websocket("/ws")
async def runs_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
