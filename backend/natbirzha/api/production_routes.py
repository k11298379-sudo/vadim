from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import get_db_session
from backend.natbirzha.config import get_game_now, nat_settings
from backend.natbirzha.models.company import NatCompany, NatFactory
from backend.natbirzha.models.inventory import NatInventory, CANONICAL_ITEMS
from backend.natbirzha.services.auth_service import get_current_company
from backend.natbirzha.services.recipes import RECIPES
from backend.natbirzha.services.production_service import ProductionTickEngine
from backend.natbirzha.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/production", tags=["Natbirzha Production"])

BUILDING_ALIASES = {
    "metallurgy_smelter": "smelter",
    "coal_power_plant": "thermal_plant",
    "oil_refinery": "refinery",
    "chemical_plant": "chem_plant",
    "cement_factory": "machinery_plant",
    "data_center": "electronics_fab",
}

class BuildFactoryRequest(BaseModel):
    building_type: Optional[str] = None
    factory_type: Optional[str] = None

    @property
    def canonical_type(self) -> str:
        raw = self.building_type or self.factory_type or ""
        return BUILDING_ALIASES.get(raw, raw).strip()

class ProduceRequest(BaseModel):
    factory_id: int
    recipe_id: Optional[str] = None

@router.get("/recipes")
async def get_recipes():
    return {"recipes": RECIPES}

@router.get("/inventory")
async def get_inventory(
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    inv_res = await session.execute(
        select(NatInventory).where(NatInventory.company_id == company.id)
    )
    items = inv_res.scalars().all()
    return {
        "inventory": [
            {
                "item_id": it.item_id,
                "name": CANONICAL_ITEMS.get(it.item_id, {}).get("name", it.item_id),
                "unit": CANONICAL_ITEMS.get(it.item_id, {}).get("unit", "шт."),
                "quantity": it.quantity,
                "reserved": it.reserved_quantity,
                "available": it.available_quantity,
                "avg_cost": it.avg_cost_basis
            }
            for it in items if it.quantity > 0 or it.reserved_quantity > 0
        ]
    }

@router.get("/factories")
async def get_factories(
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    fac_res = await session.execute(
        select(NatFactory).where(NatFactory.company_id == company.id)
    )
    factories = fac_res.scalars().all()
    return {
        "factories": [
            {
                "id": f.id,
                "building_type": f.building_type,
                "factory_type": f.building_type,
                "specialization": f.specialization,
                "level": f.level,
                "tier": f.level,
                "efficiency": ProductionTickEngine.get_effective_efficiency(company, f),
                "is_active": f.is_active,
                "workers": f.workers,
                "last_produced_at": str(f.last_produced_at)
            }
            for f in factories
        ]
    }

@router.post("/factory/build")
async def build_factory(
    req: BuildFactoryRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/production/factory/build", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    b_type = req.canonical_type
    recipe = next((r for r in RECIPES.values() if r["factory_type"] == b_type), None)
    if not recipe:
        raise HTTPException(status_code=400, detail=f"Неизвестный тип предприятия: '{b_type or 'не указан'}'.")

    # Check territory space (1 factory per tile)
    fac_res = await session.execute(select(NatFactory).where(NatFactory.company_id == company.id))
    existing_factories = fac_res.scalars().all()
    existing_count = len(existing_factories)
    if existing_count >= company.territory_tiles:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно территории ({existing_count}/{company.territory_tiles} занято). Расширьте территорию компании."
        )

    cost = nat_settings.get_factory_cost(b_type, existing_count)
    if company.cash < cost:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно средств. Требуется: {cost:,.0f} cash, доступно: {company.cash:,.0f} cash"
        )

    company.cash -= cost
    now = get_game_now()
    factory = NatFactory(
        company_id=company.id,
        building_type=b_type,
        specialization=recipe["specialization"],
        level=1,
        efficiency=1.0,
        is_active=True,
        workers=10,
        automation_level=0,
        last_produced_at=now,
        created_at=now
    )
    session.add(factory)
    await session.commit()
    await session.refresh(factory)

    resp = {
        "success": True,
        "factory_id": factory.id,
        "building_type": factory.building_type,
        "cost_paid": cost,
        "remaining_cash": company.cash
    }
    await IdempotencyService.save_record(
        session, company.user_id, "/api/natbirzha/production/factory/build", idempotency_key, req.model_dump(), 200, resp
    )
    return resp

@router.post("/factory/produce")
async def produce_manual(
    req: ProduceRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Manual production trigger:
    Delegates directly to the single unified ProductionTickEngine!
    """
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/production/factory/produce", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    res = await ProductionTickEngine.execute_manual_produce(session, company.id, req.factory_id)
    if not res.get("success"):
        err_msg = res.get("error") or res.get("message") or "Ошибка производственного цикла."
        raise HTTPException(status_code=400, detail=str(err_msg))

    await session.commit()
    await IdempotencyService.save_record(
        session, company.user_id, "/api/natbirzha/production/factory/produce", idempotency_key, req.model_dump(), 200, res
    )
    return res
