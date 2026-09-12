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
    DOTA_HEROES,
    get_or_create_rpg_character,
    serialize_character_profile,
    calculate_character_effective_stats,
    equip_item_for_character,
    unequip_item_from_character,
    use_consumable_item,
    get_rpg_shop_catalog,
    buy_item_from_shop,
    upgrade_item_forge,
    sell_item_from_inventory,
    sell_multiple_items_from_inventory,
    reset_rpg_character,
    upgrade_character_base_stat,
    open_wave_chest
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
    res = await open_wave_chest(session, char, wave)
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

    starter_w = dict(cfg["starter_weapon"])
    starter_w["uid"] = f"w_{hero_id[:4]}_{str(uuid.uuid4())[:6]}"
    starter_a = dict(cfg["starter_armor"])
    starter_a["uid"] = f"a_{hero_id[:4]}_{str(uuid.uuid4())[:6]}"

    inventory = list(char.inventory or [])
    eq = dict(char.equipment or {})

    for slot_k in ["weapon", "armor"]:
        old_it = eq.get(slot_k)
        if old_it and len(inventory) < 30:
            inventory.append(old_it)

    eq["weapon"] = starter_w
    eq["armor"] = starter_a
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


@rpg_router.post("/inventory/equip")
async def equip_item_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Equips a Dota item from inventory."""
    user_id = user.id if user else 1
    item_uid = payload.get("item_uid", "")

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg = await equip_item_for_character(session, char, item_uid)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "profile": serialize_character_profile(char, user_name=user_name)
    }


@rpg_router.post("/inventory/forge")
async def forge_item_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Upgrades Dota item level (+1..+100) at the Secret Shop Forge."""
    user_id = user.id if user else 1
    item_uid = payload.get("item_uid", "")

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg, item = await upgrade_item_forge(session, char, item_uid)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "item": item,
        "profile": serialize_character_profile(char, user_name=user_name)
    }


@rpg_router.post("/inventory/sell")
async def sell_item_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Sells a Dota item for gold."""
    user_id = user.id if user else 1
    item_uid = payload.get("item_uid", "")

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg, gold = await sell_item_from_inventory(session, char, item_uid)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "gold_earned": gold,
        "profile": serialize_character_profile(char, user_name=user_name)
    }


@rpg_router.post("/inventory/sell_multiple")
async def sell_multiple_items_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Sells multiple Dota items from inventory at once for gold."""
    user_id = user.id if user else 1
    item_uids = payload.get("item_uids", [])
    if not isinstance(item_uids, list):
        item_uids = [item_uids] if item_uids else []

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg, gold, count = await sell_multiple_items_from_inventory(session, char, item_uids)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "gold_earned": gold,
        "items_sold": count,
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


@rpg_router.post("/inventory/unequip")
async def unequip_item_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Unequips a Dota item from equipment back into inventory."""
    user_id = user.id if user else 1
    slot_or_uid = payload.get("slot") or payload.get("item_uid") or ""

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg = await unequip_item_from_character(session, char, slot_or_uid)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "profile": serialize_character_profile(char, user_name=user_name)
    }


@rpg_router.post("/inventory/use")
async def use_consumable_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Uses a potion or consumable directly from inventory."""
    user_id = user.id if user else 1
    item_uid = payload.get("item_uid", "")

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg, res_info = await use_consumable_item(session, char, item_uid)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "potion_result": res_info,
        "profile": serialize_character_profile(char, user_name=user_name)
    }


@rpg_router.get("/shop")
async def get_shop_catalog_endpoint():
    """Returns catalog of items available for purchase in Secret Shop."""
    return get_rpg_shop_catalog()


@rpg_router.post("/shop/buy")
async def buy_shop_item_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Buys an item or potion from Secret Shop."""
    user_id = user.id if user else 1
    item_id = payload.get("item_id", "")

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg, item = await buy_item_from_shop(session, char, item_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    user_name = user.display_name if user else "Дотер 11 «Б»"
    return {
        "success": True,
        "message": msg,
        "item": item,
        "profile": serialize_character_profile(char, user_name=user_name)
    }
