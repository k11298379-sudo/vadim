"""
Модуль дерева талантов для natarGRP RPG.
Объединяет деревья 8 героев из part1 и part2, предоставляет публичный API и функции миграции.
"""
from typing import Dict, Any
from backend.db.crud.rpg.talent_tree_helpers import (
    TIER_COST,
    TIER_UNLOCK_LEVEL,
    BRANCH_LABELS,
    is_node_available,
    reset_old_talents_and_refund,
)
from backend.db.crud.rpg.talent_tree_part1 import (
    _PUDGE,
    _JUGGERNAUT,
    _PHANTOM_ASSASSIN,
    _SHADOW_FIEND,
)
from backend.db.crud.rpg.talent_tree_part2 import (
    _INVOKER,
    _WRAITH_KING,
    _ANTI_MAGE,
    _LESHRAC,
)

# Каталог всех деревьев талантов
HERO_TALENT_TREE: Dict[str, Dict[str, Dict[str, Any]]] = {
    "pudge": _PUDGE,
    "juggernaut": _JUGGERNAUT,
    "phantom_assassin": _PHANTOM_ASSASSIN,
    "shadow_fiend": _SHADOW_FIEND,
    "invoker": _INVOKER,
    "wraith_king": _WRAITH_KING,
    "anti_mage": _ANTI_MAGE,
    "leshrac": _LESHRAC,
}


def get_hero_tree(hero_class: str) -> Dict[str, Dict[str, Any]]:
    """Возвращает дерево талантов для героя. Fallback → pudge."""
    return HERO_TALENT_TREE.get(hero_class, HERO_TALENT_TREE["pudge"])


def reset_char_talents_v2(char: Any) -> bool:
    """Обертка для сброса старых талантов с передачей get_hero_tree."""
    return reset_old_talents_and_refund(char, hero_tree_getter=get_hero_tree)


__all__ = [
    "HERO_TALENT_TREE",
    "BRANCH_LABELS",
    "TIER_UNLOCK_LEVEL",
    "TIER_COST",
    "get_hero_tree",
    "is_node_available",
    "reset_old_talents_and_refund",
    "reset_char_talents_v2",
]
