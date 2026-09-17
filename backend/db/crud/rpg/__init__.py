"""
natarGRP CRUD package — re-exports all public API for RPG system.
"""
from backend.db.crud.rpg.heroes import NATAR_HEROES, DOTA_HEROES, HERO_CLASSES
from backend.db.crud.rpg.items_catalog import NATAR_ITEMS_CATALOG, DOTA_ITEMS_CATALOG, RARITY_MULTIPLIERS
from backend.db.crud.rpg.creeps import NATAR_CREEPS_POOL, NATAR_FLOOR_BOSSES, DOTA_CREEPS_POOL, DOTA_FLOOR_BOSSES
from backend.db.crud.rpg.character import (
    get_or_create_rpg_character,
    calculate_character_effective_stats,
    serialize_character_profile,
)
from backend.db.crud.rpg.loot import (
    rebuild_item_description,
    generate_random_natar_item,
    generate_random_dota_item,
    pick_smart_loot_item,
)
from backend.db.crud.rpg.chests import open_wave_chest, open_boss_raid_chest
from backend.db.crud.rpg.inventory import (
    equip_item_for_character,
    unequip_item_from_character,
    use_consumable_item,
    upgrade_item_forge,
    sell_item_from_inventory,
    sell_multiple_items_from_inventory,
    reset_rpg_character,
)
from backend.db.crud.rpg.shop import (
    get_rpg_shop_catalog,
    buy_item_from_shop,
    upgrade_character_base_stat,
    add_xp_and_gold_to_character,
    get_rpg_leaderboard_data,
)
from backend.db.crud.rpg.progression_math import (
    calculate_xp_for_level,
    get_unlocked_features,
    get_full_progression_table,
    calculate_base_attribute_stats,
    LEVEL_CAP,
    STAT_POINTS_PER_LEVEL,
    PROGRESSION_MILESTONES,
)
from backend.db.crud.rpg.rebirth import (
    calculate_rebirth_multiplier,
    get_rebirth_rank_info,
    perform_ascension,
    upgrade_constellation,
    CONSTELLATIONS_CATALOG,
    REBIRTH_RANKS_CONFIG,
)
from backend.db.crud.rpg.forge_math import (
    RARITY_TIERS,
    get_forge_upgrade_requirements,
    apply_forge_upgrade_to_item,
    FORGE_MAX_LEVEL,
)
from backend.db.crud.rpg.bosses_engine import (
    BOSS_DIFFICULTIES,
    DOTA_BOSS_CATALOG,
    calculate_enrage_multiplier,
    get_boss_phase_state,
    calculate_boss_dynamic_damage,
)
from backend.db.crud.rpg.dungeon import run_dungeon_wave

__all__ = [
    "NATAR_HEROES", "DOTA_HEROES", "HERO_CLASSES",
    "NATAR_ITEMS_CATALOG", "DOTA_ITEMS_CATALOG", "RARITY_MULTIPLIERS",
    "NATAR_CREEPS_POOL", "NATAR_FLOOR_BOSSES", "DOTA_CREEPS_POOL", "DOTA_FLOOR_BOSSES",
    "get_or_create_rpg_character", "calculate_character_effective_stats", "serialize_character_profile",
    "rebuild_item_description", "generate_random_natar_item", "generate_random_dota_item", "pick_smart_loot_item",
    "open_wave_chest", "open_boss_raid_chest",
    "equip_item_for_character", "unequip_item_from_character", "use_consumable_item",
    "upgrade_item_forge", "sell_item_from_inventory", "sell_multiple_items_from_inventory", "reset_rpg_character",
    "get_rpg_shop_catalog", "buy_item_from_shop", "upgrade_character_base_stat",
    "add_xp_and_gold_to_character", "get_rpg_leaderboard_data",
    "run_dungeon_wave",
    "calculate_xp_for_level", "get_unlocked_features", "get_full_progression_table",
    "calculate_base_attribute_stats", "LEVEL_CAP", "STAT_POINTS_PER_LEVEL", "PROGRESSION_MILESTONES",
    "calculate_rebirth_multiplier", "get_rebirth_rank_info", "perform_ascension",
    "upgrade_constellation", "CONSTELLATIONS_CATALOG", "REBIRTH_RANKS_CONFIG",
    "RARITY_TIERS", "get_forge_upgrade_requirements", "apply_forge_upgrade_to_item", "FORGE_MAX_LEVEL",
    "BOSS_DIFFICULTIES", "DOTA_BOSS_CATALOG", "calculate_enrage_multiplier",
    "get_boss_phase_state", "calculate_boss_dynamic_damage",
]

