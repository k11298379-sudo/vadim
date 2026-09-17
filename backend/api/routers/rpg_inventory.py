from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db_session
from backend.db.models import User
from backend.api.auth import get_optional_webapp_user
from backend.db.crud.rpg import (
    get_or_create_rpg_character,
    serialize_character_profile,
    equip_item_for_character,
    unequip_item_from_character,
    use_consumable_item,
    get_rpg_shop_catalog,
    buy_item_from_shop,
    upgrade_item_forge,
    sell_item_from_inventory,
    sell_multiple_items_from_inventory,
)
from backend.api.routers.rpg import rpg_router


@rpg_router.post("/inventory/equip")
async def equip_item_endpoint(
    payload: Dict[str, Any] = Body(...),
    user: Optional[User] = Depends(get_optional_webapp_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Equips a Dota item from inventory."""
    user_id = user.id if user else 1
    item_uid = payload.get("item_uid", "")
    target_slot = payload.get("slot") or payload.get("target_slot")

    char = await get_or_create_rpg_character(session, user_id=user_id)
    ok, msg = await equip_item_for_character(session, char, item_uid, target_slot=target_slot)
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
