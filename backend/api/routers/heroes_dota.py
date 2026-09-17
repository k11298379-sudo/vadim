import random
import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from backend.config import settings
from backend.db.session import get_db_session
from backend.db.models import User
from backend.api.auth import get_optional_webapp_user
from backend.db.crud.rpg import (
    NATAR_HEROES,
    DOTA_HEROES,
    get_or_create_rpg_character,
    serialize_character_profile,
    reset_rpg_character,
    upgrade_character_base_stat,
    open_wave_chest,
)

rpg_router = APIRouter(prefix="/rpg", tags=["rpg"])


@rpg_router.get("/heroes")
async def get_dota_heroes_endpoint():
    """Returns list of all available natarGRP heroes."""
    return list(DOTA_HEROES.values())


@rpg_router.post("/chest/open")
async def open_chest_endpoint(
    payload: Dict[str, Any] = Body(default={}),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Opens a reward chest earned every 10-20 waves."""
    user_id = user.id if user else 1
    user_name = user.display_name if user else "Герой natarGRP"

    char = await get_or_create_rpg_character(session, user_id=user_id)
    wave = payload.get("wave", char.dungeon_cleared)
    
    if wave > char.dungeon_cleared:
        raise HTTPException(status_code=400, detail="Эта волна еще не пройдена!")
        
    talents = dict(char.talents or {})
    last_chest_wave = talents.get("_last_chest_wave", 0)
    
    if wave <= last_chest_wave:
        raise HTTPException(status_code=400, detail="Сундук за эту волну уже открыт!")
        
    res = await open_wave_chest(session, char, wave)
    
    talents["_last_chest_wave"] = wave
    char.talents = talents
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(char, "talents")
    
    res["profile"] = serialize_character_profile(char, user_name=user_name)
    return res


@rpg_router.get("/profile")
async def get_rpg_profile_endpoint(
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Returns or initializes the RPG Character profile for the current user."""
    user_id = user.id if user else 1
    user_name = user.display_name if user else "Дотер 11 «Б»"

    char = await get_or_create_rpg_character(session, user_id=user_id)
    prof = serialize_character_profile(char, user_name=user_name)
    prof["is_admin"] = bool(user and (user.role == "admin" or user.tg_id == settings.ADMIN_ID or user.tg_id == 1053722876))
    prof["tg_id"] = user.tg_id if user else None
    return prof


@rpg_router.post("/class/select")
async def select_hero_class_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Selects or changes Dota 2 hero (Pudge, Jugg, PA, SF, Invoker, WK, AM)."""
    user_id = user.id if user else 1
    user_name = user.display_name if user else "Дотер 11 «Б»"

    hero_id = payload.get("hero_class", "pudge").strip().lower()
    if hero_id not in DOTA_HEROES:
        raise HTTPException(status_code=400, detail="Неизвестный герой Dota 2")

    char = await get_or_create_rpg_character(session, user_id=user_id)
    cfg = DOTA_HEROES[hero_id]

    char.hero_class = hero_id
    char.strength = cfg["str"]
    char.agility = cfg["agi"]
    char.intelligence = cfg["int"]
    char.vitality = cfg.get("vit", cfg["str"])

    starter_w = dict(cfg.get("starter_weapon", {}))
    if starter_w:
        starter_w["uid"] = f"w_{hero_id[:4]}_{str(uuid.uuid4())[:6]}"
        starter_w["slot"] = "slot_1"
        
    starter_a = dict(cfg.get("starter_armor", {}))
    if starter_a:
        starter_a["uid"] = f"a_{hero_id[:4]}_{str(uuid.uuid4())[:6]}"
        starter_a["slot"] = "slot_2"

    inventory = list(char.inventory or [])
    eq = dict(char.equipment or {})

    for slot_k, item in eq.items():
        if item and len(inventory) < 200:
            inventory.append(item)
    
    eq = {}
    if starter_w:
        eq["slot_1"] = starter_w
    if starter_a:
        eq["slot_2"] = starter_a
    char.equipment = eq
    char.inventory = inventory
    flag_modified(char, "equipment")
    flag_modified(char, "inventory")

    await session.commit()
    await session.refresh(char)
    return serialize_character_profile(char, user_name=user_name)


@rpg_router.post("/upgrade/stat")
async def upgrade_stat_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Upgrades Strength, Agility, Intelligence or Vitality using free stat points or farmed gold."""
    user_id = user.id if user else 1
    stat_name = payload.get("stat", "").strip().lower()

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg = await upgrade_character_base_stat(session, char, stat_name)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "profile": serialize_character_profile(char, user_name=user_name)
    }


@rpg_router.post("/reset")
async def reset_character_endpoint(
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Hardcore Reset: Resets RPG character to level 1 for a fresh grind."""
    user_id = user.id if user else 1
    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg = await reset_rpg_character(session, char)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "profile": serialize_character_profile(char, user_name=user_name)
    }


@rpg_router.post("/talents/upgrade")
async def upgrade_talent_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    user_id = user.id if user else 1
    user_name = user.display_name if user else "Герой natarGRP"
    char = await get_or_create_rpg_character(session, user_id=user_id)
    
    talent_id = payload.get("talent_id")
    if not talent_id:
        raise HTTPException(status_code=400, detail="Missing talent_id")
    
    VALID_TALENTS = {"lifesteal", "crit_mult", "cooldown", "dodge"}
    if talent_id not in VALID_TALENTS:
        raise HTTPException(status_code=400, detail="Неизвестный талант")
        
    if char.talent_points <= 0:
        raise HTTPException(status_code=400, detail="Нет очков талантов!")
        
    talents = dict(char.talents or {})
    current_lvl = talents.get(talent_id, 0)
    
    # Cap talents at level 5
    if current_lvl >= 5:
        raise HTTPException(status_code=400, detail="Талант максимального уровня!")
        
    talents[talent_id] = current_lvl + 1
    char.talents = talents
    char.talent_points -= 1
    
    # Since we modify a JSON column in SQLAlchemy, we need to flag it as modified
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(char, "talents")
    
    await session.commit()
    
    return {"status": "ok", "profile": serialize_character_profile(char, user_name=user_name)}
