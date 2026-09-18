from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import get_db_session
from backend.db.models import User
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.services.auth_service import get_strict_natbirzha_user, get_current_company
from backend.natbirzha.services.company_service import CompanyService
from backend.natbirzha.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/company", tags=["Natbirzha Company"])

class CreateCompanyRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    specialization: str
    ticker: Optional[str] = None
    territory_hex: Optional[str] = None

class RespecRequest(BaseModel):
    new_specialization: str

@router.post("/create")
async def create_company(
    req: CreateCompanyRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    user: User = Depends(get_strict_natbirzha_user),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, user.id, "/api/natbirzha/company/create", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        company = await CompanyService.create_company(
            session, user.id, req.name, req.specialization
        )
        resp = {
            "success": True,
            "company_id": company.id,
            "name": company.name,
            "ticker": req.ticker or company.name[:4].upper(),
            "specialization": company.specialization,
            "cash": company.cash,
            "territory_tiles": company.territory_tiles
        }
        await IdempotencyService.save_record(
            session, user.id, "/api/natbirzha/company/create", idempotency_key, req.model_dump(), 200, resp
        )
        return resp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
@router.get("/status")
async def get_company_status(
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    nav = await CompanyService.calculate_audited_nav(session, company)
    from backend.natbirzha.models.inventory import NatInventory
    inv_res = await session.execute(select(NatInventory).where(NatInventory.company_id == company.id))
    inv = {row.item_id: row.quantity for row in inv_res.scalars().all()}
    from backend.natbirzha.models.company import NatFactory
    fac_res = await session.execute(select(NatFactory).where(NatFactory.company_id == company.id))
    from backend.natbirzha.services.recipes import RECIPES
    recipe_for_type = {r["factory_type"]: r_id for r_id, r in RECIPES.items()}
    from backend.natbirzha.config import get_game_tz
    def _format_dt_iso(dt):
        if not dt:
            return None
        if getattr(dt, 'tzinfo', None) is None:
            dt = dt.replace(tzinfo=get_game_tz())
        return dt.isoformat()

    from backend.natbirzha.config import normalize_dt, get_game_now
    now = normalize_dt(get_game_now())
    factories = []
    for f in fac_res.scalars().all():
        ready_at_norm = normalize_dt(f.cycle_ready_at)
        is_running = bool(f.cycle_ready_at)
        is_ready = bool(is_running and now >= ready_at_norm)
        rem_sec = 0
        if is_running and not is_ready:
            rem_sec = max(1, int((ready_at_norm - now).total_seconds()))
        factories.append({
            "id": f.id,
            "building_type": f.building_type,
            "specialization": f.specialization,
            "level": f.level,
            "tier": f.level,
            "factory_type": f.building_type,
            "is_active": f.is_active,
            "workers": f.workers,
            "automation_level": f.automation_level,
            "technology_level": f.technology_level,
            "current_recipe": f.current_recipe or recipe_for_type.get(f.building_type, "default"),
            "cycle_started_at": _format_dt_iso(f.cycle_started_at),
            "cycle_ready_at": _format_dt_iso(f.cycle_ready_at),
            "last_produced_at": _format_dt_iso(f.last_produced_at),
            "is_running": is_running,
            "is_ready": is_ready,
            "remaining_seconds": rem_sec
        })
    from backend.natbirzha.models.stocks import NatStock
    stock_res = await session.execute(
        select(NatStock).where(NatStock.company_id == company.id, NatStock.is_listed == True)
    )
    is_public = stock_res.scalar_one_or_none() is not None

    return {
        "id": company.id,
        "name": company.name,
        "ticker": getattr(company, "ticker", company.name[:4].upper()),
        "specialization": company.specialization,
        "level": company.level,
        "xp": company.xp,
        "cash": company.cash,
        "nat_balance": company.nat_balance,
        "territory_tiles": company.territory_tiles,
        "max_territory": company.max_territory,
        "audited_nav": nav,
        "nav": nav,
        "is_bankrupt": company.is_bankrupt,
        "is_public": is_public,
        "inventory": inv,
        "factories": factories
    }


@router.post("/territory/expand")
async def expand_territory(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/company/territory/expand", idempotency_key, {}
    )
    if cached:
        return cached[1]

    if company.territory_tiles >= company.max_territory:
        raise HTTPException(status_code=400, detail="Maximum territory limit reached.")

    # Cost scales: 10,000 * current_tiles
    cost = company.territory_tiles * 10000.0
    if company.cash < cost:
        raise HTTPException(status_code=400, detail=f"Insufficient cash. Needed: {cost}, Available: {company.cash}")

    company.cash -= cost
    company.territory_tiles += 1
    await session.commit()

    resp = {"success": True, "new_tiles": company.territory_tiles, "cost_paid": cost, "remaining_cash": company.cash}
    await IdempotencyService.save_record(
        session, company.user_id, "/api/natbirzha/company/territory/expand", idempotency_key, {}, 200, resp
    )
    return resp


@router.post("/respec")
async def respec_specialization(
    req: RespecRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/company/respec", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        res = await CompanyService.change_specialization(session, company, req.new_specialization)
        await IdempotencyService.save_record(
            session, company.user_id, "/api/natbirzha/company/respec", idempotency_key, req.model_dump(), 200, res
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class BuyLicenseRequest(BaseModel):
    target_specialization: str

@router.post("/license/buy")
async def buy_foreign_license_route(
    req: BuyLicenseRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/company/license/buy", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        res = await CompanyService.buy_foreign_license(session, company, req.target_specialization)
        await IdempotencyService.save_record(
            session, company.user_id, "/api/natbirzha/company/license/buy", idempotency_key, req.model_dump(), 200, res
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset")
async def reset_company_route(
    user: User = Depends(get_strict_natbirzha_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Completely resets company and assets so the player can restart onboarding."""
    ok = await CompanyService.reset_company_for_user(session, user.id)
    return {
        "success": True,
        "reset": ok,
        "message": "Company successfully reset. You can now choose a new specialization."
    }


