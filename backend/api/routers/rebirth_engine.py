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
    
    current_rank = getattr(char, "rebirths", 0)
    req_level = 50
    if current_rank == 0: req_level = 30
    elif current_rank == 1: req_level = 40
    elif current_rank == 2: req_level = 45

    if char.level < req_level:
        raise HTTPException(status_code=400, detail=f"Нужен {req_level} уровень для Вознесения!")
    
    essence_reward = 0
    if current_rank == 0: essence_reward = 3
    elif current_rank == 1: essence_reward = 5
    elif current_rank == 2: essence_reward = 8
    elif current_rank == 3: essence_reward = 12
    elif current_rank == 4: essence_reward = 18
    else: essence_reward = 25

    char.level = 1
    char.xp = 0
    char.rebirths = current_rank + 1
    # Store essence in json 'talents' since we can't easily alter postgres schema directly here without migration
    talents = dict(getattr(char, "talents", {}) or {})
    talents["rebirth_essence"] = talents.get("rebirth_essence", 0) + essence_reward
    char.talents = talents
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(char, "talents")

    await session.commit()
    await session.refresh(char)
    
    return {
        "success": True,
        "message": f"Вознесение успешно! Ранг: {char.rebirths}. Получено ✨ {essence_reward} Астральной Эссенции.",
        "profile": serialize_character_profile(char)
    }