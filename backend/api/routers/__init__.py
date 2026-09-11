# Modular API Routers for FastAPI
from backend.api.routers.common import router as common_router
from backend.api.routers.schedule import router as schedule_router
from backend.api.routers.homework import router as homework_router
from backend.api.routers.games import router as games_router
from backend.api.routers.durak import router as durak_router

__all__ = [
    "common_router",
    "schedule_router",
    "homework_router",
    "games_router",
    "durak_router",
]
