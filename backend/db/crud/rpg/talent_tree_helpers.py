"""
Вспомогательные структуры, константы и функции для системы дерева талантов.
Включает логику сброса старых талантов и миграции на новую систему.
"""
from typing import Dict, Any

# Стоимость узла по тиру (в очках талантов)
TIER_COST = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}

# Уровень персонажа для открытия тира
TIER_UNLOCK_LEVEL = {1: 5, 2: 10, 3: 15, 4: 20, 5: 30}

BRANCH_LABELS = {
    "atk": {"name": "Атака", "icon": "🗡️", "color": "red"},
    "tank": {"name": "Выживание", "icon": "🛡️", "color": "blue"},
    "util": {"name": "Утилита", "icon": "✨", "color": "purple"},
}


def _node(branch: str, tier: int, name: str, icon: str,
          desc: str, effect: Dict[str, Any], req: str = None) -> Dict[str, Any]:
    """Вспомогательная функция для создания узла дерева."""
    node_id = f"{branch}_{tier}"
    return {
        "id": node_id,
        "branch": branch,
        "tier": tier,
        "name": name,
        "icon": icon,
        "desc": desc,
        "effect": effect,
        "cost": TIER_COST[tier],
        "req": req or (f"{branch}_{tier - 1}" if tier > 1 else None),
        "unlock_level": TIER_UNLOCK_LEVEL[tier],
    }


def is_node_available(node: Dict[str, Any], char_level: int,
                      purchased: Dict[str, int]) -> bool:
    """Проверяет, доступен ли узел для покупки."""
    if char_level < node["unlock_level"]:
        return False
    req = node.get("req")
    if req and not purchased.get(req, 0):
        return False
    return True


def reset_old_talents_and_refund(char: Any, hero_tree_getter=None) -> bool:
    """
    Сбрасывает старые таланты Доты и старые пассивки (lifesteal/dodge/crit_mult/cooldown),
    возвращая вложенные очки и гарантируя баланс очков по уровню (1 очко за каждые 2 уровня).
    """
    talents = dict(getattr(char, "talents", {}) or {})
    modified = False

    # 1. Возврат очков за старые 4 пассивки
    old_passives = ["lifesteal", "dodge", "crit_mult", "cooldown"]
    refunded_pts = 0
    for key in old_passives:
        if key in talents:
            lvl = int(talents.pop(key, 0) or 0)
            if lvl > 0:
                refunded_pts += lvl
            modified = True

    # 2. Удаление старых дота-талантов
    if "dota_talents" in talents:
        talents.pop("dota_talents", None)
        modified = True

    # 3. Пересчёт очков талантов по уровню персонажа
    char_level = getattr(char, "level", 1) or 1
    min_pts_from_level = char_level // 2

    # Подсчитываем, сколько уже потрачено в новом дереве
    tree_data = talents.get("tree", {})
    tree_spent = 0
    if hero_tree_getter:
        for h_class, h_nodes in tree_data.items():
            h_tree = hero_tree_getter(h_class)
            for nid, nlvl in (h_nodes or {}).items():
                if nlvl and nid in h_tree:
                    tree_spent += h_tree[nid].get("cost", 1)

    current_pts = getattr(char, "talent_points", 0) or 0
    target_pts = max(current_pts + refunded_pts, min_pts_from_level - tree_spent)
    if target_pts != current_pts:
        char.talent_points = target_pts
        modified = True

    if not talents.get("_talents_v2_migrated"):
        talents["_talents_v2_migrated"] = True
        modified = True

    if modified:
        char.talents = talents

    return modified
