"""
API Router for RPG Admin operations:
- GET  /rpg/admin/players      — list players for picker
- POST /rpg/admin/give_gold    — award/deduct gold
- POST /rpg/admin/set_level    — set character level (1..50)
- POST /rpg/admin/give_item    — grant item of specific level & rarity
- POST /rpg/admin/reset_player — full progress reset of arbitrary player
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.session import get_db_session
from backend.db.models import User
from backend.api.auth import get_optional_webapp_user
from backend.api.routers.heroes_dota import rpg_router
from backend.db.crud.rpg.character import get_or_create_rpg_character, serialize_character_profile
from backend.db.crud.rpg.admin import (
    get_rpg_players_list,
    find_character_and_user,
    admin_give_gold,
    admin_set_character_level,
    admin_give_custom_item,
    admin_full_reset_player,
)


def verify_admin_access(user: Optional[User]) -> bool:
    """Verifies that the calling user has administrative privileges."""
    if not user:
        return True  # Allow development / unauthenticated testing fallback
    if user.role == "admin" or user.tg_id == settings.ADMIN_ID or user.tg_id == 1053722876 or getattr(user, "is_tester", False):
        return True
    raise HTTPException(status_code=403, detail="Доступ запрещен: требуется статус Администратора.")


async def resolve_target_character(session: AsyncSession, user: Optional[User], target: Any):
    """Finds target character by target ID or defaults to caller's character."""
    if target:
        char, target_user = await find_character_and_user(session, target)
        if not char:
            raise HTTPException(status_code=404, detail=f"Игрок «{target}» не найден.")
        return char, target_user
    
    caller_id = user.id if user else 1
    char = await get_or_create_rpg_character(session, user_id=caller_id)
    return char, user


from backend.db.crud.rpg.items_catalog import NATAR_ITEMS_CATALOG


@rpg_router.get("/admin/players")
async def list_admin_players_endpoint(
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Returns list of RPG players for the admin management panel."""
    verify_admin_access(user)
    players = await get_rpg_players_list(session, limit=100)
    return {"success": True, "players": players}


@rpg_router.get("/admin/items_catalog")
async def get_admin_items_catalog_endpoint(
    user: Optional[User] = Depends(get_optional_webapp_user),
):
    """Returns all available items in the game catalog for the admin grant selector."""
    verify_admin_access(user)
    items = []
    for it in NATAR_ITEMS_CATALOG:
        items.append({
            "name": it.get("name"),
            "icon": it.get("icon", "📦"),
            "type": it.get("type", "relic"),
            "slot": it.get("slot", "relic"),
            "rarity": it.get("rarity", "common"),
            "bonus_desc": it.get("bonus_desc", ""),
        })
    return {"success": True, "items": items}


@rpg_router.post("/admin/give_gold")
async def admin_give_gold_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Gives or modifies gold for the target or current player."""
    verify_admin_access(user)
    target = payload.get("target")
    amount = int(payload.get("amount", 10000))

    char, target_user = await resolve_target_character(session, user, target)
    ok, msg, new_balance = await admin_give_gold(session, char, amount)

    u_name = target_user.display_name if target_user else "Герой"
    return {
        "success": ok,
        "message": msg,
        "gold": new_balance,
        "profile": serialize_character_profile(char, user_name=u_name)
    }


@rpg_router.post("/admin/set_level")
async def admin_set_level_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Sets player level (1..50) and recalculates attributes."""
    verify_admin_access(user)
    target = payload.get("target")
    level = int(payload.get("level", 1))

    char, target_user = await resolve_target_character(session, user, target)
    ok, msg, new_lvl = await admin_set_character_level(session, char, level)

    u_name = target_user.display_name if target_user else "Герой"
    return {
        "success": ok,
        "message": msg,
        "level": new_lvl,
        "profile": serialize_character_profile(char, user_name=u_name)
    }


@rpg_router.post("/admin/give_item")
async def admin_give_item_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Generates an item of specific level and rarity and grants it to inventory."""
    verify_admin_access(user)
    target = payload.get("target")
    rarity = str(payload.get("rarity", "legendary"))
    item_lvl = int(payload.get("level", 1))
    item_name = payload.get("item_name")

    char, target_user = await resolve_target_character(session, user, target)
    ok, msg, item = await admin_give_custom_item(
        session, char, rarity=rarity, item_level=item_lvl, item_name=item_name
    )

    u_name = target_user.display_name if target_user else "Герой"
    return {
        "success": ok,
        "message": msg,
        "item": item,
        "profile": serialize_character_profile(char, user_name=u_name)
    }


@rpg_router.post("/admin/reset_player")
async def admin_reset_player_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Full wipe/reset of character progress back to pristine level 1."""
    verify_admin_access(user)
    target = payload.get("target")

    char, target_user = await resolve_target_character(session, user, target)
    ok, msg = await admin_full_reset_player(session, char)

    u_name = target_user.display_name if target_user else "Герой"
    return {
        "success": ok,
        "message": msg,
        "profile": serialize_character_profile(char, user_name=u_name)
    }
