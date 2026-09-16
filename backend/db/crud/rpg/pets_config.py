from typing import Dict, Any

# Pets Configuration (Roblox Simulator Style)
PETS_CATALOG: Dict[str, Dict[str, Any]] = {
    "fairy": {
        "id": "fairy",
        "name": "Лесная Фея",
        "icon": "🧚",
        "rarity": "rare",
        "base_hp_mult": 1.15,
        "base_gold_mult": 1.05,
        "base_dmg_mult": 1.0,
        "base_xp_mult": 1.10,
        "stars_scaling": 0.05,
    },
    "wolf": {
        "id": "wolf",
        "name": "Призрачный Волк",
        "icon": "🐺",
        "rarity": "epic",
        "base_hp_mult": 1.0,
        "base_gold_mult": 1.0,
        "base_dmg_mult": 1.15,
        "base_xp_mult": 1.10,
        "stars_scaling": 0.06,
    },
    "dragon": {
        "id": "dragon",
        "name": "Золотой Дракон",
        "icon": "🐉",
        "rarity": "legendary",
        "base_hp_mult": 1.10,
        "base_gold_mult": 1.25,
        "base_dmg_mult": 1.20,
        "base_xp_mult": 1.0,
        "stars_scaling": 0.08,
    },
    "phoenix": {
        "id": "phoenix",
        "name": "Феникс",
        "icon": "🦅",
        "rarity": "immortal",
        "base_hp_mult": 1.30,
        "base_gold_mult": 1.30,
        "base_dmg_mult": 1.30,
        "base_xp_mult": 1.30,
        "stars_scaling": 0.12,
    },
    "slime": {
        "id": "slime",
        "name": "Слайм",
        "icon": "💧",
        "rarity": "common",
        "base_hp_mult": 1.05,
        "base_gold_mult": 1.05,
        "base_dmg_mult": 1.05,
        "base_xp_mult": 1.05,
        "stars_scaling": 0.02,
    }
}

PET_HATCH_RATES = {
    "common": 50,
    "rare": 30,
    "epic": 14,
    "legendary": 5,
    "immortal": 1
}
