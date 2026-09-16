import random
import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from backend.db.models import RPGCharacter, User
from backend.db.crud.rpg.heroes import NATAR_HEROES
from backend.db.crud.rpg.items_catalog import RARITY_MULTIPLIERS

# ==============================================================================
# CHARACTER CALCULATIONS & CRUDS
# ==============================================================================



# ==============================================================================
# CHARACTER CALCULATIONS & CRUDS
# ==============================================================================

async def get_or_create_rpg_character(
    session: AsyncSession,
    user_id: int,
    preferred_class: str = "pudge"
) -> RPGCharacter:
    """Gets existing character or creates a new one with chosen hero archetype."""
    user_check = await session.execute(select(User).where(User.id == user_id))
    user_record = user_check.scalar_one_or_none()
    if not user_record:
        fallback_tg = 999990000 + user_id
        tg_check = await session.execute(select(User).where(User.tg_id == fallback_tg))
        user_record = tg_check.scalar_one_or_none()
        if not user_record:
            user_record = User(tg_id=fallback_tg, full_name="Герой natarGRP", role="student")
            session.add(user_record)
            await session.commit()
            await session.refresh(user_record)
        user_id = user_record.id

    res = await session.execute(select(RPGCharacter).where(RPGCharacter.user_id == user_id))
    char = res.scalar_one_or_none()

    if not char:
        hero_cfg = NATAR_HEROES.get(preferred_class, NATAR_HEROES["pudge"])
        starter_weapon = dict(hero_cfg["starter_weapon"])
        starter_weapon["uid"] = str(uuid.uuid4())[:8]
        starter_armor = dict(hero_cfg["starter_armor"])
        starter_armor["uid"] = str(uuid.uuid4())[:8]

        starter_potion = {
            "uid": str(uuid.uuid4())[:8],
            "name": "Зелье Исцеления",
            "type": "potion",
            "slot": "consumable",
            "slot_name": "Зелье",
            "slot_icon": "🧪",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🧴",
            "heal_amount": 120,
            "count": 3,
            "bonus_desc": "❤️ Восстанавливает 120 HP (3 шт.)"
        }

        starter_relic = {
            "uid": str(uuid.uuid4())[:8],
            "name": "Талисман Энергии",
            "type": "relic",
            "slot": "relic",
            "slot_name": "Реликвия",
            "slot_icon": "💍",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🌿",
            "upgrade": 0,
            "bonus": {"hp": 50, "mp": 40},
            "bonus_desc": "❤️ +50 HP | 🔮 +40 MP"
        }

        char = RPGCharacter(
            user_id=user_id,
            hero_class=preferred_class,
            level=1,
            xp=0,
            gold=250,
            gems=20,
            strength=hero_cfg["str"],
            agility=hero_cfg["agi"],
            intelligence=hero_cfg["int"],
            vitality=hero_cfg["str"],
            stat_points=2,
            equipment={
                "weapon": starter_weapon,
                "armor": starter_armor,
                "relic": starter_relic
            },
            inventory=[starter_potion],
            dungeon_floor=1,
            dungeon_cleared=0,
            pvp_rating=1000,
            pvp_wins=0,
            pvp_losses=0,
            boss_kills=0
        )
        session.add(char)
        await session.commit()
        await session.refresh(char)

    return char


def calculate_character_effective_stats(char: RPGCharacter) -> Dict[str, Any]:
    """
    Calculates final attributes, ATK, DEF, HP, MP using the 3-attribute system:
      - Сила (Strength): +22 HP за очко, +0.35 HP/сек регенерация
      - Ловкость (Agility): +0.025 скорости атаки, +0.4 брони, криты, уклонение
      - Интеллект (Intelligence): +14 маны за очко, +0.25 MP/сек регенерация, +0.4% сопр. магии
      - Основной атрибут героя (Primary Attr): +1 к базовому урону атаки за каждое очко!
    """
    h_class = str(getattr(char, "hero_class", "pudge") or "pudge").strip().lower()
    LEGACY_MAP = {
        "warrior": "juggernaut",
        "knight": "pudge",
        "paladin": "wraith_king",
        "archer": "phantom_assassin",
        "rogue": "phantom_assassin",
        "assassin": "phantom_assassin",
        "mage": "invoker",
        "wizard": "invoker"
    }
    canonical_class = LEGACY_MAP.get(h_class, h_class)
    cfg = NATAR_HEROES.get(canonical_class, NATAR_HEROES["pudge"])

    # Base attributes from character allocation
    str_val = int(char.strength)
    agi_val = int(char.agility)
    int_val = int(char.intelligence)

    # Equipment slots (supports both legacy weapon/armor/relic and generic slot_1..slot_6)
    eq = char.equipment or {}
    equipped_items = [it for it in eq.values() if it and isinstance(it, dict)]

    # Accumulate all equipment bonuses
    gear_str = 0
    gear_agi = 0
    gear_int = 0
    ult_boost = 0
    ult_cd_reduct = 0
    flat_spell_amp = 0
    flat_hp = 0
    flat_mp = 0
    flat_atk = 0
    flat_def = 0
    flat_atk_speed = 0.0
    crit_chance = 0
    dodge_chance = 0
    lifesteal = 0
    magic_res = 0
    damage_block = 0
    reflect = 0
    flat_hp_regen = 0.0
    flat_mp_regen = 0.0
    w_min = 8
    w_max = 14
    has_custom_weapon = False

    for slot_item in equipped_items:
        sb = slot_item.get("bonus", {})
        all_s = sb.get("all_stats", 0)
        gear_str += sb.get("str", 0) + all_s
        gear_agi += sb.get("agi", 0) + all_s
        gear_int += sb.get("int", 0) + all_s

        ult_boost += sb.get("ult_boost", 0)
        ult_cd_reduct += sb.get("ult_cd", 0) + sb.get("cooldown_reduct", 0)
        flat_spell_amp += sb.get("spell_amp", 0)
        flat_hp += sb.get("hp", 0)
        flat_mp += sb.get("mp", 0)
        flat_atk += sb.get("atk", 0)
        flat_def += sb.get("defense", 0) + sb.get("def", 0) + sb.get("aura_armor", 0) + sb.get("armor_aura", 0)
        flat_atk_speed += (sb.get("atk_speed", 0) * 0.01) + (sb.get("speed", 0) * 0.01)
        crit_chance += sb.get("crit", 0) + sb.get("crit_chance", 0)
        dodge_chance += sb.get("dodge", 0)
        lifesteal += sb.get("lifesteal", 0)
        magic_res += sb.get("magic_resist", 0)
        damage_block += sb.get("damage_block", 0) + sb.get("block", 0)
        reflect += sb.get("reflect", 0)
        flat_hp_regen += sb.get("hp_regen", 0)
        flat_mp_regen += sb.get("mp_regen", 0)

        # Inherent item defense / hp / attack stats
        item_type = slot_item.get("type") or slot_item.get("slot")
        if item_type == "weapon" or "min_atk" in slot_item:
            if not has_custom_weapon:
                w_min = slot_item.get("min_atk") or slot_item.get("base_min") or 8
                w_max = slot_item.get("max_atk") or slot_item.get("base_max") or 14
                has_custom_weapon = True
            else:
                w_min += slot_item.get("min_atk") or slot_item.get("base_min") or 0
                w_max += slot_item.get("max_atk") or slot_item.get("base_max") or 0

        if item_type == "armor" or "defense" in slot_item:
            flat_def += slot_item.get("defense") or slot_item.get("base_def") or slot_item.get("def") or 0
            flat_hp += slot_item.get("hp_bonus") or slot_item.get("base_hp") or 0


    if canonical_class == "wraith_king":
        lifesteal += 15
    if canonical_class == "pudge":
        flat_hp_regen += 2.5
    total_str = str_val + gear_str
    total_agi = agi_val + gear_agi
    total_int = int_val + gear_int

    # Attributes scaling
    stat_hp = cfg.get("base_hp", 160) + int(total_str * 22) + flat_hp
    stat_hp_regen = round((total_str * 0.35) + flat_hp_regen, 1)

    stat_atk_speed = round(1.0 + (total_agi * 0.025) + flat_atk_speed, 2)
    stat_def = int(total_agi * 0.4) + flat_def
    crit_chance = min(85, 5 + int(total_agi * 0.4) + crit_chance)
    dodge_chance = min(60, int(total_agi * 0.3) + dodge_chance)

    stat_mp = cfg.get("base_mp", 60) + int(total_int * 14) + flat_mp
    stat_mp_regen = round((total_int * 0.25) + flat_mp_regen, 1)
    magic_res = min(80, int(total_int * 0.35) + magic_res)

    # Primary attribute attack bonus
    if cfg["attr"] == "Сила":
        primary_bonus = total_str * 1.0
    elif cfg["attr"] == "Ловкость":
        primary_bonus = total_agi * 1.0
    else: # Интеллект
        primary_bonus = total_int * 1.0

    stat_atk = int(primary_bonus + 10) + flat_atk
    total_min_atk = stat_atk + w_min
    total_max_atk = stat_atk + w_max

    # Spell Amplification: MP pool (+0.2% per point) + flat gear spell amp
    spell_amp = round(stat_mp * 0.2 + flat_spell_amp, 1)

    gear_score = int(
        (total_min_atk + total_max_atk) * 1.5
        + stat_def * 3.0
        + stat_hp * 0.35
        + stat_mp * 0.3
        + crit_chance * 3.0
        + int(stat_atk_speed * 40)
    )

    is_mage = canonical_class in ("invoker", "mage", "wizard")
    damage_type = "magical" if is_mage else "physical"

    # Endgame RPG multipliers
    rebirths = getattr(char, "rebirths", 0)
    rebirth_mult = 1.0 + (rebirths * 0.1)
    
    talents = getattr(char, "talents", {})
    talent_lifesteal = talents.get("lifesteal", 0) * 2
    talent_dodge = talents.get("dodge", 0) * 4

    # Apply rebirth multiplier to core stats
    stat_hp = int(stat_hp * rebirth_mult)
    total_min_atk = int(total_min_atk * rebirth_mult)
    total_max_atk = int(total_max_atk * rebirth_mult)

    return {
        "hp_max": stat_hp,
        "mp_max": stat_mp,
        "hp_regen": stat_hp_regen,
        "mp_regen": stat_mp_regen,
        "min_atk": total_min_atk,
        "max_atk": total_max_atk,
        "defense": stat_def,
        "attack_speed": stat_atk_speed,
        "magic_resist": magic_res,
        "crit_chance": crit_chance,
        "dodge_chance": dodge_chance + talent_dodge,
        "lifesteal": min(60, lifesteal + talent_lifesteal),
        "damage_block": damage_block,
        "reflect": min(100, reflect),
        "gear_score": gear_score,
        "primary_attr": cfg.get("attr", "Сила"),
        "primary_damage_bonus": int(primary_bonus),
        "spell_amp": spell_amp,
        "ult_boost": ult_boost,
        "ult_cd_reduct": min(60, ult_cd_reduct),
        "damage_type": damage_type,
        "skill": cfg.get("skill", {"name": "Навык", "icon": "⚡", "mp_cost": 20, "desc": "Навык героя"}),
        "base_strength": str_val,
        "base_agility": agi_val,
        "base_intelligence": int_val,
        "gear_strength": gear_str,
        "gear_agility": gear_agi,
        "gear_intelligence": gear_int,
        "total_strength": total_str,
        "total_agility": total_agi,
        "total_intelligence": total_int
    }


def serialize_character_profile(char: RPGCharacter, user_name: str = "") -> Dict[str, Any]:
    """Serializes character data for API response."""
    stats = calculate_character_effective_stats(char)
    h_class = str(getattr(char, "hero_class", "pudge") or "pudge").strip().lower()
    LEGACY_MAP = {
        "warrior": "juggernaut",
        "knight": "pudge",
        "paladin": "wraith_king",
        "archer": "phantom_assassin",
        "rogue": "phantom_assassin",
        "assassin": "phantom_assassin",
        "mage": "invoker",
        "wizard": "invoker"
    }
    canonical_class = LEGACY_MAP.get(h_class, h_class)
    cfg = NATAR_HEROES.get(canonical_class, NATAR_HEROES["pudge"])
    xp_needed = 120 + (char.level - 1) * 160

    return {
        "id": char.id,
        "user_id": char.user_id,
        "user_name": user_name,
        "hero_class": canonical_class,
        "class_name": cfg["name"],
        "class_icon": cfg["icon"],
        "class_avatar": cfg.get("avatar", "🗡️"),
        "primary_attr": cfg["attr"],
        "level": char.level,
        "xp": char.xp,
        "xp_needed": xp_needed,
        "experience": char.xp,
        "experience_to_next": xp_needed,
        "gold": char.gold,
        "gems": char.gems,
        "stat_points": getattr(char, "stat_points", 0),
        "rebirths": getattr(char, "rebirths", 0),
        "talent_points": getattr(char, "talent_points", 0),
        "talents": getattr(char, "talents", {}),
        "strength": stats["total_strength"],
        "agility": stats["total_agility"],
        "intelligence": stats["total_intelligence"],
        "vitality": stats["total_strength"],
        "base_attributes": {
            "strength": char.strength,
            "agility": char.agility,
            "intelligence": char.intelligence,
            "vitality": char.strength
        },
        "gear_attributes": {
            "strength": stats["gear_strength"],
            "agility": stats["gear_agility"],
            "intelligence": stats["gear_intelligence"]
        },
        "total_attributes": {
            "strength": stats["total_strength"],
            "agility": stats["total_agility"],
            "intelligence": stats["total_intelligence"]
        },
        "stats": stats,
        "equipment": char.equipment,
        "inventory": char.inventory,
        "dungeon_floor": char.dungeon_floor,
        "dungeon_cleared": char.dungeon_cleared,
        "pvp_rating": char.pvp_rating,
        "pvp_wins": char.pvp_wins,
        "pvp_losses": char.pvp_losses,
        "boss_kills": char.boss_kills
    }


