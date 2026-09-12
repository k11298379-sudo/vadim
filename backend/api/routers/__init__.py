# Modular API Routers for FastAPI
from backend.api.routers.common import router as common_router
from backend.api.routers.schedule import router as schedule_router
from backend.api.routers.homework import router as homework_router
from backend.api.routers.games import router as games_router
from backend.api.routers.games_actions import router as games_actions_router
from backend.api.routers.durak import router as durak_router
from backend.api.routers.rpg import rpg_router
import backend.api.routers.rpg_combat  # Registers combat routes onto rpg_router

__all__ = [
    "common_router",
    "schedule_router",
    "homework_router",
    "games_router",
    "games_actions_router",
    "durak_router",
    "rpg_router",
]

