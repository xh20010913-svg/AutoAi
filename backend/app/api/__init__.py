from fastapi import APIRouter

from app.api.agents import router as agents_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.api.websocket import router as ws_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(tasks_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(ws_router)
api_router.include_router(agents_router)
