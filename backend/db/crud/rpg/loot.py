import random
import uuid
from typing import Optional, Dict, Any, List
from backend.db.crud.rpg.items_catalog import NATAR_ITEMS_CATALOG, RARITY_MULTIPLIERS
from backend.db.crud.rpg.heroes import NATAR_HEROES

# ==============================================================================
# REWARD CHEST SYSTEM & LOOT GENERATOR
# ==============================================================================

def rebuild_item_description(item: Dict[str, Any]) -> str:
    """Dynamically reconstructs readable bonus_desc with current upgraded stats."""
    parts = []
    i_type = item.get("type", "")
    bonus = item.get("bonus", {})

    if i_type == "weapon":
        w_min = item.get("min_atk") or item.get("base_min") or 8
        w_max = item.get("max_atk") or item.get("base_max") or 14
        parts.append(f"⚔️ +{w_min}..{w_max} Урон")
    elif i_type == "armor":
        a_def = item.get("defense") or item.get("base_def") or item.get("def") or 0
        a_hp = item.get("hp_bonus") or item.get("base_hp") or 0
        if a_def > 0:
            parts.append(f"🛡️ +{a_def} Броня")
        if a_hp > 0:
            parts.append(f"❤️ +{a_hp} HP")
    elif i_type == "relic":
        if bonus.get("hp"):
            parts.append(f"❤️ +{bonus['hp']} HP")
        if bonus.get("mp"):
            parts.append(f"🔮 +{bonus['mp']} MP")
        if bonus.get("atk"):
            parts.append(f"⚔️ +{bonus['atk']} Урон")

    # Extra bonus keys
    if bonus.get("all_stats"):
        parts.append(f"👑 +{bonus['all_stats']} Статы")
    if bonus.get("ult_boost"):
        parts.append(f"💥 +{bonus['ult_boost']}% Урон Ульты")
    if bonus.get("ult_cd"):
        parts.append(f"⏱️ -{bonus['ult_cd']}% КД Ульты")
    if bonus.get("spell_amp"):
        parts.append(f"🔮 +{bonus['spell_amp']}% Сила заклинаний")
    if bonus.get("str"):
        parts.append(f"🥩 +{bonus['str']} Сила")
    if bonus.get("agi"):
        parts.append(f"🏹 +{bonus['agi']} Ловкость")
    if bonus.get("int"):
        parts.append(f"🧙 +{bonus['int']} Интеллект")
    if bonus.get("crit"):
        parts.append(f"💥 +{bonus['crit']}% Крит")
    if bonus.get("dodge"):
        parts.append(f"💨 +{bonus['dodge']}% Уворот")
    if bonus.get("atk_speed"):
        parts.append(f"⚡ +{bonus['atk_speed']}% Скор. атаки")
    if bonus.get("lifesteal"):
        parts.append(f"🩸 +{bonus['lifesteal']}% Вампиризм")
    if bonus.get("hp_regen"):
        parts.append(f"🩹 +{bonus['hp_regen']} HP/сек")
    if bonus.get("mp_regen"):
        parts.append(f"⚡ +{bonus['mp_regen']} MP/сек")
    if bonus.get("magic_resist"):
        parts.append(f"🔮 +{bonus['magic_resist']}% Защита от магии")
    if bonus.get("armor_pierce"):
        parts.append(f"🩸 -{bonus['armor_pierce']} Брони врага")
    if bonus.get("cleave"):
        parts.append(f"🌪️ Сплэш {bonus['cleave']}%")
    if bonus.get("stun_chance"):
        parts.append(f"💫 {bonus['stun_chance']}% Оглушение")
    if bonus.get("lightning") or bonus.get("chain_lightning"):
        l_val = bonus.get("lightning") or bonus.get("chain_lightning")
        parts.append(f"⚡ Цепная молния {l_val}")
    if bonus.get("burst_magic"):
        parts.append(f"🔮 Взрыв {bonus['burst_magic']} ед.")
    if bonus.get("meteor"):
        parts.append(f"☄️ Метеор {bonus['meteor']}")
    if bonus.get("reflect"):
        parts.append(f"🦔 Отражает {bonus['reflect']}%")
    if bonus.get("block") or bonus.get("damage_block"):
        blk = bonus.get("block") or bonus.get("damage_block")
        parts.append(f"🛡️ Блок {blk}")
    if bonus.get("armor_aura"):
        parts.append(f"🛡️ +{bonus['armor_aura']} Аура брони")
    if bonus.get("burn_aura"):
        parts.append(f"🔥 Аура огня {bonus['burn_aura']}/с")
    if bonus.get("double_strike"):
        parts.append(f"⚔️ Двойной удар {bonus['double_strike']}%")
    if bonus.get("gold_boost"):
        parts.append(f"💰 +{bonus['gold_boost']}% Золото")
    if bonus.get("cooldown_reduct"):
        parts.append(f"⏳ -{bonus['cooldown_reduct']}% Кулдаун")
    if bonus.get("magic_dmg"):
        parts.append(f"✨ +{bonus['magic_dmg']} Маг. урон")
    if bonus.get("magic_pierce"):
        parts.append(f"🔮 -{bonus['magic_pierce']}% Маг. защиты")
    if bonus.get("mana_burn"):
        parts.append(f"💧 Сжигание маны {bonus['mana_burn']}")
    if bonus.get("creep_dmg"):
        parts.append(f"⚔️ +{bonus['creep_dmg']}% по крипам")
    if bonus.get("giant_stomp"):
        parts.append(f"💥 Удар великана {bonus['giant_stomp']}")
    if bonus.get("summon_demons"):
        parts.append("👹 Призыв демонов")
    if bonus.get("dispel"):
        parts.append("✨ Очищение")
    if bonus.get("silence"):
        parts.append("🤐 Безмолвие")
    if bonus.get("hex"):
        parts.append("🐸 Хекс")
    if bonus.get("truesight"):
        parts.append("👁️ Истинное зрение")
    if bonus.get("true_strike"):
        parts.append("🎯 Точный удар")
    if bonus.get("revive"):
        parts.append("👑 Полное воскрешение")
    if bonus.get("slow") or bonus.get("slow_aura"):
        parts.append("❄️ Замедление")
    if bonus.get("static_shield"):
        parts.append("⚡ Статический щит")

    if not parts:
        return item.get("bonus_desc", "")
    return " | ".join(parts)


# ==============================================================================
# CHARACTER CALCULATIONS & CRUDS
# ==============================================================================



def pick_smart_loot_item(pool: List[Dict[str, Any]], hero_class: str = None, owned_names: set = None) -> Dict[str, Any]:
    """Picks an item from pool with class weighting and strict anti-duplicate protection."""
    if not pool:
        return {}
    if owned_names is None:
        owned_names = set()
    else:
        owned_names = {str(n).strip().lower() for n in owned_names if n}

    h_lower = str(hero_class or "").lower()
    h_cfg = NATAR_HEROES.get(h_lower, {})
    primary_attr = h_cfg.get("attr", "")
    is_mage = (primary_attr == "Интеллект") or h_lower in ("invoker", "mage", "wizard")
    is_agi = (primary_attr == "Ловкость") or h_lower in ("phantom_assassin", "juggernaut", "anti_mage", "shadow_fiend", "archer", "rogue")
    is_str = (primary_attr == "Сила") or h_lower in ("pudge", "wraith_king", "warrior", "knight", "paladin")

    weights = []
    candidates = []
    
    # Filter candidates: if already owned, check if unique relic
    for it in pool:
        name_lower = str(it.get("name", "")).strip().lower()
        is_owned = (name_lower in owned_names) or any(name_lower in on or on in name_lower for on in owned_names)
        
        # Absolute block on duplicate unique relics (Aghanim, Shard, Aegis, Skadi) if player already has them
        is_unique_relic = any(k in name_lower for k in ("aganim", "аганим", "shard", "шард", "aegis", "эгида", "blessing", "благословение"))
        if is_owned and is_unique_relic:
            continue
            
        b = it.get("bonus", {})
        w = 1.0
        if is_mage:
            if any(k in b for k in ("int", "spell_amp", "burst_magic", "mp", "cooldown_reduct", "ult_cd")):
                w += 2.5
            if "ult_boost" in b or "all_stats" in b:
                w += 1.5
            if it.get("slot") == "weapon" and any(k in b for k in ("int", "spell_amp")):
                w += 1.5
        elif is_agi:
            if any(k in b for k in ("agi", "atk_speed", "dodge", "crit")):
                w += 2.5
            if "all_stats" in b or "lifesteal" in b:
                w += 1.5
            if it.get("slot") == "weapon" and any(k in b for k in ("agi", "atk_speed", "crit")):
                w += 1.5
        elif is_str:
            if any(k in b for k in ("str", "hp", "def", "damage_block", "reflect", "lifesteal")):
                w += 2.5
            if "all_stats" in b:
                w += 1.5
            if it.get("slot") in ("armor", "weapon") and any(k in b for k in ("str", "hp")):
                w += 1.5

        # Anti-duplicate penalty for owned equipment
        if is_owned:
            w *= 0.08

        candidates.append(it)
        weights.append(w)

    if not candidates:
        # Fallback if player literally owns everything in pool
        candidates = pool
        weights = [1.0] * len(pool)

    chosen = random.choices(candidates, weights=weights, k=1)[0]
    return dict(chosen)


def generate_random_natar_item(floor: int, quality_luck: float = 0.0, hero_class: str = None) -> Dict[str, Any]:
    """Generates a class-weighted item from the streamlined natarGRP catalog."""
    roll = random.random() + quality_luck + (floor * 0.006)

    if roll > 0.98:
        target_rarities = ["immortal", "legendary"]
    elif roll > 0.85:
        target_rarities = ["legendary", "epic"]
    elif roll > 0.55:
        target_rarities = ["epic", "rare"]
    elif roll > 0.25:
        target_rarities = ["rare", "common", "uncommon"]
    else:
        target_rarities = ["common", "uncommon"]

    filtered_catalog = [it for it in NATAR_ITEMS_CATALOG if it.get("rarity") in target_rarities]
    if not filtered_catalog:
        filtered_catalog = NATAR_ITEMS_CATALOG

    chosen = pick_smart_loot_item(filtered_catalog, hero_class=hero_class)
    chosen["uid"] = str(uuid.uuid4())[:8]
    if "bonus" in chosen:
        chosen["bonus"] = dict(chosen["bonus"])

    rarity = chosen.get("rarity", "common")
    rarity_data = RARITY_MULTIPLIERS.get(rarity, RARITY_MULTIPLIERS["common"])
    chosen["rarity_color"] = rarity_data["color"]
    chosen["rarity_name"] = rarity_data["name"]

    floor_scale = 1.0 + (floor * 0.08)

    if chosen.get("type") == "weapon":
        chosen["upgrade"] = 0
        chosen["min_atk"] = max(8, int(chosen.get("base_min", 16) * floor_scale))
        chosen["max_atk"] = max(chosen["min_atk"] + 5, int(chosen.get("base_max", 24) * floor_scale))
    elif chosen.get("type") == "armor":
        chosen["upgrade"] = 0
        chosen["defense"] = max(4, int(chosen.get("base_def", 8) * floor_scale))
        chosen["hp_bonus"] = max(20, int(chosen.get("base_hp", 50) * floor_scale))
    elif chosen.get("type") == "relic":
        chosen["upgrade"] = 0
    elif chosen.get("type") == "potion":
        chosen["heal_amount"] = int(chosen.get("heal_amount", 60) * floor_scale)

    chosen["bonus_desc"] = rebuild_item_description(chosen)
    return chosen


# Backwards compatibility aliases
generate_random_item = generate_random_natar_item
generate_random_dota_item = generate_random_natar_item



# Backwards compatibility aliases
generate_random_item = generate_random_natar_item
generate_random_dota_item = generate_random_natar_item
