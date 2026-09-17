import math
import random
from typing import Dict, Any, Tuple, Optional

# ==============================================================================
# 7 CANONICAL RARITY TIERS (Volume V of GDD)
# ==============================================================================

RARITY_TIERS: Dict[str, Dict[str, Any]] = {
    "common": {
        "id": "common",
        "name": "Обычный",
        "color": "#94a3b8",
        "multiplier": 1.00,
        "affixes_count": 0,
        "drop_weight": 50.0,
        "sell_base": 40,
    },
    "uncommon": {
        "id": "uncommon",
        "name": "Необычный",
        "color": "#22c55e",
        "multiplier": 1.30,
        "affixes_count": 1,
        "drop_weight": 28.0,
        "sell_base": 75,
    },
    "rare": {
        "id": "rare",
        "name": "Редкий",
        "color": "#3b82f6",
        "multiplier": 1.75,
        "affixes_count": 2,
        "drop_weight": 13.5,
        "sell_base": 140,
    },
    "epic": {
        "id": "epic",
        "name": "Эпический",
        "color": "#a855f7",
        "multiplier": 2.40,
        "affixes_count": 3,
        "drop_weight": 6.0,
        "sell_base": 350,
    },
    "legendary": {
        "id": "legendary",
        "name": "Легендарный",
        "color": "#f59e0b",
        "multiplier": 3.40,
        "affixes_count": 4,
        "drop_weight": 1.9,
        "sell_base": 900,
    },
    "mythic": {
        "id": "mythic",
        "name": "Мифический",
        "color": "#ef4444",
        "multiplier": 4.80,
        "affixes_count": 5,
        "drop_weight": 0.45,
        "sell_base": 2500,
    },
    "immortal": {
        "id": "immortal",
        "name": "Бессмертный",
        "color": "#ec4899",
        "multiplier": 6.80,
        "affixes_count": 6,
        "drop_weight": 0.15,
        "sell_base": 7500,
    },
}

FORGE_MAX_LEVEL = 15


def get_forge_upgrade_requirements(current_level: int) -> Dict[str, Any]:
    """
    Returns success rate, gold and gem costs according to Volume V:
    - +1..+3: 100% success, (L+1) * 350 gold, 0 gems
    - +4..+6: 85% success, (L+1) * 800 gold, 2 gems
    - +7..+9: 65% success, (L+1) * 2000 gold, 6 gems
    - +10..+12: 45% success, (L+1) * 5500 gold, 15 gems
    - +13..+15: 25% success, (L+1) * 15000 gold, 45 gems
    """
    if current_level >= FORGE_MAX_LEVEL:
        return {
            "current_level": current_level,
            "target_level": current_level,
            "is_max": True,
            "success_rate": 0.0,
            "success_pct": 0,
            "gold_cost": 0,
            "gems_cost": 0,
            "stat_multiplier": round(1.0 + (current_level * 0.15), 3),
        }

    target_level = current_level + 1
    if target_level <= 3:
        rate = 1.00
        gold = target_level * 350
        gems = 0
    elif target_level <= 6:
        rate = 0.85
        gold = target_level * 800
        gems = 2
    elif target_level <= 9:
        rate = 0.65
        gold = target_level * 2000
        gems = 6
    elif target_level <= 12:
        rate = 0.45
        gold = target_level * 5500
        gems = 15
    else:  # 13..15
        rate = 0.25
        gold = target_level * 15000
        gems = 45

    return {
        "current_level": current_level,
        "target_level": target_level,
        "is_max": False,
        "success_rate": rate,
        "success_pct": int(rate * 100),
        "gold_cost": gold,
        "gems_cost": gems,
        "stat_multiplier": round(1.0 + (target_level * 0.15), 3),
        "current_multiplier": round(1.0 + (current_level * 0.15), 3),
    }


def apply_forge_upgrade_to_item(item: Dict[str, Any], target_level: int) -> Dict[str, Any]:
    """
    Recalculates item stats for target_level (+1..+15):
    Stat_final = Stat_base * (1 + Level * 0.15) * M_rarity
    """
    from backend.db.crud.rpg.loot import rebuild_item_description

    item["upgrade"] = target_level
    item["forge_level"] = target_level
    growth_mult = 1.0 + (target_level * 0.15)

    # 1. Base Weapon Attack
    if "base_min" not in item and "min_atk" in item:
        cur_lvl = item.get("upgrade", 0)
        item["base_min"] = max(6, int(round(item["min_atk"] / (1.0 + cur_lvl * 0.15))))
    if "base_max" not in item and "max_atk" in item:
        cur_lvl = item.get("upgrade", 0)
        item["base_max"] = max(10, int(round(item["max_atk"] / (1.0 + cur_lvl * 0.15))))

    if "base_min" in item:
        item["min_atk"] = int(round(item["base_min"] * growth_mult))
    if "base_max" in item:
        item["max_atk"] = max(item.get("min_atk", 8) + 4, int(round(item["base_max"] * growth_mult)))

    # 2. Base Armor Defense & HP
    if "base_def" not in item and ("defense" in item or "def" in item):
        cur_d = item.get("defense", item.get("def", 4))
        cur_lvl = item.get("upgrade", 0)
        item["base_def"] = max(2, int(round(cur_d / (1.0 + cur_lvl * 0.15))))
    if "base_hp" not in item and "hp_bonus" in item:
        cur_lvl = item.get("upgrade", 0)
        item["base_hp"] = max(15, int(round(item["hp_bonus"] / (1.0 + cur_lvl * 0.15))))

    if "base_def" in item:
        new_def = int(round(item["base_def"] * growth_mult))
        item["defense"] = new_def
        if "def" in item:
            item["def"] = new_def
    if "base_hp" in item:
        item["hp_bonus"] = int(round(item["base_hp"] * growth_mult))

    # 3. Bonus Attributes
    bonus = dict(item.get("bonus", {}))
    if "base_bonus" not in item:
        item["base_bonus"] = dict(bonus)

    base_b = item["base_bonus"]
    for k, v in base_b.items():
        if isinstance(v, (int, float)) and v > 0:
            if k in ["str", "agi", "int", "atk", "all_stats"]:
                bonus[k] = int(round(v * growth_mult))
            elif k in ["hp", "mp"]:
                bonus[k] = int(round(v * growth_mult))
            elif k in ["crit", "dodge", "lifesteal", "atk_speed"]:
                bonus[k] = min(65, int(round(v * (1.0 + target_level * 0.10))))
            elif k in ["ult_boost"]:
                bonus[k] = min(250, int(round(v * (1.0 + target_level * 0.08))))
            elif k in ["ult_cd", "cooldown_reduct"]:
                bonus[k] = min(60, int(round(v * (1.0 + target_level * 0.05))))
            elif k in ["spell_amp"]:
                bonus[k] = min(75, int(round(v * (1.0 + target_level * 0.10))))
            elif k in ["lightning", "chain_lightning", "burst_magic", "cleave", "reflect", "damage_block", "block"]:
                bonus[k] = int(round(v * growth_mult))

    item["bonus"] = bonus
    item["bonus_desc"] = rebuild_item_description(item)
    return item
