"""Background scheduler for periodic auto-assignment of todo tasks."""

from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.database import async_session
from app.services.auto_assign import auto_assign_all

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None


async def _run_scheduler() -> None:
    """Periodically scan todo tasks and auto-assign them."""
    logger.info(
        "Auto-assign scheduler started (interval=%ds)",
        settings.AUTO_ASSIGN_INTERVAL_SECONDS,
    )
    while True:
        try:
            await asyncio.sleep(settings.AUTO_ASSIGN_INTERVAL_SECONDS)
            async with async_session() as session:
                assignments = await auto_assign_all(session)
                if assignments:
                    logger.info(
                        "Scheduler auto-assigned %d tasks", len(assignments)
                    )
        except asyncio.CancelledError:
            logger.info("Auto-assign scheduler stopped")
            break
        except Exception:
            logger.exception("Auto-assign scheduler error")


def start_scheduler() -> None:
    """Start the background auto-assign scheduler."""
    global _task
    if not settings.AUTO_ASSIGN_ENABLED:
        logger.info("Auto-assign scheduler disabled via config")
        return
    if _task is None or _task.done():
        _task = asyncio.create_task(_run_scheduler())


def stop_scheduler() -> None:
    """Stop the background auto-assign scheduler."""
    global _task
    if _task and not _task.done():
        _task.cancel()
