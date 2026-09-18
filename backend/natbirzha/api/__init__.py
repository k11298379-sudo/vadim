from fastapi import APIRouter

from backend.natbirzha.api.auth_routes import router as auth_router
from backend.natbirzha.api.company_routes import router as company_router
from backend.natbirzha.api.production_routes import router as production_router
from backend.natbirzha.api.market_routes import router as market_router
from backend.natbirzha.api.stock_routes import router as stock_router
from backend.natbirzha.api.military_routes import router as military_router
from backend.natbirzha.api.alliance_routes import router as alliance_router
from backend.natbirzha.api.bankruptcy_routes import router as bankruptcy_router
from backend.natbirzha.api.building_routes import router as building_router

natbirzha_router = APIRouter(prefix="/natbirzha")

natbirzha_router.include_router(auth_router)
natbirzha_router.include_router(company_router)
natbirzha_router.include_router(production_router)
natbirzha_router.include_router(building_router)
natbirzha_router.include_router(market_router)
natbirzha_router.include_router(stock_router)
natbirzha_router.include_router(military_router)
natbirzha_router.include_router(alliance_router)
natbirzha_router.include_router(bankruptcy_router)

__all__ = ["natbirzha_router"]
