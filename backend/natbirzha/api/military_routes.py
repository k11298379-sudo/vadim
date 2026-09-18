from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import get_db_session
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.models.military import NatArmy, NatTournament
from backend.natbirzha.services.auth_service import get_current_company
from backend.natbirzha.services.military_service import MilitaryService
from backend.natbirzha.services.idempotency_service import IdempotencyService

router = APIRouter(prefix="/military", tags=["Natbirzha Military"])

class RecruitRequest(BaseModel):
    unit_type: str
    count: int = Field(gt=0)

class JoinAllianceRequest(BaseModel):
    alliance_id: int

@router.get("/status")
async def get_military_status(
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    army_res = await session.execute(select(NatArmy).where(NatArmy.company_id == company.id))
    army = army_res.scalar_one_or_none()
    return {
        "company_id": company.id,
        "infantry": army.infantry if army else 0,
        "tanks": army.tanks if army else 0,
        "drones": army.drones if army else 0,
        "air_defense": army.air_defense if army else 0,
        "army_strength": army.army_strength if army else 0,
        "nat_balance": company.nat_balance
    }

@router.get("/tournaments/current")
@router.get("/tournament")
async def get_current_tournament(
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    from backend.natbirzha.models.military import NatTournamentParticipant
    res = await session.execute(
        select(NatTournament).order_by(NatTournament.id.desc()).limit(1)
    )
    tourn = res.scalar_one_or_none()
    if not tourn:
        return {"tournament": None, "participants": []}

    part_res = await session.execute(
        select(NatTournamentParticipant, NatCompany)
        .join(NatCompany, NatTournamentParticipant.company_id == NatCompany.id)
        .where(NatTournamentParticipant.tournament_id == tourn.id)
        .order_by(NatTournamentParticipant.snapshot_strength.desc())
        .limit(10)
    )
    participants = [
        {
            "company_id": c.id,
            "company_name": c.name,
            "score": p.snapshot_strength,
            "rank": p.final_rank
        }
        for p, c in part_res.all()
    ]
    return {
        "tournament": {
            "id": tourn.id,
            "cycle_number": tourn.cycle_number,
            "status": tourn.status,
            "snapshot_time": str(tourn.snapshot_time) if tourn.snapshot_time else None,
            "finish_time": str(tourn.finish_time) if tourn.finish_time else None,
        },
        "participants": participants
    }

@router.post("/recruit")
async def recruit_units(
    req: RecruitRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/military/recruit", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        res = await MilitaryService.recruit_units(session, company, req.unit_type, req.count)
        await IdempotencyService.save_record(
            session, company.user_id, "/api/natbirzha/military/recruit", idempotency_key, req.model_dump(), 200, res
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/alliance/join")
async def join_alliance(
    req: JoinAllianceRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    cached = await IdempotencyService.check_or_conflict(
        session, company.user_id, "/api/natbirzha/military/alliance/join", idempotency_key, req.model_dump()
    )
    if cached:
        return cached[1]

    try:
        res = await MilitaryService.join_alliance(session, req.alliance_id, company)
        await IdempotencyService.save_record(
            session, company.user_id, "/api/natbirzha/military/alliance/join", idempotency_key, req.model_dump(), 200, res
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/tournament/{tournament_id}/resolve")
async def resolve_tournament(
    tournament_id: int,
    company: NatCompany = Depends(get_current_company),
    session: AsyncSession = Depends(get_db_session)
):
    try:
        return await MilitaryService.resolve_tournament(session, tournament_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
