import random
import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from backend.db.models import RPGCharacter
from backend.db.crud.rpg.loot import generate_random_natar_item, pick_smart_loot_item, rebuild_item_description
from backend.db.crud.rpg.chests_drops import BOSS_EXCLUSIVE_DROPS
from backend.db.crud.rpg.items_catalog import NATAR_ITEMS_CATALOG, RARITY_MULTIPLIERS
from backend.db.crud.rpg.heroes import NATAR_HEROES

async def open_wave_chest(
    session: AsyncSession,
    char: RPGCharacter,
    wave: int
) -> Dict[str, Any]:
    """
    Opens a reward chest earned every 10-20 waves!
    Guarantees impactful functional equipment and gold/gems.
    """
    if wave >= 50:
        tier = "mythic"
        chest_name = "Мифический Сундук Владыки"
        chest_icon = "👑"
        gold_reward = 180 + random.randint(40, 80)
        gems_reward = 15
        allowed_rarities = ["epic", "legendary", "immortal"]
    elif wave >= 20:
        tier = "gold"
        chest_name = "Золотой Сундук Катакомб"
        chest_icon = "🎁"
        gold_reward = 90 + random.randint(20, 50)
        gems_reward = 8
        allowed_rarities = ["rare", "epic"]
    else:
        tier = "silver"
        chest_name = "Серебряный Сундук Награды"
        chest_icon = "📦"
        gold_reward = 45 + random.randint(10, 25)
        gems_reward = 3
        allowed_rarities = ["uncommon", "rare"]

    pool = [
        it for it in NATAR_ITEMS_CATALOG
        if it.get("rarity") in allowed_rarities and it.get("slot") in ["weapon", "armor", "relic"]
    ]
    if not pool:
        pool = NATAR_ITEMS_CATALOG

    owned_names = set()
    for it in (char.inventory or []):
        if it.get("name"):
            owned_names.add(it["name"].strip().lower())
    for slot, it in (char.equipment or {}).items():
        if isinstance(it, dict) and it.get("name"):
            owned_names.add(it["name"].strip().lower())

    item = pick_smart_loot_item(pool, hero_class=getattr(char, 'hero_class', None), owned_names=owned_names)
    item["uid"] = str(uuid.uuid4())[:8]
    item["upgrade"] = 0
    if "bonus" in item:
        item["bonus"] = dict(item["bonus"])
    rarity = item.get("rarity", "common")
    rarity_data = RARITY_MULTIPLIERS.get(rarity, RARITY_MULTIPLIERS["common"])
    item["rarity_color"] = rarity_data["color"]
    item["rarity_name"] = rarity_data["name"]
    item["bonus_desc"] = rebuild_item_description(item)

    if item.get("type") == "weapon":
        item["min_atk"] = item.get("base_min", 16)
        item["max_atk"] = item.get("base_max", 24)
    elif item.get("type") == "armor":
        item["defense"] = item.get("base_def", 8)
        item["hp_bonus"] = item.get("base_hp", 50)

    char.gold += gold_reward
    char.gems += gems_reward

    inv = list(char.inventory or [])
    if len(inv) < 30:
        inv.append(item)
        char.inventory = inv
        flag_modified(char, "inventory")

    await session.commit()
    await session.refresh(char)

    return {
        "chest_name": chest_name,
        "chest_icon": chest_icon,
        "tier": tier,
        "gold_reward": gold_reward,
        "gems_reward": gems_reward,
        "item": item
    }


async def open_boss_raid_chest(
    session: AsyncSession,
    char: RPGCharacter,
    boss_id: str = "roshan"
) -> Dict[str, Any]:
    """
    Opens an exclusive Raid Boss Treasure Chest!
    Guarantees iconic legendary artifacts from Dota 2 (Aegis, Cheese, Shard, Rapier)
    or boss trophies with massive stats and gold rewards.
    """
    boss_id = str(boss_id or "roshan").strip().lower()

    owned_names = set()
    for it in (char.inventory or []):
        if it.get("name"):
            owned_names.add(it["name"].strip().lower())
    for slot, it in (char.equipment or {}).items():
        if isinstance(it, dict) and it.get("name"):
            owned_names.add(it["name"].strip().lower())

    pool = BOSS_EXCLUSIVE_DROPS.get(boss_id) or BOSS_EXCLUSIVE_DROPS["roshan"]
    item = pick_smart_loot_item(pool, hero_class=getattr(char, 'hero_class', None), owned_names=owned_names)
    item["uid"] = str(uuid.uuid4())[:8]
    item["upgrade"] = 0
    if "bonus" in item:
        item["bonus"] = dict(item["bonus"])

    gold_reward = 220 + random.randint(50, 120)
    gems_reward = 12 + random.randint(5, 10)

    char.gold += gold_reward
    char.gems += gems_reward

    inv = list(char.inventory or [])
    if len(inv) < 30:
        inv.append(item)
        char.inventory = inv
        flag_modified(char, "inventory")

    await session.commit()
    await session.refresh(char)

    return {
        "chest_name": f"Сокровищница: {item.get('name')}",
        "chest_icon": "🏆",
        "tier": "immortal",
        "gold_reward": gold_reward,
        "gems_reward": gems_reward,
        "item": item
    }


