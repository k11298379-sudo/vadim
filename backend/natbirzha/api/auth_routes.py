from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.session import get_db_session
from backend.db.models import User
from backend.natbirzha.models.company import NatCompany
from backend.natbirzha.services.auth_service import get_strict_natbirzha_user

router = APIRouter(prefix="/auth", tags=["Natbirzha Auth"])

@router.post("/login")
@router.get("/login")
async def login_user(
    user: User = Depends(get_strict_natbirzha_user),
    session: AsyncSession = Depends(get_db_session)
):
    comp_res = await session.execute(select(NatCompany).where(NatCompany.user_id == user.id))
    company = comp_res.scalar_one_or_none()
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "tg_id": user.tg_id,
            "full_name": user.display_name,
            "role": user.role
        },
        "has_company": company is not None,
        "company_id": company.id if company else None,
        "company_name": company.name if company else None,
        "specialization": company.specialization if company else None
    }

@router.get("/me")
async def get_me(
    user: User = Depends(get_strict_natbirzha_user),
    session: AsyncSession = Depends(get_db_session)
):
    return await login_user(user, session)

