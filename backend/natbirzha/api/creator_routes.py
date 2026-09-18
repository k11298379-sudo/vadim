from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.session import get_db_session
from backend.db.models import User
from backend.natbirzha.services.auth_service import get_strict_natbirzha_user
from backend.natbirzha.services.creator_service import CreatorService
from backend.natbirzha.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/creator", tags=["Natbirzha Creator & State"])

def is_creator_or_admin(user: User) -> bool:
    return bool(
        user.role == "admin"
        or (settings.ADMIN_ID and user.tg_id == settings.ADMIN_ID)
        or user.id == 1
        or user.tg_id == 1053722876
        or user.tg_id == 1
    )

async def get_current_creator(
    user: User = Depends(get_strict_natbirzha_user)
) -> User:
    if not is_creator_or_admin(user):
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещён: требуются полномочия Создателя или Администратора государства."
        )
    return user

class WarningRequest(BaseModel):
    company_id: int
    reason: str = Field(min_length=3)

class RestrictionRequest(BaseModel):
    company_id: Optional[int] = None
    item_id: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    reason: str = Field(min_length=3)
    duration_minutes: Optional[int] = None

class IssueBondRequest(BaseModel):
    title: str = Field(min_length=3)
    volume: int = Field(gt=0)
    face_value: float = Field(gt=0)
    coupon_rate: float = Field(ge=0)
    maturity_days: int = Field(gt=0)
    purpose: str = Field(min_length=3)

@router.get("/overview")
async def get_overview(
    _admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    return await CreatorService.get_overview(session)

@router.get("/market")
async def get_market(
    _admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    return await CreatorService.get_market_snapshot(session)

@router.post("/market/warnings")
async def send_warning(
    req: WarningRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, admin.id, "/api/natbirzha/creator/market/warnings", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        res = await CreatorService.add_warning(session, admin.tg_id, req.company_id, req.reason)
        await IdempotencyService.save_record(
            session, admin.id, "/api/natbirzha/creator/market/warnings", idempotency_key, req.model_dump(), 200, res
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/market/restrictions")
async def set_restriction(
    req: RestrictionRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, admin.id, "/api/natbirzha/creator/market/restrictions", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        res = await CreatorService.set_restriction(
            session, admin.tg_id, req.company_id, req.item_id,
            req.min_price, req.max_price, req.reason, req.duration_minutes
        )
        await IdempotencyService.save_record(
            session, admin.id, "/api/natbirzha/creator/market/restrictions", idempotency_key, req.model_dump(), 200, res
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/market/restrictions/{restriction_id}")
async def remove_restriction(
    restriction_id: int,
    admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    try:
        return await CreatorService.remove_restriction(session, admin.tg_id, restriction_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/bonds/issue")
async def issue_bonds(
    req: IssueBondRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, admin.id, "/api/natbirzha/creator/bonds/issue", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        res = await CreatorService.issue_bonds(
            session, admin.tg_id, req.title, req.volume,
            req.face_value, req.coupon_rate, req.maturity_days, req.purpose
        )
        await IdempotencyService.save_record(
            session, admin.id, "/api/natbirzha/creator/bonds/issue", idempotency_key, req.model_dump(), 200, res
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bonds")
async def get_bonds(
    _admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    return {"bonds": await CreatorService.get_bonds(session)}

@router.post("/tournaments/launch")
async def launch_tournament(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, admin.id, "/api/natbirzha/creator/tournaments/launch", idempotency_key, {}
    )
    if cached:
        return cached[1]

    res = await CreatorService.launch_early_tournament(session, admin.tg_id)
    await IdempotencyService.save_record(
        session, admin.id, "/api/natbirzha/creator/tournaments/launch", idempotency_key, {}, 200, res
    )
    return res

@router.get("/audit-log")
async def get_audit_log(
    limit: int = Query(50, ge=1, le=200),
    _admin: User = Depends(get_current_creator),
    session: AsyncSession = Depends(get_db_session)
):
    return {"logs": await CreatorService.get_audit_log(session, limit=limit)}
