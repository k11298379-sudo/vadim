import random
import uuid
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from backend.db.models import RPGCharacter
from backend.db.crud.rpg.loot import rebuild_item_description
from backend.db.crud.rpg.items_catalog import RARITY_MULTIPLIERS
from backend.db.crud.rpg.character import get_or_create_rpg_character, serialize_character_profile
from backend.db.crud.rpg.heroes import NATAR_HEROES

from backend.db.crud.rpg.inventory_sell import sell_item_from_inventory, sell_multiple_items_from_inventory, reset_rpg_character

async def equip_item_for_character(
    session: AsyncSession,
    char: RPGCharacter,
    item_uid: str,
    target_slot: Optional[str] = None
) -> Tuple[bool, str]:
    """Equips an item from inventory to character slot (1 of 6)."""
    inventory = list(char.inventory or [])
    target_idx = None
    for idx, it in enumerate(inventory):
        if it.get("uid") == item_uid or (not it.get("uid") and str(it.get("id")) == str(item_uid)):
            target_idx = idx
            break

    if target_idx is None:
        return False, "Предмет не найден в инвентаре."

    item = inventory.pop(target_idx)
    if not item.get("uid"):
        import uuid
        item["uid"] = str(uuid.uuid4())[:8]

    # Only equippable items (not potions)
    t = (item.get("type") or item.get("slot") or "").lower()
    if t in ["potion", "consumable"]:
        inventory.append(item)
        return False, "Этот предмет нельзя надеть в слот снаряжения."

    equipment = dict(char.equipment or {})
    slots = ["slot_1", "slot_2", "slot_3", "slot_4", "slot_5", "slot_6"]

    slot_to_use = None
    if target_slot and str(target_slot).strip():
        s_clean = str(target_slot).strip().lower()
        if s_clean in slots or s_clean in ["weapon", "armor", "relic"]:
            slot_to_use = s_clean

    # Try to find empty slot among slot_1..slot_6
    if not slot_to_use:
        for s in slots:
            if s not in equipment or not equipment[s]:
                slot_to_use = s
                break

    # If all slots are occupied and no slot specified, replace slot_1 (or first occupied slot)
    if not slot_to_use:
        for s in slots:
            if s in equipment and equipment[s]:
                slot_to_use = s
                break
        if not slot_to_use:
            slot_to_use = "slot_1"

    old_equipped = equipment.get(slot_to_use)
    if old_equipped:
        inventory.append(old_equipped)

    item["slot"] = slot_to_use
    equipment[slot_to_use] = item

    char.equipment = equipment
    char.inventory = inventory
    flag_modified(char, "equipment")
    flag_modified(char, "inventory")
    await session.commit()
    await session.refresh(char)
    return True, f"Предмет «{item.get('name', 'Снаряжение')}» успешно надет!"


async def unequip_item_from_character(
    session: AsyncSession,
    char: RPGCharacter,
    slot_or_uid: str
) -> Tuple[bool, str]:
    """Unequips an item from character equipment slot back into inventory."""
    inventory = list(char.inventory or [])
    if len(inventory) >= 200:
        return False, "Инвентарь полон (максимум 200 слотов). Освободите место перед снятием!"

    equipment = dict(char.equipment or {})
    target_slot = None
    cleaned = (slot_or_uid or "").strip().lower()

    # 1. Direct slot key match (e.g. "slot_1", "slot_2", "weapon", "armor", "relic")
    if cleaned in equipment and equipment[cleaned]:
        target_slot = cleaned
    else:
        # 2. Match by item UID or ID across all keys
        for s, eq_item in list(equipment.items()):
            if eq_item and isinstance(eq_item, dict):
                if str(eq_item.get("uid")) == str(slot_or_uid) or str(eq_item.get("id")) == str(slot_or_uid):
                    target_slot = s
                    break

        # 3. Fallback: match by type or slot name
        if not target_slot and cleaned:
            for s, eq_item in list(equipment.items()):
                if eq_item and isinstance(eq_item, dict):
                    if str(eq_item.get("type", "")).lower() == cleaned or str(eq_item.get("slot", "")).lower() == cleaned:
                        target_slot = s
                        break

    if not target_slot or not equipment.get(target_slot):
        return False, "В этом слоте нет надетого предмета."

    item = equipment.pop(target_slot)
    inventory.append(item)

    char.equipment = equipment
    char.inventory = inventory
    flag_modified(char, "equipment")
    flag_modified(char, "inventory")
    await session.commit()
    await session.refresh(char)
    return True, f"Предмет «{item.get('name', 'Снаряжение')}» успешно снят в инвентарь!"


async def use_consumable_item(
    session: AsyncSession,
    char: RPGCharacter,
    item_uid: str
) -> Tuple[bool, str, Dict[str, Any]]:
    """Uses a potion or consumable directly from inventory."""
    inventory = list(char.inventory or [])
    target_idx = None
    for idx, it in enumerate(inventory):
        if it.get("uid") == item_uid and (it.get("slot") == "consumable" or it.get("type") == "potion"):
            target_idx = idx
            break

    if target_idx is None:
        return False, "Зелье не найдено в инвентаре.", {}

    item = dict(inventory[target_idx])
    heal_hp = item.get("heal_amount", 0)
    heal_mp = item.get("mp_amount", 0)

    count = item.get("count", 1) - 1
    if count <= 0:
        inventory.pop(target_idx)
    else:
        item["count"] = count
        item["bonus_desc"] = f"Восстанавливает {heal_hp or heal_mp} (осталось {count} шт.)"
        inventory[target_idx] = item

    char.inventory = inventory
    flag_modified(char, "inventory")
    await session.commit()
    await session.refresh(char)

    res_info = {
        "heal_hp": heal_hp,
        "heal_mp": heal_mp,
        "item_name": item.get("name", "Зелье"),
        "remaining_count": max(0, count)
    }
    msg_parts = []
    if heal_hp > 0:
        msg_parts.append(f"+{heal_hp} HP ❤️")
    if heal_mp > 0:
        msg_parts.append(f"+{heal_mp} MP 🔮")
    msg = f"Использовано «{item.get('name', 'Зелье')}» ({' | '.join(msg_parts)})!"
    return True, msg, res_info


async def upgrade_item_forge(
    session: AsyncSession,
    char: RPGCharacter,
    item_uid: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Upgrades item level (+1..+100) at the Forge."""
    target_item = None
    is_equipped = False
    slot_name = None

    equipment = dict(char.equipment or {})
    for s in ["slot_1", "slot_2", "slot_3", "slot_4", "slot_5", "slot_6"]:
        if equipment.get(s) and equipment[s].get("uid") == item_uid:
            target_item = dict(equipment[s])
            is_equipped = True
            slot_name = s
            break

    inventory = list(char.inventory or [])
    if not target_item:
        for it in inventory:
            if it.get("uid") == item_uid:
                target_item = dict(it)
                break

    if not target_item:
        return False, "Предмет для заточки не найден.", None

    current_upg = target_item.get("upgrade", 0)
    cost = int(60 * (1.25 ** current_upg))
    if char.gold < cost:
        return False, f"Не хватает золота! Заточка до +{current_upg + 1} стоит {cost} 🪙 (у вас {char.gold} 🪙).", None

    char.gold -= cost
    new_upg = current_upg + 1
    target_item["upgrade"] = new_upg
    target_item["forge_level"] = new_upg

    # 1. Weapon damage
    if target_item.get("slot") == "weapon" or target_item.get("type") == "weapon" or "min_atk" in target_item or "base_min" in target_item:
        cur_min = target_item.get("min_atk") or target_item.get("base_min") or 8
        cur_max = target_item.get("max_atk") or target_item.get("base_max") or 14
        target_item["min_atk"] = int(cur_min * 1.15) + 3
        target_item["base_min"] = target_item["min_atk"]
        target_item["max_atk"] = max(target_item["min_atk"] + 4, int(cur_max * 1.15) + 5)
        target_item["base_max"] = target_item["max_atk"]

    # 2. Armor defense & HP
    if target_item.get("slot") == "armor" or target_item.get("type") == "armor" or "defense" in target_item or "base_def" in target_item or "def" in target_item:
        cur_def = target_item.get("defense") or target_item.get("base_def") or target_item.get("def") or 4
        cur_hp = target_item.get("hp_bonus") or target_item.get("base_hp") or 20
        target_item["defense"] = int(cur_def * 1.15) + 2
        target_item["base_def"] = target_item["defense"]
        if "def" in target_item:
            target_item["def"] = target_item["defense"]
        target_item["hp_bonus"] = int(cur_hp * 1.15) + 25
        target_item["base_hp"] = target_item["hp_bonus"]

    # 3. Bonus attributes and stats
    if "bonus" in target_item and isinstance(target_item["bonus"], dict):
        bonus = dict(target_item["bonus"])
        for k, v in bonus.items():
            if isinstance(v, (int, float)) and v > 0:
                if k in ["str", "agi", "int", "atk", "all_stats"]:
                    bonus[k] = int(v * 1.15) + 2
                elif k in ["hp", "mp"]:
                    bonus[k] = int(v * 1.15) + 15
                elif k in ["hp_regen", "mp_regen", "aura_armor", "armor_aura", "block", "damage_block", "armor_pierce"]:
                    bonus[k] = int(v * 1.15) + 1
                elif k in ["crit", "dodge", "lifesteal", "atk_speed"]:
                    bonus[k] = min(65, int(v * 1.1) + 1)
                elif k in ["ult_boost"]:
                    bonus[k] = min(250, int(v * 1.06) + 2)
                elif k in ["ult_cd", "cooldown_reduct"]:
                    bonus[k] = min(60, int(v * 1.05) + 1)
                elif k in ["spell_amp"]:
                    bonus[k] = min(75, int(v * 1.1) + 1)
                elif k in ["lightning", "chain_lightning", "burst_magic", "cleave", "reflect", "meteor", "magic_dmg", "burn_aura"]:
                    bonus[k] = int(v * 1.15) + 3
        target_item["bonus"] = bonus

    target_item["bonus_desc"] = rebuild_item_description(target_item)

    if is_equipped and slot_name:
        equipment[slot_name] = target_item
        char.equipment = dict(equipment)
        flag_modified(char, "equipment")
    else:
        for idx, it in enumerate(inventory):
            if it.get("uid") == item_uid:
                inventory[idx] = target_item
                break
        char.inventory = list(inventory)
        flag_modified(char, "inventory")

    await session.commit()
    await session.refresh(char)
    return True, f"Заточка успешна! «{target_item['name']}» теперь +{new_upg} ⚔️", target_item


