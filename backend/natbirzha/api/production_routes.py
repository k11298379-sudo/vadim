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
from backend.natbirzha.services.building_service import BuildingService
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

def _format_dt_iso(dt):
    if not dt:
        return None
    from backend.natbirzha.config import get_game_tz
    if getattr(dt, 'tzinfo', None) is None:
        dt = dt.replace(tzinfo=get_game_tz())
    return dt.isoformat()

@router.get("/factories")
async def get_factories(
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    fac_res = await session.execute(
        select(NatFactory).where(NatFactory.company_id == company.id)
    )
    factories = fac_res.scalars().all()
    from backend.natbirzha.config import normalize_dt, get_game_now
    now = normalize_dt(get_game_now())
    items = []
    for f in factories:
        ready_at_norm = normalize_dt(f.cycle_ready_at)
        is_running = bool(f.cycle_ready_at)
        is_ready = bool(is_running and now >= ready_at_norm)
        rem_sec = 0
        if is_running and not is_ready:
            rem_sec = max(1, int((ready_at_norm - now).total_seconds()))
        items.append({
            "id": f.id,
            "building_type": f.building_type,
            "factory_type": f.building_type,
            "specialization": f.specialization,
            "level": f.level,
            "tier": f.level,
            "efficiency": ProductionTickEngine.get_effective_efficiency(company, f),
            "is_active": f.is_active,
            "workers": f.workers,
            "automation_level": f.automation_level,
            "technology_level": f.technology_level,
            "current_recipe": f.current_recipe or next((k for k, v in RECIPES.items() if v.get("factory_type") == f.building_type), None),
            "cycle_started_at": _format_dt_iso(f.cycle_started_at),
            "cycle_ready_at": _format_dt_iso(f.cycle_ready_at),
            "last_produced_at": _format_dt_iso(f.last_produced_at),
            "is_running": is_running,
            "is_ready": is_ready,
            "remaining_seconds": rem_sec
        })
    return {"factories": items}

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
    try:
        resp = await BuildingService.build_factory(session, company, b_type, idempotency_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await session.commit()
    await IdempotencyService.save_record(
        session, company.user_id, "/api/natbirzha/production/factory/build", idempotency_key, req.model_dump(), 200, resp
    )
    return resp


class UpgradeFactoryRequest(BaseModel):
    factory_id: int
    upgrade_type: str

@router.post("/factory/upgrade")
async def upgrade_factory(
    req: UpgradeFactoryRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/production/factory/upgrade", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]
    try:
        resp = await BuildingService.upgrade_factory(session, company, req.factory_id, req.upgrade_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await session.commit()
    await IdempotencyService.save_record(
        session, company.user_id, "/api/natbirzha/production/factory/upgrade", idempotency_key, req.model_dump(), 200, resp
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

    res = await ProductionTickEngine.execute_manual_produce(session, company.id, req.factory_id, req.recipe_id)
    if not res.get("success"):
        reason = res.get("reason", "")
        if reason.startswith("insufficient_"):
            item_id = reason.replace("insufficient_", "")
            item_info = CANONICAL_ITEMS.get(item_id, {})
            item_name = item_info.get("name", item_id)
            needed = res.get("needed", 0)
            available = res.get("available", 0)
            unit = item_info.get("unit", "ед.")
            err_msg = f"Недостаточно сырья: {item_name} (требуется {needed} {unit}, на складе {available} {unit}). Купите на Бирже или добудьте на производстве."
        elif reason == "cycle_in_progress":
            rem = res.get("remaining_seconds", 0)
            err_msg = f"Цикл еще выполняется (осталось {rem} сек.)."
        elif reason == "cycle_ready_to_collect":
            err_msg = "Цикл готов! Нажмите «Забрать продукцию»."
        elif reason == "factory_inactive":
            err_msg = "Предприятие отключено."
        elif reason == "company_level_required":
            err_msg = f"Для рецепта требуется уровень компании {res.get('required_level', 1)}."
        elif reason == "recipe_not_available":
            err_msg = "Этот рецепт не подходит для данного типа предприятия."
        else:
            err_msg = res.get("error") or res.get("message") or f"Ошибка производственного цикла ({reason or 'сбой'})."
        raise HTTPException(status_code=400, detail=str(err_msg))


    await session.commit()
    await IdempotencyService.save_record(
        session, company.user_id, "/api/natbirzha/production/factory/produce", idempotency_key, req.model_dump(), 200, res
    )
    return res

@router.post("/factory/{factory_id}/start")
async def start_factory_production(
    factory_id: int,
    recipe_id: Optional[str] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, f"/api/natbirzha/production/factory/{factory_id}/start", idempotency_key, {"recipe_id": recipe_id}
    )
    if cached:
        return cached[1]
    factory = await session.get(NatFactory, factory_id)
    if not factory or factory.company_id != company.id:
        raise HTTPException(status_code=404, detail="Предприятие не найдено")
    res = await ProductionTickEngine.start_cycle(session, company, factory, recipe_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("reason", "Невозможно запустить цикл"))
    await session.commit()
    await IdempotencyService.save_record(
        session, company.user_id, f"/api/natbirzha/production/factory/{factory_id}/start", idempotency_key, {"recipe_id": recipe_id}, 200, res
    )
    return res

@router.post("/factory/{factory_id}/collect")
async def collect_factory_production(
    factory_id: int,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, f"/api/natbirzha/production/factory/{factory_id}/collect", idempotency_key, {}
    )
    if cached:
        return cached[1]
    factory = await session.get(NatFactory, factory_id)
    if not factory or factory.company_id != company.id:
        raise HTTPException(status_code=404, detail="Предприятие не найдено")
    res = await ProductionTickEngine.complete_cycle(session, company, factory)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("reason", "Невозможно собрать продукцию"))
    await session.commit()
    await IdempotencyService.save_record(
        session, company.user_id, f"/api/natbirzha/production/factory/{factory_id}/collect", idempotency_key, {}, 200, res
    )
    return res
