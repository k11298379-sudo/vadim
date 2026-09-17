from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db_session
from backend.db.models import User
from backend.api.auth import get_optional_webapp_user
from backend.db.crud.rpg import get_or_create_rpg_character, serialize_character_profile

rebirth_engine_router = APIRouter(prefix="/rpg/rebirth_system", tags=["RPG Rebirth"])

@rebirth_engine_router.post("/")
async def perform_rebirth(
    user: User = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    user_id = user.id if user else 1
    char = await get_or_create_rpg_character(session, user_id=user_id)
    if char.level < 100:
        raise HTTPException(status_code=400, detail="Нужен 100 уровень!")
    
    char.level = 1
    char.xp = 0
    char.rebirths += 1
    await session.commit()
    await session.refresh(char)
    
    return {
        "success": True,
        "message": f"Перерождение успешно! Ранг: {char.rebirths}",
        "profile": serialize_character_profile(char)
    }
