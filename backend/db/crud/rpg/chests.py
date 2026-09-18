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
    char_floor = getattr(char, "dungeon_floor", 1) or 1
    floor_mult = 1.0 + (char_floor - 1) * 0.08
    if wave >= 40:
        tier = "mythic"
        chest_name = "Мифический Сундук Владыки"
        chest_icon = "👑"
        gold_reward = int((400 + wave * 8) * floor_mult) + random.randint(30, 80)
        gems_reward = min(25, 10 + char_floor // 3)
        allowed_rarities = ["epic", "legendary", "immortal"]
    elif wave >= 20:
        tier = "gold"
        chest_name = "Золотой Сундук Катакомб"
        chest_icon = "🎁"
        gold_reward = int((200 + wave * 5) * floor_mult) + random.randint(20, 50)
        gems_reward = min(15, 5 + char_floor // 4)
        allowed_rarities = ["rare", "epic", "legendary"]
    else:
        tier = "silver"
        chest_name = "Серебряный Сундук Награды"
        chest_icon = "📦"
        gold_reward = int((100 + wave * 3) * floor_mult) + random.randint(10, 30)
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
    if len(inv) < 200:
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

    pool = BOSS_EXCLUSIVE_DROPS.get(boss_id)
    if not pool:
        # If boss has no exclusive drops (e.g. early game bosses like golem), drop a standard wave chest but better
        return await open_wave_chest(session, char, wave=50) # wave=50 forces mythic/immortal tier
        
    item = pick_smart_loot_item(pool, hero_class=getattr(char, 'hero_class', None), owned_names=owned_names)
    item["uid"] = str(uuid.uuid4())[:8]
    item["upgrade"] = 0
    if "bonus" in item:
        item["bonus"] = dict(item["bonus"])

    RAID_CHEST_GOLD = {
        "golem": 600, "lich": 1200, "tormentor": 2000, "dragon": 3500,
        "pudge_boss": 5500, "faceless_void": 8500, "roshan": 12000,
        "tidehunter": 16000, "sf_boss": 22000, "necrophos": 30000,
        "terrorblade": 40000, "invoker_boss": 55000, "chaos_knight": 70000,
        "dark_tormentor": 90000, "storm_spirit": 115000, "doom": 145000,
        "primal_beast": 180000, "phantom_roshan": 225000, "tinker_boss": 280000,
        "enigma": 350000
    }
    base_chest_gold = RAID_CHEST_GOLD.get(boss_id, 25000)
    gold_reward = int(base_chest_gold * random.uniform(0.9, 1.15))
    gems_reward = max(10, min(65, int(base_chest_gold / 50000) + 12))

    char.gold += gold_reward
    char.gems += gems_reward

    inv = list(char.inventory or [])
    if len(inv) < 200:
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


