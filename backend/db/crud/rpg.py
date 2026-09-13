import random
import uuid
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from backend.db.models import RPGCharacter, User

# ==============================================================================
# natarGRP HERO ARCHETYPES (ГЕРОИ natarGRP)
# ==============================================================================

NATAR_HEROES = {
    "pudge": {
        "id": "pudge",
        "name": "Потрошитель (Мясник)",
        "icon": "🪝",
        "avatar": "🥩",
        "attr": "Сила",
        "desc": "Громила с гигантским тесаком и цепью. Неудержимое здоровье и регенерация плоти.",
        "base_hp": 220,
        "base_mp": 60,
        "str": 22,
        "agi": 9,
        "int": 8,
        "starter_weapon": {
            "uid": "w_starter_pudge",
            "name": "Ржавый Крюк",
            "type": "weapon",
            "slot": "weapon",
            "slot_name": "Оружие",
            "slot_icon": "⚔️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🪝",
            "min_atk": 16,
            "max_atk": 24,
            "upgrade": 0,
            "bonus": {"str": 4},
            "bonus_desc": "⚔️ +16..24 Урон | 🥩 +4 Сила"
        },
        "starter_armor": {
            "uid": "a_starter_pudge",
            "name": "Фартук Мясника",
            "type": "armor",
            "slot": "armor",
            "slot_name": "Броня",
            "slot_icon": "🛡️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🦺",
            "defense": 8,
            "hp_bonus": 60,
            "upgrade": 0,
            "bonus": {"hp_regen": 4},
            "bonus_desc": "🛡️ +8 Броня | ❤️ +60 HP | 🩹 +4 HP/сек"
        },
        "skill": {
            "name": "Мясной Крюк & Пожирание",
            "icon": "🥩",
            "mp_cost": 25,
            "desc": "Хукает врага цепью, наносит 220% урона и восстанавливает себе 50 HP!"
        }
    },
    "juggernaut": {
        "id": "juggernaut",
        "name": "Мастер Клинка (Самурай)",
        "icon": "🗡️",
        "avatar": "👺",
        "attr": "Ловкость",
        "desc": "Непревзойденный фехтовальщик бури. Шквал смертоносных ударов и ураганная скорость атаки.",
        "base_hp": 150,
        "base_mp": 70,
        "str": 13,
        "agi": 21,
        "int": 9,
        "starter_weapon": {
            "uid": "w_starter_jug",
            "name": "Катана Бури",
            "type": "weapon",
            "slot": "weapon",
            "slot_name": "Оружие",
            "slot_icon": "⚔️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🗡️",
            "min_atk": 18,
            "max_atk": 26,
            "upgrade": 0,
            "bonus": {"crit": 15},
            "bonus_desc": "⚔️ +18..26 Урон | 💥 +15% Крит"
        },
        "starter_armor": {
            "uid": "a_starter_jug",
            "name": "Маска Предков",
            "type": "armor",
            "slot": "armor",
            "slot_name": "Броня",
            "slot_icon": "🛡️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🎭",
            "defense": 7,
            "hp_bonus": 30,
            "upgrade": 0,
            "bonus": {"dodge": 10},
            "bonus_desc": "🛡️ +7 Броня | ❤️ +30 HP | 💨 +10% Уворот"
        },
        "skill": {
            "name": "Танец Клинков (Шквал)",
            "icon": "⚡",
            "mp_cost": 25,
            "desc": "Серия из 3 молниеносных рассекающих ударов (по 130% урона с гарантированным критом)!"
        }
    },
    "phantom_assassin": {
        "id": "phantom_assassin",
        "name": "Теневой Клинок (Убийца)",
        "icon": "🩸",
        "avatar": "🥷",
        "attr": "Ловкость",
        "desc": "Бесшумная тень ночи. Мастер уклонения от ударов и сокрушительных смертельных выпадов.",
        "base_hp": 135,
        "base_mp": 65,
        "str": 11,
        "agi": 23,
        "int": 8,
        "starter_weapon": {
            "uid": "w_starter_pa",
            "name": "Кинжал Тени",
            "type": "weapon",
            "slot": "weapon",
            "slot_name": "Оружие",
            "slot_icon": "⚔️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🗡️",
            "min_atk": 17,
            "max_atk": 25,
            "upgrade": 0,
            "bonus": {"crit": 20},
            "bonus_desc": "⚔️ +17..25 Урон | 💥 +20% Крит"
        },
        "starter_armor": {
            "uid": "a_starter_pa",
            "name": "Плащ Размытия",
            "type": "armor",
            "slot": "armor",
            "slot_name": "Броня",
            "slot_icon": "🛡️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🥋",
            "defense": 6,
            "hp_bonus": 25,
            "upgrade": 0,
            "bonus": {"dodge": 20},
            "bonus_desc": "🛡️ +6 Броня | ❤️ +25 HP | 💨 +20% Уворот"
        },
        "skill": {
            "name": "Смертельный Выпад",
            "icon": "💥",
            "mp_cost": 20,
            "desc": "Сокрушительный выпад из тени с шансом 400% критического урона!"
        }
    },
    "shadow_fiend": {
        "id": "shadow_fiend",
        "name": "Жнец Душ (Владыка Теней)",
        "icon": "💀",
        "avatar": "🖤",
        "attr": "Интеллект",
        "desc": "Повелевает украденными душами поверженных врагов. Испепеляющие темные взрывы и шторм душ.",
        "base_hp": 130,
        "base_mp": 95,
        "str": 10,
        "agi": 18,
        "int": 18,
        "starter_weapon": {
            "uid": "w_starter_sf",
            "name": "Осколок Тьмы",
            "type": "weapon",
            "slot": "weapon",
            "slot_name": "Оружие",
            "slot_icon": "⚔️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🔥",
            "min_atk": 18,
            "max_atk": 27,
            "upgrade": 0,
            "bonus": {"mp": 25},
            "bonus_desc": "⚔️ +18..27 Урон | 🔮 +25 Мана"
        },
        "starter_armor": {
            "uid": "a_starter_sf",
            "name": "Мантия Теней",
            "type": "armor",
            "slot": "armor",
            "slot_name": "Броня",
            "slot_icon": "🛡️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🦹",
            "defense": 5,
            "hp_bonus": 25,
            "upgrade": 0,
            "bonus": {"mp_regen": 5},
            "bonus_desc": "🛡️ +5 Броня | ❤️ +25 HP | 🔮 +5 MP/сек"
        },
        "skill": {
            "name": "Взрыв Душ (Тройной Удар)",
            "icon": "🌑",
            "mp_cost": 25,
            "desc": "Три мощных взрыва темной энергии вокруг: суммарно 280% магического урона!"
        }
    },
    "invoker": {
        "id": "invoker",
        "name": "Архимаг Стихий (Чародей)",
        "icon": "🔮",
        "avatar": "🧙‍♂️",
        "attr": "Интеллект",
        "desc": "Верховный магистр древних стихий. Огромный запас маны, метеоритные штормы и лучи солнца.",
        "base_hp": 125,
        "base_mp": 140,
        "str": 9,
        "agi": 10,
        "int": 25,
        "starter_weapon": {
            "uid": "w_starter_inv",
            "name": "Сфера Трех Стихий",
            "type": "weapon",
            "slot": "weapon",
            "slot_name": "Оружие",
            "slot_icon": "⚔️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🔮",
            "min_atk": 17,
            "max_atk": 28,
            "upgrade": 0,
            "bonus": {"mp": 40},
            "bonus_desc": "⚔️ +17..28 Урон | 🔮 +40 Мана"
        },
        "starter_armor": {
            "uid": "a_starter_inv",
            "name": "Мантия Архимага",
            "type": "armor",
            "slot": "armor",
            "slot_name": "Броня",
            "slot_icon": "🛡️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "👘",
            "defense": 5,
            "hp_bonus": 25,
            "upgrade": 0,
            "bonus": {"int": 6},
            "bonus_desc": "🛡️ +5 Броня | ❤️ +25 HP | 🧙 +6 Интеллект"
        },
        "skill": {
            "name": "Санстрайк & Хаос Метеор",
            "icon": "☄️",
            "mp_cost": 30,
            "desc": "Солнечный луч Санстрайка с неба и пылающая «котлета» Хаос Метеора через всю арену!"
        }
    },
    "wraith_king": {
        "id": "wraith_king",
        "name": "Король Скелетов (Монарх)",
        "icon": "👑",
        "avatar": "💀",
        "attr": "Сила",
        "desc": "Древний бессмертный монарх катакомб. Сокрушительный вампиризм и несокрушимая стойкость.",
        "base_hp": 210,
        "base_mp": 55,
        "str": 21,
        "agi": 9,
        "int": 7,
        "starter_weapon": {
            "uid": "w_starter_wk",
            "name": "Меч Призрачного Монарха",
            "type": "weapon",
            "slot": "weapon",
            "slot_name": "Оружие",
            "slot_icon": "⚔️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🗡️",
            "min_atk": 16,
            "max_atk": 24,
            "upgrade": 0,
            "bonus": {"lifesteal": 12},
            "bonus_desc": "⚔️ +16..24 Урон | 🩸 +12% Вампиризм"
        },
        "starter_armor": {
            "uid": "a_starter_wk",
            "name": "Корона Костяного Царя",
            "type": "armor",
            "slot": "armor",
            "slot_name": "Броня",
            "slot_icon": "🛡️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "👑",
            "defense": 9,
            "hp_bonus": 50,
            "upgrade": 0,
            "bonus": {"hp": 30},
            "bonus_desc": "🛡️ +9 Броня | ❤️ +80 HP"
        },
        "skill": {
            "name": "Призрачный Стан & Крит",
            "icon": "💥",
            "mp_cost": 20,
            "desc": "Оглушает врага снарядом призраков и наносит 250% урона с вампиризмом!"
        }
    },
    "anti_mage": {
        "id": "anti_mage",
        "name": "Охотник на Магов (Каратель)",
        "icon": "⚔️",
        "avatar": "🧑‍🦲",
        "attr": "Ловкость",
        "desc": "Быстрый охотник на чародеев. Рассекает эфир, выжигает ману врагов и взрывает боссов.",
        "base_hp": 145,
        "base_mp": 60,
        "str": 13,
        "agi": 22,
        "int": 6,
        "starter_weapon": {
            "uid": "w_starter_am",
            "name": "Парные Клинки Охотника",
            "type": "weapon",
            "slot": "weapon",
            "slot_name": "Оружие",
            "slot_icon": "⚔️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "⚔️",
            "min_atk": 17,
            "max_atk": 25,
            "upgrade": 0,
            "bonus": {"mana_burn": 15},
            "bonus_desc": "⚔️ +17..25 Урон | ⚡ Сжигание маны"
        },
        "starter_armor": {
            "uid": "a_starter_am",
            "name": "Одеяния Монаха",
            "type": "armor",
            "slot": "armor",
            "slot_name": "Броня",
            "slot_icon": "🛡️",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "icon": "🥋",
            "defense": 7,
            "hp_bonus": 30,
            "upgrade": 0,
            "bonus": {"magic_resist": 25},
            "bonus_desc": "🛡️ +7 Броня | ❤️ +30 HP | 🔮 +25% Сопр. магии"
        },
        "skill": {
            "name": "Взрыв Пустоты (Кара)",
            "icon": "⚡",
            "mp_cost": 20,
            "desc": "Выжигает запасы маны врага и взрывает его изнутри на 260% урона!"
        }
    }
}

# 100% Backwards compatibility aliases
DOTA_HEROES = NATAR_HEROES
HERO_CLASSES = NATAR_HEROES

# ==============================================================================
# RARITY MULTIPLIERS & SETTINGS
# ==============================================================================

RARITY_MULTIPLIERS = {
    "common": {"name": "Обычный", "color": "#94a3b8", "mult": 1.0, "sell": 40},
    "uncommon": {"name": "Необычный", "color": "#22c55e", "mult": 1.25, "sell": 75},
    "rare": {"name": "Редкий", "color": "#38bdf8", "mult": 1.5, "sell": 120},
    "epic": {"name": "Эпический", "color": "#c084fc", "mult": 2.2, "sell": 320},
    "legendary": {"name": "Легендарный", "color": "#facc15", "mult": 3.4, "sell": 850},
    "immortal": {"name": "Бессмертный", "color": "#f97316", "mult": 5.0, "sell": 2500}
}

# ==============================================================================
# 28 STREAMLINED FUNCTIONAL ITEMS (natarGRP CATALOG)
# ==============================================================================

# ==============================================================================
# MASSIVE 107-ITEM DOTA 2 & HARDCORE RPG CATALOG
# ==============================================================================

NATAR_ITEMS_CATALOG = [
    # --- TIER 1: COMMON / STARTER (Levels 1 - 10) ---
    {
        "name": "Железная Ветка (Iron Branch)",
        "icon": "🌿",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "common",
        "bonus": {"str": 1, "agi": 1, "int": 1, "atk": 1},
        "bonus_desc": "🌿 +1 ко всем характеристикам | ⚔️ +1 Урон"
    },
    {
        "name": "Перчатки Силы (Gauntlets of Strength)",
        "icon": "🥊",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "common",
        "bonus": {"str": 3, "hp": 35},
        "bonus_desc": "💪 +3 Сила | ❤️ +35 HP"
    },
    {
        "name": "Тапочки Ловкости (Slippers of Agility)",
        "icon": "🥿",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "common",
        "bonus": {"agi": 3, "dodge": 1},
        "bonus_desc": "🏃 +3 Ловкость | 💨 +1% Уворот"
    },
    {
        "name": "Мантия Интеллекта (Mantle of Intelligence)",
        "icon": "📜",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "common",
        "bonus": {"int": 3, "mp": 30},
        "bonus_desc": "🔮 +3 Интеллект | 💧 +30 MP"
    },
    {
        "name": "Венец Благородства (Circlet)",
        "icon": "👑",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "common",
        "bonus": {"str": 2, "agi": 2, "int": 2},
        "bonus_desc": "✨ +2 ко всем характеристикам"
    },
    {
        "name": "Топорик Лесоруба (Quelling Blade)",
        "icon": "🪓",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "common",
        "base_min": 4,
        "base_max": 7,
        "bonus": {"creep_dmg": 4},
        "bonus_desc": "⚔️ +4..7 Урон | 🌲 +4 доп. урона по крипам"
    },
    {
        "name": "Прочный Щиток (Stout Shield)",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "common",
        "base_def": 3,
        "base_hp": 25,
        "bonus": {"block": 6},
        "bonus_desc": "🛡️ +3 Броня | 🛡️ Блокирует 6 урона"
    },
    {
        "name": "Кольцо Защиты (Ring of Protection)",
        "icon": "💍",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "common",
        "base_def": 2,
        "base_hp": 15,
        "bonus": {"def": 2},
        "bonus_desc": "🛡️ +2 Броня | ❤️ +15 HP"
    },
    {
        "name": "Волшебная Палочка (Magic Stick)",
        "icon": "🪄",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "common",
        "bonus": {"hp": 15, "mp": 20},
        "bonus_desc": "❤️ +15 HP | 💧 +20 MP"
    },
    {
        "name": "Камень Порчи (Blight Stone)",
        "icon": "🪨",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "common",
        "base_min": 3,
        "base_max": 5,
        "bonus": {"armor_pierce": 1},
        "bonus_desc": "⚔️ +3..5 Урон | 🩸 -1 Брони врага"
    },
    {
        "name": "Шнурок Ветра (Wind Lace)",
        "icon": "👟",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "common",
        "base_def": 1,
        "base_hp": 10,
        "bonus": {"dodge": 2},
        "bonus_desc": "💨 +2% Уворот | 🛡️ +1 Броня"
    },
    {
        "name": "Капли Дождя (Infused Raindrops)",
        "icon": "💧",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "common",
        "bonus": {"hp": 30, "mp_regen": 1},
        "bonus_desc": "❤️ +30 HP | 💧 +1 MP/сек"
    },
    {
        "name": "Ржавый Кинжал Новичка",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "common",
        "base_min": 5,
        "base_max": 8,
        "bonus": {"crit": 2},
        "bonus_desc": "⚔️ +5..8 Урон | 💥 +2% Крит"
    },
    {
        "name": "Тканевая Куртка Ополченца",
        "icon": "🥋",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "common",
        "base_def": 2,
        "base_hp": 25,
        "bonus": {},
        "bonus_desc": "🛡️ +2 Броня | ❤️ +25 HP"
    },
    {
        "name": "Кольцо Регенерации (Ring of Regen)",
        "icon": "💚",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "common",
        "bonus": {"hp_regen": 2},
        "bonus_desc": "💚 +2 HP в секунду"
    },
    {
        "name": "Дубовый Боевой Посох",
        "icon": "🪵",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "common",
        "base_min": 4,
        "base_max": 7,
        "bonus": {"int": 2},
        "bonus_desc": "⚔️ +4..7 Урон | 🔮 +2 Интеллект"
    },

    # --- TIER 2: UNCOMMON / EARLY GAME (Levels 10 - 30) ---
    {
        "name": "Клинки Атаки (Blades of Attack)",
        "icon": "⚔️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "uncommon",
        "base_min": 9,
        "base_max": 14,
        "bonus": {"atk": 4},
        "bonus_desc": "⚔️ +9..14 Урон | 💥 +4 Базовый урон"
    },
    {
        "name": "Кольчуга (Chainmail)",
        "icon": "🦺",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 5,
        "base_hp": 60,
        "bonus": {"def": 2},
        "bonus_desc": "🛡️ +5 Броня | ❤️ +60 HP"
    },
    {
        "name": "Шлем Железной Воли (Helm of Iron Will)",
        "icon": "🪖",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 6,
        "base_hp": 90,
        "bonus": {"hp_regen": 4},
        "bonus_desc": "🛡️ +6 Броня | 💚 +4 HP/сек | ❤️ +90 HP"
    },
    {
        "name": "Маска Смерти (Morbid Mask)",
        "icon": "🎭",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "uncommon",
        "bonus": {"lifesteal": 7},
        "bonus_desc": "🧛 +7% Вампиризм от атак"
    },
    {
        "name": "Сапоги Скорости (Boots of Speed)",
        "icon": "👢",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 3,
        "base_hp": 40,
        "bonus": {"dodge": 5},
        "bonus_desc": "💨 +5% Уворот | 🛡️ +3 Броня"
    },
    {
        "name": "Фазовые Сапоги (Phase Boots)",
        "icon": "👢",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 4,
        "base_hp": 70,
        "bonus": {"atk": 12, "dodge": 4},
        "bonus_desc": "⚔️ +12 Урон | 🛡️ +4 Броня | 💨 +4% Уворот"
    },
    {
        "name": "Сапоги Мощи (Power Treads)",
        "icon": "🥾",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 4,
        "base_hp": 95,
        "bonus": {"all_stats": 5, "atk": 8},
        "bonus_desc": "✨ +5 ко всем характеристикам | ⚔️ +8 Урон"
    },
    {
        "name": "Сфера Коррозии (Orb of Corrosion)",
        "icon": "🧪",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "uncommon",
        "base_min": 10,
        "base_max": 16,
        "bonus": {"armor_pierce": 3, "hp": 50},
        "bonus_desc": "⚔️ +10..16 Урон | 🩸 -3 Брони врага | ❤️ +50 HP"
    },
    {
        "name": "Клинок Сокола (Falcon Blade)",
        "icon": "🪶",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "uncommon",
        "base_min": 12,
        "base_max": 18,
        "bonus": {"hp": 120, "mp": 50},
        "bonus_desc": "⚔️ +12..18 Урон | ❤️ +120 HP | 💧 +50 MP"
    },
    {
        "name": "Авангард (Vanguard)",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 7,
        "base_hp": 180,
        "bonus": {"block": 18, "hp_regen": 5},
        "bonus_desc": "🛡️ +7 Броня | ❤️ +180 HP | 🛡️ Блок 18 урона | 💚 +5 HP/сек"
    },
    {
        "name": "Урна Теней (Urn of Shadows)",
        "icon": "🏺",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "uncommon",
        "bonus": {"all_stats": 2, "armor": 2, "hp_regen": 2},
        "bonus_desc": "✨ +2 Статы | 🛡️ +2 Броня | 💚 +2 HP/сек"
    },
    {
        "name": "Медальон Мужества (Medallion of Courage)",
        "icon": "🏅",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 5,
        "base_hp": 75,
        "bonus": {"armor_pierce": 3},
        "bonus_desc": "🛡️ +5 Броня | 🩸 -3 Брони врага при ударе"
    },
    {
        "name": "Корона Императора (Crown)",
        "icon": "👑",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "uncommon",
        "bonus": {"str": 4, "agi": 4, "int": 4},
        "bonus_desc": "👑 +4 ко всем характеристикам"
    },
    {
        "name": "Пояс Великана (Belt of Strength)",
        "icon": "🥋",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 3,
        "base_hp": 110,
        "bonus": {"str": 6},
        "bonus_desc": "💪 +6 Сила | ❤️ +110 HP"
    },
    {
        "name": "Сапоги Эльфийской Ловкости (Boots of Elvenskin)",
        "icon": "🥿",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 3,
        "base_hp": 40,
        "bonus": {"agi": 6, "dodge": 3},
        "bonus_desc": "🏃 +6 Ловкость | 💨 +3% Уворот"
    },
    {
        "name": "Мантия Мага (Robe of the Magi)",
        "icon": "👘",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "uncommon",
        "base_def": 3,
        "base_hp": 30,
        "bonus": {"int": 6, "mp": 60},
        "bonus_desc": "🔮 +6 Интеллект | 💧 +60 MP"
    },

    # --- TIER 3: RARE / MID GAME (Levels 30 - 60) ---
    {
        "name": "Палаш (Broadsword)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 18,
        "base_max": 28,
        "bonus": {"atk": 6},
        "bonus_desc": "⚔️ +18..28 Урон | 💥 +6 Урон"
    },
    {
        "name": "Клеймор (Claymore)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 24,
        "base_max": 36,
        "bonus": {"atk": 8},
        "bonus_desc": "⚔️ +24..36 Урон | 💥 +8 Урон"
    },
    {
        "name": "Мифриловый Молот (Mithril Hammer)",
        "icon": "🔨",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 30,
        "base_max": 44,
        "bonus": {"crit": 4},
        "bonus_desc": "⚔️ +30..44 Урон | 💥 +4% Крит"
    },
    {
        "name": "Латный Доспех (Platemail)",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "rare",
        "base_def": 11,
        "base_hp": 160,
        "bonus": {"def": 4},
        "bonus_desc": "🛡️ +11 Броня | ❤️ +160 HP"
    },
    {
        "name": "Кристалис (Crystalys)",
        "icon": "💎",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 34,
        "base_max": 48,
        "bonus": {"crit": 15},
        "bonus_desc": "⚔️ +34..48 Урон | 💥 +15% шанс Крита (x1.75)"
    },
    {
        "name": "Крушитель Черепов (Skull Basher)",
        "icon": "🔨",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 28,
        "base_max": 42,
        "bonus": {"str": 10, "stun_chance": 12},
        "bonus_desc": "⚔️ +28..42 Урон | 💪 +10 Сила | 💫 12% Шанс Оглушения"
    },
    {
        "name": "Теневой Клинок (Shadow Blade)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 32,
        "base_max": 46,
        "bonus": {"dodge": 12, "atk": 10},
        "bonus_desc": "⚔️ +32..46 Урон | 💨 +12% Уворот | 💥 +10 Урон"
    },
    {
        "name": "Яша (Yasha)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 22,
        "base_max": 34,
        "bonus": {"agi": 16, "speed": 10, "dodge": 6},
        "bonus_desc": "🏃 +16 Ловкость | ⚡ +10% Скорость атаки | 💨 +6% Уворот"
    },
    {
        "name": "Саша (Sange)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 22,
        "base_max": 34,
        "bonus": {"str": 16, "hp": 180, "lifesteal": 6},
        "bonus_desc": "💪 +16 Сила | ❤️ +180 HP | 🧛 +6% Вампиризм"
    },
    {
        "name": "Кайя (Kaya)",
        "icon": "🪄",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 20,
        "base_max": 32,
        "bonus": {"int": 16, "mp": 150, "spell_amp": 10},
        "bonus_desc": "🔮 +16 Интеллект | 💧 +150 MP | ✨ +10% Сила заклинаний"
    },
    {
        "name": "Молния (Maelstrom)",
        "icon": "⚡",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 26,
        "base_max": 40,
        "bonus": {"chain_lightning": 25},
        "bonus_desc": "⚔️ +26..40 Урон | ⚡ 25% Шанс выпустить Цепную Молнию"
    },
    {
        "name": "Клинок Очищения (Diffusal Blade)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 25,
        "base_max": 38,
        "bonus": {"agi": 15, "mana_burn": 30},
        "bonus_desc": "🏃 +15 Ловкость | 💧 Сожжение 30 маны за удар"
    },
    {
        "name": "Пика Дракона (Dragon Lance)",
        "icon": "🔱",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 24,
        "base_max": 36,
        "bonus": {"str": 12, "agi": 12, "hp": 140},
        "bonus_desc": "💪 +12 Сила | 🏃 +12 Ловкость | ❤️ +140 HP"
    },
    {
        "name": "Возвратный Доспех (Blade Mail)",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "rare",
        "base_def": 8,
        "base_hp": 130,
        "bonus": {"atk": 16, "reflect": 25},
        "bonus_desc": "🛡️ +8 Броня | ⚔️ +16 Урон | 🔄 Отражает 25% урона"
    },
    {
        "name": "Аганимный Осколок (Aghanim Shard)",
        "icon": "🔷",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "bonus": {"all_stats": 8, "ult_cd": 15},
        "bonus_desc": "👑 +8 ко всем характеристикам | ⏱️ -15% КД Ульты"
    },
    {
        "name": "Саша и Яша (Sange and Yasha)",
        "icon": "⚔️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 36,
        "base_max": 52,
        "bonus": {"str": 16, "agi": 16, "dodge": 8, "lifesteal": 6},
        "bonus_desc": "💪 +16 Сила | 🏃 +16 Ловкость | 💨 +8% Уворот | 🧛 +6% Вампиризм"
    },

    # --- TIER 4: EPIC / LATE GAME (Levels 60 - 90) ---
    {
        "name": "Боевой Топор (Battle Fury)",
        "icon": "🪓",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 60,
        "base_max": 88,
        "bonus": {"cleave": 45, "hp_regen": 8},
        "bonus_desc": "⚔️ +60..88 Урон | 💥 45% Сплэш урон вокруг | 💚 +8 HP/сек"
    },
    {
        "name": "Дедал (Daedalus)",
        "icon": "🏹",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 85,
        "base_max": 125,
        "bonus": {"crit": 30},
        "bonus_desc": "⚔️ +85..125 Урон | 💥 +30% Шанс Крита (x2.25)"
    },
    {
        "name": "Бабочка (Butterfly)",
        "icon": "🦋",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 45,
        "base_max": 68,
        "bonus": {"agi": 35, "dodge": 32, "atk": 25},
        "bonus_desc": "🏃 +35 Ловкость | 💨 +32% Уворот | ⚔️ +25 Базовый урон"
    },
    {
        "name": "Обезьяний Посох (Monkey King Bar)",
        "icon": "🐒",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 52,
        "base_max": 78,
        "bonus": {"true_strike": 80, "atk": 30},
        "bonus_desc": "⚔️ +52..78 Урон | 🎯 80% Истинный удар сквозь увороты"
    },
    {
        "name": "Сияние (Radiance)",
        "icon": "☀️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 60,
        "base_max": 85,
        "bonus": {"burn_aura": 65, "dodge": 15},
        "bonus_desc": "⚔️ +60..85 Урон | 🔥 Аура Ожога 65 урона/сек | 💨 +15% Уворот"
    },
    {
        "name": "Опустошитель (Desolator)",
        "icon": "🔴",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 58,
        "base_max": 82,
        "bonus": {"armor_pierce": 6},
        "bonus_desc": "⚔️ +58..82 Урон | 🩸 Снижает броню врага на 6"
    },
    {
        "name": "Сатаник (Satanic)",
        "icon": "🩸",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "bonus": {"str": 25, "atk": 35, "lifesteal": 28},
        "bonus_desc": "💪 +25 Сила | ⚔️ +35 Урон | 🧛 +28% Вампиризм"
    },
    {
        "name": "Сердце Тарраска (Heart of Tarrasque)",
        "icon": "❤️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "epic",
        "base_def": 8,
        "base_hp": 650,
        "bonus": {"str": 45, "hp_regen_pct": 2},
        "bonus_desc": "💪 +45 Сила | ❤️ +650 HP | 💚 Регенерация +2% Макс. HP/сек"
    },
    {
        "name": "Кираса Штурма (Assault Cuirass)",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "epic",
        "base_def": 18,
        "base_hp": 300,
        "bonus": {"armor_aura": 5, "atk_speed": 35},
        "bonus_desc": "🛡️ +18 Броня | 🛡️ +5 Броня Аура | ⚡ +35% Скорость атаки"
    },
    {
        "name": "Черный Королевский Бар (Black King Bar)",
        "icon": "🟡",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "bonus": {"str": 12, "atk": 25, "magic_immune": 1},
        "bonus_desc": "💪 +12 Сила | ⚔️ +25 Урон | 🛡️ Иммунитет к оглушениям"
    },
    {
        "name": "Страж Шивы (Shiva Guard)",
        "icon": "❄️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "epic",
        "base_def": 16,
        "base_hp": 280,
        "bonus": {"int": 30, "slow_aura": 25},
        "bonus_desc": "🛡️ +16 Броня | 🔮 +30 Интеллект | ❄️ Ледяная Аура замедления"
    },
    {
        "name": "Око Скади (Eye of Skadi)",
        "icon": "👁️",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "bonus": {"all_stats": 25, "hp": 300, "mp": 300, "slow": 30},
        "bonus_desc": "✨ +25 ко всем статам | ❤️ +300 HP | ❄️ Атаки замедляют на 30%"
    },
    {
        "name": "Кровавый Шип (Bloodthorn)",
        "icon": "🌹",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 56,
        "base_max": 84,
        "bonus": {"int": 25, "crit": 25, "silence": 1},
        "bonus_desc": "⚔️ +56..84 Урон | 🔮 +25 Интеллект | 💥 +25% Крит"
    },
    {
        "name": "Мьёльнир (Mjollnir)",
        "icon": "⚡",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 35,
        "base_max": 55,
        "bonus": {"atk_speed": 65, "static_shield": 1},
        "bonus_desc": "⚔️ +35..55 Урон | ⚡ +65% Скорость атаки | ⚡ Статический Щит"
    },
    {
        "name": "Коса Вайса (Scythe of Vyse)",
        "icon": "🐏",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "bonus": {"int": 35, "str": 10, "agi": 10, "hex": 1},
        "bonus_desc": "🔮 +35 Интеллект | ✨ Хекс (превращение врага в овечку)"
    },
    {
        "name": "Абиссальный Клинок (Abyssal Blade)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 45,
        "base_max": 70,
        "bonus": {"str": 10, "hp": 250, "stun_active": 1},
        "bonus_desc": "⚔️ +45..70 Урон | 💪 +10 Сила | 💫 Оглушающий Удар"
    },

    # --- TIER 5: IMMORTAL / ANCIENT ARTIFACTS (Levels 90 - 150+) ---
    {
        "name": "Божественная Рапира (Divine Rapier)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "base_min": 250,
        "base_max": 380,
        "bonus": {"crit": 20},
        "bonus_desc": "👑 ВЫСШИЙ КЛИНОК: ⚔️ +250..380 Урон | 💥 +20% Крит (x2.5)"
    },
    {
        "name": "Эгида Бессмертия (Aegis of the Immortal)",
        "icon": "🛡️",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "bonus": {"hp": 500, "def": 15, "revive": 1},
        "bonus_desc": "👑 ВТОРАЯ ЖИЗНЬ: Воскрешение при гибели с 100% HP! | ❤️ +500 HP | 🛡️ +15 Броня"
    },
    {
        "name": "Сыр Рошана (Cheese)",
        "icon": "🧀",
        "type": "potion",
        "slot": "consumable",
        "slot_name": "Зелье",
        "slot_icon": "🧪",
        "rarity": "immortal",
        "count": 3,
        "heal_hp": 9999,
        "heal_mp": 9999,
        "bonus": {"full_heal": 1},
        "bonus_desc": "🧀 Мгновенно восстанавливает 100% HP и 100% MP (3 порции)!"
    },
    {
        "name": "Благословение Аганима (Aghanim Blessing)",
        "icon": "🔮",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "bonus": {"all_stats": 25, "hp": 350, "mp": 350, "ult_boost": 40},
        "bonus_desc": "👑 +25 Статы | ❤️ +350 HP | 💧 +350 MP | 💥 +40% Урон Ульты"
    },
    {
        "name": "Сфера Обновления (Refresher Orb)",
        "icon": "🟢",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "bonus": {"hp_regen": 15, "mp_regen": 12, "refresh": 1},
        "bonus_desc": "🔄 Мгновенно сбрасывает время перезарядки всех скиллов"
    },
    {
        "name": "Апекс (Apex)",
        "icon": "🔺",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "bonus": {"primary_attr": 75, "hp": 400},
        "bonus_desc": "👑 +75 к Основному Атрибуту (+75 Урон) | ❤️ +400 HP"
    },
    {
        "name": "Падшие Небеса (Fallen Sky)",
        "icon": "☄️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "base_min": 120,
        "base_max": 190,
        "bonus": {"str": 25, "meteor": 250},
        "bonus_desc": "⚔️ +120..190 Урон | ☄️ Падение Метеора оглушает на 3 сек"
    },
    {
        "name": "Зеркальный Щит (Mirror Shield)",
        "icon": "🪞",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "immortal",
        "base_def": 25,
        "base_hp": 600,
        "bonus": {"all_stats": 18, "reflect": 50},
        "bonus_desc": "🛡️ +25 Броня | ❤️ +600 HP | 🪞 50% Шанс Отразить любое заклинание"
    },
    {
        "name": "Гигантское Кольцо (Giant Ring)",
        "icon": "💍",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "immortal",
        "base_def": 20,
        "base_hp": 1200,
        "bonus": {"str": 50, "giant_stomp": 100},
        "bonus_desc": "💪 +50 Сила | ❤️ +1200 HP | 🦶 Топот растаптывает врагов"
    },
    {
        "name": "Стигийский Дезолятор (Stygian Desolator)",
        "icon": "🩸",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "base_min": 140,
        "base_max": 220,
        "bonus": {"armor_pierce": 12},
        "bonus_desc": "⚔️ +140..220 Урон | 🩸 РАССЕКАЕТ БРОНЮ ВРАГА НА -12"
    },
    {
        "name": "Око Вечности (Eye of Eternity)",
        "icon": "👁️",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "bonus": {"all_stats": 35, "hp": 800, "mp": 800, "atk": 80},
        "bonus_desc": "👑 ВЕЛИКИЙ АРТЕФАКТ: +35 Все статы | ❤️ +800 HP | 💧 +800 MP | ⚔️ +80 Урон"
    }
,
{   'base_max': 7,
    'base_min': 4,
    'bonus': {'int': 2, 'magic_dmg': 3},
    'bonus_desc': '⚔️ +4..7 Урон | 🔮 +2 Интеллект | ⚡ +3 Магич. урон',
    'icon': '🦯',
    'name': 'Дубовый Посох (Oak Staff)',
    'rarity': 'common',
    'slot': 'weapon',
    'slot_icon': '⚔️',
    'slot_name': 'Оружие',
    'type': 'weapon'},
{   'base_max': 6,
    'base_min': 3,
    'bonus': {'agi': 1, 'atk_speed': 4},
    'bonus_desc': '⚔️ +3..6 Урон | 🏃 +1 Ловкость | ⚡ +4% Скор. атаки',
    'icon': '🗡️',
    'name': 'Ржавый Кинжал (Rusty Dagger)',
    'rarity': 'common',
    'slot': 'weapon',
    'slot_icon': '⚔️',
    'slot_name': 'Оружие',
    'type': 'weapon'},
{   'base_def': 2,
    'base_hp': 25,
    'bonus': {'block': 5},
    'bonus_desc': '🛡️ +2 Броня | ❤️ +25 HP | 🛡️ Блок 5 урона',
    'icon': '🛡️',
    'name': 'Деревянный Баклер (Wooden Buckler)',
    'rarity': 'common',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'bonus': {'hp': 25, 'mp': 15},
    'bonus_desc': '❤️ +25 HP | 💧 +15 MP',
    'icon': '💎',
    'name': 'Треснувший Опал (Cracked Opal)',
    'rarity': 'common',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'atk': 2, 'mp_regen': 1.2},
    'bonus_desc': '⚔️ +2 Урон | 💧 +1.2 Реген MP/сек',
    'icon': '💍',
    'name': 'Кольцо Базилиуса (Ring of Basilius)',
    'rarity': 'common',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'base_max': 8,
    'base_min': 5,
    'bonus': {'creep_dmg': 6, 'str': 2},
    'bonus_desc': '⚔️ +5..8 Урон | 💪 +2 Сила | 🌲 +6 Урон по крипам',
    'icon': '🪓',
    'name': 'Топорик Лесоруба (Woodcutter Hatchet)',
    'rarity': 'common',
    'slot': 'weapon',
    'slot_icon': '⚔️',
    'slot_name': 'Оружие',
    'type': 'weapon'},
{   'base_def': 1,
    'base_hp': 20,
    'bonus': {'int': 2, 'mp': 20},
    'bonus_desc': '🛡️ +1 Броня | ❤️ +20 HP | 🔮 +2 Интеллект',
    'icon': '🎗️',
    'name': 'Повязка Ученика (Apprentice Band)',
    'rarity': 'common',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'bonus': {'agi': 2, 'dodge': 2},
    'bonus_desc': '🏃 +2 Ловкость | 💨 +2% Шанс Уворота',
    'icon': '🎗️',
    'name': 'Шнурок Проворства (Lace of Haste)',
    'rarity': 'common',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'atk': 3, 'hp': 60, 'hp_regen': 1.0, 'str': 5},
    'bonus_desc': '💪 +5 Сила | ⚔️ +3 Урон | ❤️ +60 HP | 🩸 +1.0 HP/сек',
    'icon': '🥊',
    'name': 'Брейсер Защитника (Bracer)',
    'rarity': 'uncommon',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'agi': 5, 'atk_speed': 6, 'def': 2},
    'bonus_desc': '🏃 +5 Ловкость | 🛡️ +2 Броня | ⚡ +6% Скор. атаки',
    'icon': '💍',
    'name': 'Врейс Бенд (Wraith Band)',
    'rarity': 'uncommon',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'int': 5, 'mp': 60, 'spell_amp': 3},
    'bonus_desc': '🔮 +5 Интеллект | 💧 +60 MP | ✨ +3% Сила магии',
    'icon': '📿',
    'name': 'Нулл Талисман (Null Talisman)',
    'rarity': 'uncommon',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'def': 2, 'hp_regen': 1.5, 'str': 6},
    'bonus_desc': '💪 +6 Сила | 🛡️ +2 Броня | 🩸 +1.5 HP/сек',
    'icon': '💍',
    'name': 'Кольцо Души (Soul Ring)',
    'rarity': 'uncommon',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'hp': 100, 'hp_regen': 2.0},
    'bonus_desc': '❤️ +100 HP | 🩸 +2.0 Реген HP/сек',
    'icon': '💧',
    'name': 'Капля Жизни (Tear of Life)',
    'rarity': 'uncommon',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'base_def': 3,
    'base_hp': 75,
    'bonus': {'magic_resist': 12},
    'bonus_desc': '🛡️ +3 Броня | ❤️ +75 HP | 🔮 +12% Магич. сопротивление',
    'icon': '🧥',
    'name': 'Плащ Мудрости (Cloak of Wisdom)',
    'rarity': 'uncommon',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'base_max': 20,
    'base_min': 14,
    'bonus': {'agi': 4, 'crit_chance': 4},
    'bonus_desc': '⚔️ +14..20 Урон | 🏃 +4 Ловкость | 🎯 +4% Шанс Крита',
    'icon': '🗡️',
    'name': 'Кинжал Тени (Shadow Dagger)',
    'rarity': 'uncommon',
    'slot': 'weapon',
    'slot_icon': '⚔️',
    'slot_name': 'Оружие',
    'type': 'weapon'},
{   'bonus': {'agi': 7, 'atk': 7, 'def': 2, 'int': 3, 'str': 3},
    'bonus_desc': '🏃 +7 Ловк | 💪 +3 Сила | 🔮 +3 Инт | ⚔️ +7 Урон | 🛡️ +2 Броня',
    'icon': '💍',
    'name': 'Кольцо Аквилы (Ring of Aquila)',
    'rarity': 'uncommon',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'atk_speed': 14, 'int': 7, 'str': 7},
    'bonus_desc': '💪 +7 Сила | 🔮 +7 Инт | ⚡ +14% Скор. Атаки аура',
    'icon': '🥁',
    'name': 'Барабаны Войны (Drum of Endurance)',
    'rarity': 'rare',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'atk_percent': 12, 'def': 4, 'lifesteal': 15},
    'bonus_desc': '🛡️ +4 Броня | 🩸 +15% Вампиризм | ⚔️ +12% Бонус урона',
    'icon': '🦇',
    'name': 'Владимир (Vladmir Offering)',
    'rarity': 'rare',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'base_def': 8,
    'base_hp': 200,
    'bonus': {'all_stats': 6, 'dodge': 6},
    'bonus_desc': '🛡️ +8 Броня | ❤️ +200 HP | 🌟 +6 Все статы | 💨 +6% Уворот',
    'icon': '☀️',
    'name': 'Солар Крест (Solar Crest)',
    'rarity': 'rare',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'bonus': {'int': 12, 'mp': 300, 'mp_regen': 2.5, 'spell_amp': 8},
    'bonus_desc': '🔮 +12 Инт | 💧 +300 MP | 💧 +2.5 MP/сек | ✨ +8% Сила магии',
    'icon': '🔍',
    'name': 'Линза Эфира (Aether Lens)',
    'rarity': 'rare',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'base_def': 5,
    'base_hp': 180,
    'bonus': {'dodge': 8, 'magic_resist': 20},
    'bonus_desc': '🛡️ +5 Броня | ❤️ +180 HP | 🔮 +20% Маг. Резист | 💨 +8% Уворот',
    'icon': '🧥',
    'name': 'Плащ Мерцания (Glimmer Cape)',
    'rarity': 'rare',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'base_max': 42,
    'base_min': 28,
    'bonus': {'atk_speed': 10, 'double_strike': 15, 'str': 12},
    'bonus_desc': '⚔️ +28..42 Урон | 💪 +12 Сила | ⚡ 15% Шанс Двойного Удара',
    'icon': '⚔️',
    'name': 'Эхо Сабля (Echo Sabre)',
    'rarity': 'rare',
    'slot': 'weapon',
    'slot_icon': '⚔️',
    'slot_name': 'Оружие',
    'type': 'weapon'},
{   'base_max': 48,
    'base_min': 32,
    'bonus': {'hp_regen': 3.0, 'int': 12, 'str': 12},
    'bonus_desc': '⚔️ +32..48 Урон | 💪 +12 Сила | 🔮 +12 Инт | ☄️ Огненный удар',
    'icon': '☄️',
    'name': 'Метеор Хаммер (Meteor Hammer)',
    'rarity': 'rare',
    'slot': 'weapon',
    'slot_icon': '⚔️',
    'slot_name': 'Оружие',
    'type': 'weapon'},
{   'base_max': 50,
    'base_min': 35,
    'bonus': {'agi': 10, 'int': 8, 'str': 10},
    'bonus_desc': '⚔️ +35..50 Урон | 🌟 +10 Сила/Ловкость | 🔱 Притягивает крипов',
    'icon': '🔱',
    'name': 'Меч Гарпуна (Harpoon Blade)',
    'rarity': 'rare',
    'slot': 'weapon',
    'slot_icon': '⚔️',
    'slot_name': 'Оружие',
    'type': 'weapon'},
{   'base_max': 95,
    'base_min': 65,
    'bonus': {'agi': 12, 'chain_lightning': 25, 'int': 24},
    'bonus_desc': '⚔️ +65..95 Урон | 🔮 +24 Инт | ⚡ 25% Цепная Молния 180 урона',
    'icon': '⚡',
    'name': 'Крикун Глейпнир (Gleipnir)',
    'rarity': 'epic',
    'slot': 'weapon',
    'slot_icon': '⚔️',
    'slot_name': 'Оружие',
    'type': 'weapon'},
{   'base_def': 16,
    'base_hp': 450,
    'bonus': {'damage_block': 40, 'str': 15},
    'bonus_desc': '🛡️ +16 Броня | ❤️ +450 HP | 💪 +15 Сила | 🛡️ Блок 40 урона',
    'icon': '🛡️',
    'name': 'Кримсон Гард (Crimson Guard)',
    'rarity': 'epic',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'base_def': 10,
    'base_hp': 400,
    'bonus': {'hp_regen': 6.0, 'magic_resist': 30},
    'bonus_desc': '🛡️ +10 Броня | ❤️ +400 HP | 🔮 +30% Маг. Резист | 🩸 +6 HP/сек',
    'icon': '🪈',
    'name': 'Трубка Прозрения (Pipe of Insight)',
    'rarity': 'epic',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'base_def': 12,
    'base_hp': 350,
    'bonus': {'combo_shield': 1, 'mp': 350},
    'bonus_desc': '🛡️ +12 Броня | ❤️ +350 HP | 💧 +350 MP | 🛡️ Неуязвимость при низком HP',
    'icon': '📀',
    'name': 'Эон Диск (Aeon Disk)',
    'rarity': 'epic',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'bonus': {'int': 35, 'move_speed': 15, 'mp_regen': 4.0},
    'bonus_desc': '🔮 +35 Инт | 💧 +4.0 MP/сек | 🌪️ Циклон неуязвимости',
    'icon': '🌪️',
    'name': 'Винд Вейкер (Wind Waker)',
    'rarity': 'epic',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'atk': 45, 'int': 25, 'magic_pierce': 20},
    'bonus_desc': '🔮 +25 Инт | ⚔️ +45 Урон | 👻 Атаки пробивают сопротивление магии',
    'icon': '👻',
    'name': 'Брошь Призрака (Revenant Brooch)',
    'rarity': 'epic',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'cooldown_reduct': 25, 'hp': 425, 'mp': 725},
    'bonus_desc': '❤️ +425 HP | 💧 +725 MP | ⏱️ -25% Время перезарядки способностей',
    'icon': '🔮',
    'name': 'Октарин Ядро (Octarine Core)',
    'rarity': 'epic',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'all_stats': 16, 'hp_regen': 4.0, 'mp_regen': 3.0},
    'bonus_desc': '🌟 +16 Все атрибуты | 🩸 +4 HP/сек | 🛡️ Блокирует опасные заклинания',
    'icon': '🌐',
    'name': 'Сфера Линкена (Linken Sphere)',
    'rarity': 'epic',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'bonus': {'hp': 750, 'int': 30, 'str': 30, 'summon_demons': 4},
    'bonus_desc': '👑 ВЕЛИКИЙ АРТЕФАКТ: 💪 +30 Сила | 🔮 +30 Инт | 💀 Призыв 4 демонов',
    'icon': '📖',
    'name': 'Книга Мертвых (Book of the Dead)',
    'rarity': 'immortal',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'base_def': 20,
    'base_hp': 900,
    'bonus': {'atk_speed': 40, 'gold_boost': 25},
    'bonus_desc': '🛡️ +20 Броня | ❤️ +900 HP | ⚡ +40% Скор. Атаки | 🪙 +25% Больше золота',
    'icon': '🏴\u200d☠️',
    'name': 'Пиратская Шляпа (Pirate Hat)',
    'rarity': 'immortal',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'base_def': 18,
    'base_hp': 850,
    'bonus': {'dispel': 1, 'hp_regen': 10.0, 'move_speed': 30},
    'bonus_desc': '🛡️ +18 Броня | ❤️ +850 HP | 🩸 +10 HP/сек | 💨 Сверхбыстрый рывок и сброс станов',
    'icon': '👢',
    'name': 'Сапоги Силы (Force Boots)',
    'rarity': 'immortal',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'},
{   'bonus': {'mp': 800, 'mp_regen': 10.0, 'spell_amp': 25, 'truesight': 1},
    'bonus_desc': '💧 +800 MP | 💧 +10 MP/сек | ✨ +25% Сила Заклинаний | 👁️ Истинное Зрение',
    'icon': '🔮',
    'name': 'Камень Провидца (Seer Stone)',
    'rarity': 'immortal',
    'slot': 'relic',
    'slot_icon': '💍',
    'slot_name': 'Реликвия',
    'type': 'relic'},
{   'base_def': 28,
    'base_hp': 1100,
    'bonus': {'all_stats': 25, 'instant_refresh': 1},
    'bonus_desc': '🛡️ +28 Броня | ❤️ +1100 HP | 🌟 +25 Все характеристики | ⚙️ Сброс всех кулдаунов',
    'icon': '⚙️',
    'name': 'Экс Махина (Ex Machina)',
    'rarity': 'immortal',
    'slot': 'armor',
    'slot_icon': '🛡️',
    'slot_name': 'Броня',
    'type': 'armor'}
,
    # --- EXPANDED DOTA 2 MAGE & AGILITY ARTIFACTS ---
    {
        "name": "Посох Чародея (Staff of Wizardry)",
        "icon": "🪄",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "uncommon",
        "base_min": 15,
        "base_max": 24,
        "bonus": {"int": 10, "mp": 80, "spell_amp": 5},
        "bonus_desc": "🔮 +10 Интеллект | 💧 +80 MP | ✨ +5% Сила заклинаний"
    },
    {
        "name": "Клинок Ловкости (Blade of Alacrity)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "uncommon",
        "base_min": 16,
        "base_max": 25,
        "bonus": {"agi": 10, "atk_speed": 8, "dodge": 3},
        "bonus_desc": "🏃 +10 Ловкость | ⚡ +8% Скор. атаки | 💨 +3% Уворот"
    },
    {
        "name": "Дагон I (Dagon I)",
        "icon": "⚡",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "bonus": {"int": 14, "spell_amp": 12, "burst_magic": 120},
        "bonus_desc": "🔮 +14 Интеллект | ✨ +12% Сила заклинаний | ⚡ Энерго-разряд 120 ед."
    },
    {
        "name": "Скипетр Эула (Eul's Scepter)",
        "icon": "🌪️",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "bonus": {"int": 18, "mp_regen": 5.0, "dodge": 8},
        "bonus_desc": "🔮 +18 Интеллект | 💧 +5 MP/сек | 💨 +8% Уворот | 🌪️ Циклон неуязвимости"
    },
    {
        "name": "Мистический Посох (Mystic Staff)",
        "icon": "🧙",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 28,
        "base_max": 42,
        "bonus": {"int": 25, "mp": 250, "spell_amp": 10},
        "bonus_desc": "🔮 +25 Интеллект | 💧 +250 MP | ✨ +10% Сила заклинаний"
    },
    {
        "name": "Орлиный Рог (Eaglehorn)",
        "icon": "🏹",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "base_min": 30,
        "base_max": 44,
        "bonus": {"agi": 25, "atk_speed": 18, "dodge": 6},
        "bonus_desc": "🏃 +25 Ловкость | ⚡ +18% Скор. атаки | 💨 +6% Уворот"
    },
    {
        "name": "Ботинки Путешествий (Boots of Travel)",
        "icon": "👟",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "bonus": {"agi": 15, "dodge": 12, "atk_speed": 15},
        "bonus_desc": "🏃 +15 Ловкость | 💨 +12% Уворот | ⚡ +15% Скор. атаки"
    },
    {
        "name": "Дагон III (Dagon III)",
        "icon": "⚡",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "bonus": {"int": 24, "spell_amp": 20, "burst_magic": 240},
        "bonus_desc": "🔮 +24 Интеллект | ✨ +20% Сила заклинаний | ⚡ Энерго-разряд 240 ед."
    },
    {
        "name": "Дагон V (Dagon V)",
        "icon": "⚡",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "bonus": {"int": 34, "spell_amp": 28, "burst_magic": 360},
        "bonus_desc": "🔮 +34 Интеллект | ✨ +28% Сила заклинаний | ⚡ Сокрушительный разряд 360 ед."
    },
    {
        "name": "Эфирный Клинок (Ethereal Blade)",
        "icon": "🪄",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 46,
        "base_max": 70,
        "bonus": {"int": 30, "agi": 20, "spell_amp": 22, "burst_magic": 180},
        "bonus_desc": "🔮 +30 Интеллект | 🏃 +20 Ловкость | ✨ +22% Сила магии | 🌀 Эфирный залп"
    },
    {
        "name": "Кайя и Саша (Kaya and Sange)",
        "icon": "⚔️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 44,
        "base_max": 66,
        "bonus": {"int": 20, "str": 20, "hp": 220, "spell_amp": 18, "lifesteal": 10},
        "bonus_desc": "🔮 +20 Интеллект | 💪 +20 Сила | ❤️ +220 HP | ✨ +18% Сила заклинаний | 🧛 +10% Вампиризм"
    },
    {
        "name": "Яша и Кайя (Yasha and Kaya)",
        "icon": "⚔️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 44,
        "base_max": 66,
        "bonus": {"int": 20, "agi": 20, "spell_amp": 18, "atk_speed": 22, "dodge": 10},
        "bonus_desc": "🔮 +20 Интеллект | 🏃 +20 Ловкость | ✨ +18% Сила заклинаний | ⚡ +22% Скор. атаки"
    },
    {
        "name": "Манта Стайл (Manta Style)",
        "icon": "👥",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 42,
        "base_max": 64,
        "bonus": {"agi": 26, "str": 10, "int": 10, "atk_speed": 25, "dodge": 12},
        "bonus_desc": "🏃 +26 Ловкость | 👑 +10 Сила/Инт | ⚡ +25% Скор. атаки | 💨 +12% Уворот | 👥 Призыв иллюзий"
    },
    {
        "name": "Серебряный Кортик (Silver Edge)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 62,
        "base_max": 92,
        "bonus": {"agi": 26, "crit": 28, "dodge": 15, "atk": 25},
        "bonus_desc": "🏃 +26 Ловкость | 💥 +28% Крит | 💨 +15% Уворот | ⚔️ +25 Базовый урон"
    },
    {
        "name": "Ураганная Пика (Hurricane Pike)",
        "icon": "🔱",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "base_min": 46,
        "base_max": 68,
        "bonus": {"agi": 22, "int": 18, "str": 15, "hp": 240, "dodge": 8},
        "bonus_desc": "🏃 +22 Ловкость | 🔮 +18 Интеллект | 💪 +15 Сила | ❤️ +240 HP"
    },
    {
        "name": "Сфера Линки (Linken's Sphere)",
        "icon": "🌐",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "bonus": {"all_stats": 22, "hp": 400, "mp": 400, "hp_regen": 8, "mp_regen": 6, "magic_immune": 1},
        "bonus_desc": "🌟 +22 Все характеристики | ❤️ +400 HP | 💧 +400 MP | 🛡️ Блок смертельного удара"
    }
]

DOTA_ITEMS_CATALOG = NATAR_ITEMS_CATALOG

# ==============================================================================
# CREEPS & DUNGEON BOSSES (КРИПЫ И БОССЫ ПОДЗЕМЕЛЬЯ)
# ==============================================================================

NATAR_CREEPS_POOL = [
    # --- НОВЫЕ КРИПЫ ВЫСОКИХ ЭТАЖЕЙ (20, 40, 50, 80, 100, 200+) ---
    {"name": "Варлок Легиона", "icon": "🔮", "base_hp": 320, "base_atk": 38, "base_def": 8, "gold": 14, "xp": 18, "floor_min": 20},
    {"name": "Железный Голем", "icon": "🗿", "base_hp": 550, "base_atk": 42, "base_def": 24, "gold": 16, "xp": 22, "floor_min": 20},
    {"name": "Адская Гончая", "icon": "🐕", "base_hp": 260, "base_atk": 45, "base_def": 6, "gold": 12, "xp": 16, "floor_min": 20},
    {"name": "Некромант Катакомб", "icon": "💀", "base_hp": 480, "base_atk": 52, "base_def": 10, "gold": 22, "xp": 30, "floor_min": 40},
    {"name": "Теневой Ассасин", "icon": "🗡️", "base_hp": 380, "base_atk": 65, "base_def": 12, "gold": 24, "xp": 34, "floor_min": 40},
    {"name": "Костяной Страж", "icon": "🛡️", "base_hp": 650, "base_atk": 48, "base_def": 30, "gold": 26, "xp": 36, "floor_min": 40},
    {"name": "Кентавр-Завоеватель", "icon": "🐎", "base_hp": 900, "base_atk": 60, "base_def": 35, "gold": 38, "xp": 48, "floor_min": 50},
    {"name": "Инфернальный Дракон", "icon": "🐉", "base_hp": 850, "base_atk": 75, "base_def": 25, "gold": 42, "xp": 54, "floor_min": 50},
    {"name": "Пламенный Маг", "icon": "🔥", "base_hp": 720, "base_atk": 82, "base_def": 18, "gold": 40, "xp": 52, "floor_min": 50},
    {"name": "Повелитель Пустоты", "icon": "👁️", "base_hp": 1200, "base_atk": 90, "base_def": 30, "gold": 65, "xp": 85, "floor_min": 80},
    {"name": "Абиссальный Бегемот", "icon": "👹", "base_hp": 1600, "base_atk": 110, "base_def": 40, "gold": 80, "xp": 100, "floor_min": 80},
    {"name": "Вестник Разлома", "icon": "⚡", "base_hp": 1100, "base_atk": 125, "base_def": 28, "gold": 75, "xp": 95, "floor_min": 80},
    {"name": "Древний Титан Скал", "icon": "🏔️", "base_hp": 2800, "base_atk": 140, "base_def": 50, "gold": 130, "xp": 170, "floor_min": 100},
    {"name": "Архимаг Хаоса", "icon": "🧙", "base_hp": 2200, "base_atk": 160, "base_def": 35, "gold": 140, "xp": 180, "floor_min": 100},
    {"name": "Паладин Падших", "icon": "✨", "base_hp": 2500, "base_atk": 130, "base_def": 55, "gold": 135, "xp": 175, "floor_min": 100},
    {"name": "Страж Апокалипсиса", "icon": "🔥", "base_hp": 5500, "base_atk": 250, "base_def": 70, "gold": 260, "xp": 360, "floor_min": 200},
    {"name": "Астральный Призрак", "icon": "👻", "base_hp": 4800, "base_atk": 300, "base_def": 45, "gold": 290, "xp": 410, "floor_min": 200},
    {"name": "Космический Разрушитель", "icon": "🌌", "base_hp": 6200, "base_atk": 340, "base_def": 60, "gold": 320, "xp": 450, "floor_min": 200},
    {"name": "Линейный Мечник", "icon": "🗡️", "base_hp": 120, "base_atk": 12, "base_def": 3, "gold": 4, "xp": 6},
    {"name": "Линейный Стрелок", "icon": "🏹", "base_hp": 90, "base_atk": 16, "base_def": 1, "gold": 5, "xp": 7},
    {"name": "Осадная Катапульта", "icon": "🚜", "base_hp": 260, "base_atk": 24, "base_def": 6, "gold": 8, "xp": 10},
    {"name": "Супер-Мечник Тьмы", "icon": "⚔️", "base_hp": 220, "base_atk": 22, "base_def": 8, "gold": 7, "xp": 9},
    {"name": "Лесной Волк Катакомб", "icon": "🐺", "base_hp": 160, "base_atk": 20, "base_def": 4, "gold": 5, "xp": 8},
    {"name": "Кентавр-Воитель", "icon": "🐎", "base_hp": 310, "base_atk": 26, "base_def": 9, "gold": 9, "xp": 12},
    {"name": "Адский Крушитель", "icon": "🐻", "base_hp": 380, "base_atk": 30, "base_def": 10, "gold": 10, "xp": 14},
    {"name": "Сатир-Осквернитель", "icon": "🐐", "base_hp": 240, "base_atk": 28, "base_def": 6, "gold": 8, "xp": 11}
]

NATAR_FLOOR_BOSSES = [
    {"name": "Мясник Катакомб", "icon": "🪝", "base_hp": 25000, "base_atk": 45, "base_def": 15, "gold": 140, "xp": 160},
    {"name": "Повелитель Теней", "icon": "💀", "base_hp": 35000, "base_atk": 55, "base_def": 18, "gold": 160, "xp": 180},
    {"name": "Древний Терзатель", "icon": "🔮", "base_hp": 50000, "base_atk": 65, "base_def": 22, "gold": 180, "xp": 220},
    {"name": "Дракон Инферно", "icon": "🐉", "base_hp": 70000, "base_atk": 80, "base_def": 26, "gold": 210, "xp": 250},
    {"name": "РОШАН СВИРЕПЫЙ (Roshan)", "icon": "🐲", "base_hp": 95000, "base_atk": 100, "base_def": 32, "gold": 260, "xp": 300},
    {"name": "Левиафан Бездны (Tidehunter)", "icon": "🐙", "base_hp": 125000, "base_atk": 120, "base_def": 36, "gold": 310, "xp": 360},
    {"name": "Повелитель Душ (Nevermore)", "icon": "💀", "base_hp": 160000, "base_atk": 145, "base_def": 40, "gold": 370, "xp": 430},
    {"name": "Чумной Владыка (Necrophos)", "icon": "🧟", "base_hp": 205000, "base_atk": 170, "base_def": 44, "gold": 440, "xp": 510},
    {"name": "Демиург Арсенала (Invoker)", "icon": "🧙‍♂️", "base_hp": 260000, "base_atk": 200, "base_def": 48, "gold": 520, "xp": 600},
    {"name": "Всадник Хаоса (Chaos Knight)", "icon": "🐎", "base_hp": 325000, "base_atk": 235, "base_def": 52, "gold": 610, "xp": 700},
    {"name": "Тёмный Терзатель Бездны", "icon": "💎", "base_hp": 400000, "base_atk": 275, "base_def": 58, "gold": 720, "xp": 820},
    {"name": "Вестник Апокалипсиса (Doom)", "icon": "👹", "base_hp": 490000, "base_atk": 320, "base_def": 64, "gold": 840, "xp": 950},
    {"name": "Первобытный Титан (Primal Beast)", "icon": "🦣", "base_hp": 600000, "base_atk": 370, "base_def": 70, "gold": 980, "xp": 1100},
    {"name": "Призрачный Рошан Хаоса", "icon": "👻", "base_hp": 730000, "base_atk": 430, "base_def": 78, "gold": 1150, "xp": 1300},
    {"name": "Пожиратель Миров (Enigma Cosmic)", "icon": "🌌", "base_hp": 900000, "base_atk": 500, "base_def": 88, "gold": 1400, "xp": 1600}
]

DOTA_CREEPS_POOL = NATAR_CREEPS_POOL
DOTA_FLOOR_BOSSES = NATAR_FLOOR_BOSSES


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

    # Equipment slots
    eq = char.equipment or {}
    weapon = eq.get("weapon")
    armor = eq.get("armor")
    relic = eq.get("relic")

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
    flat_hp_regen = 0.0
    flat_mp_regen = 0.0
    w_min = 8
    w_max = 14

    for slot_item in (weapon, armor, relic):
        if not slot_item:
            continue
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
        flat_hp_regen += sb.get("hp_regen", 0)
        flat_mp_regen += sb.get("mp_regen", 0)

    if weapon:
        w_min = weapon.get("min_atk") or weapon.get("base_min") or 8
        w_max = weapon.get("max_atk") or weapon.get("base_max") or 14

    if armor:
        flat_def += armor.get("defense") or armor.get("base_def") or armor.get("def") or 0
        flat_hp += armor.get("hp_bonus") or armor.get("base_hp") or 0

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
        "dodge_chance": dodge_chance,
        "lifesteal": min(60, lifesteal),
        "gear_score": gear_score,
        "primary_attr": cfg["attr"],
        "primary_damage_bonus": int(primary_bonus),
        "spell_amp": spell_amp,
        "ult_boost": ult_boost,
        "ult_cd_reduct": min(60, ult_cd_reduct),
        "damage_type": damage_type,
        "skill": cfg["skill"],
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


# ==============================================================================
# REWARD CHEST SYSTEM & LOOT GENERATOR
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

    BOSS_EXCLUSIVE_DROPS = {
        "golem": [
            {
                "name": "Гранитный Молот Сокрушения",
                "icon": "🔨",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "epic",
                "rarity_name": "Эпический",
                "rarity_color": "#c084fc",
                "base_min": 55,
                "base_max": 78,
                "bonus": {"stun_chance": 20, "str": 15},
                "bonus_desc": "⚔️ +55..78 Урон | 💥 +20% Шанс оглушения | 🥩 +15 Сила"
            },
            {
                "name": "Осколок Гранитного Кристалла",
                "icon": "🔮",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "epic",
                "rarity_name": "Эпический",
                "rarity_color": "#c084fc",
                "bonus": {"int": 18, "spell_amp": 15, "magic_dmg": 25},
                "bonus_desc": "🔮 +18 Интеллект | ✨ +15% Сила заклинаний | ⚡ +25 Магический урон"
            },
            {
                "name": "Обсидиановый Доспех Колосса",
                "icon": "🛡️",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "epic",
                "rarity_name": "Эпический",
                "rarity_color": "#c084fc",
                "defense": 22,
                "hp_bonus": 160,
                "bonus": {"damage_block": 25, "hp": 160},
                "bonus_desc": "🛡️ +22 Броня | ❤️ +160 HP | 🧱 Блок 25 ед. урона"
            },
            {
                "name": "Кинжал из Обсидиана",
                "icon": "🗡️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "epic",
                "rarity_name": "Эпический",
                "rarity_color": "#c084fc",
                "base_min": 50,
                "base_max": 74,
                "bonus": {"agi": 18, "atk_speed": 20, "crit": 15},
                "bonus_desc": "⚔️ +50..74 Урон | 🏃 +18 Ловкость | ⚡ +20% Скор. атаки | 💥 +15% Крит"
            }
        ],
        "lich": [
            {
                "name": "Ледяная Корона Архилича",
                "icon": "👑",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "legendary",
                "rarity_name": "Легендарный",
                "rarity_color": "#f59e0b",
                "bonus": {"int": 35, "spell_amp": 25, "freeze_chance": 30},
                "bonus_desc": "🔮 +35 Интеллект | ✨ +25% Сила заклинаний | ❄️ 30% Шанс заморозки"
            },
            {
                "name": "Око Ледяного Шторма (Eye of Skadi)",
                "icon": "❄️",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"all_stats": 25, "slow_enemy": 35, "hp": 250, "mp": 250},
                "bonus_desc": "👑 +25 Все характеристики | ❄️ Замедление врагов 35% | ❤️ +250 HP | 🔮 +250 MP"
            },
            {
                "name": "Мантия Замерзшей Бездны",
                "icon": "🧥",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "legendary",
                "rarity_name": "Легендарный",
                "rarity_color": "#f59e0b",
                "defense": 26,
                "hp_bonus": 180,
                "bonus": {"frost_armor": 30, "int": 20},
                "bonus_desc": "🛡️ +26 Броня | ❤️ +180 HP | ❄️ Ледяной панцирь замедляет атакующих"
            },
            {
                "name": "Посох Абсолютного Нуля",
                "icon": "🪄",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "legendary",
                "rarity_name": "Легендарный",
                "rarity_color": "#f59e0b",
                "base_min": 75,
                "base_max": 115,
                "bonus": {"int": 30, "burst_magic": 140},
                "bonus_desc": "⚔️ +75..115 Урон | 🔮 +30 Интеллект | ⚡ Ледяной взрыв 140 ед."
            }
        ],
        "tormentor": [
            {
                "name": "Aghanim's Shard (Осколок Аганима)",
                "icon": "💎",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"spell_amp": 30, "int": 25, "ult_boost": 35, "ult_cd": 20},
                "bonus_desc": "🔮 +25 Интеллект | ✨ +30% Сила заклинаний | 💥 +35% Урон Ульты | ⏱️ -20% КД"
            },
            {
                "name": "Отражающий Панцирь Терзателя",
                "icon": "🔮",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "legendary",
                "rarity_name": "Легендарный",
                "rarity_color": "#f59e0b",
                "defense": 32,
                "hp_bonus": 220,
                "bonus": {"reflect": 40, "magic_resist": 25},
                "bonus_desc": "🛡️ +32 Броня | ❤️ +220 HP | 🪞 Отражает 40% входящего урона"
            },
            {
                "name": "Эфирный Фокус Терзателя",
                "icon": "🌀",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "legendary",
                "rarity_name": "Легендарный",
                "rarity_color": "#f59e0b",
                "bonus": {"int": 28, "spell_amp": 25, "burst_magic": 220},
                "bonus_desc": "🔮 +28 Интеллект | ✨ +25% Сила заклинаний | ⚡ Эфирный разряд 220 ед."
            },
            {
                "name": "Кристальный Клинок Бездны",
                "icon": "🗡️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "legendary",
                "rarity_name": "Легендарный",
                "rarity_color": "#f59e0b",
                "base_min": 85,
                "base_max": 125,
                "bonus": {"crit": 25, "agi": 22},
                "bonus_desc": "⚔️ +85..125 Урон | 🏃 +22 Ловкость | 💥 +25% Крит"
            }
        ],
        "dragon": [
            {
                "name": "Чешуя Черного Дракона",
                "icon": "🌋",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 36,
                "hp_bonus": 300,
                "bonus": {"fire_aura": 45, "str": 25},
                "bonus_desc": "🛡️ +36 Броня | ❤️ +300 HP | 🔥 Огненная аура дракона 45/с"
            },
            {
                "name": "Огненный Клинок Бездны",
                "icon": "🔥",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "legendary",
                "rarity_name": "Легендарный",
                "rarity_color": "#f59e0b",
                "base_min": 95,
                "base_max": 135,
                "bonus": {"burn": 50, "crit": 25, "agi": 28},
                "bonus_desc": "⚔️ +95..135 Урон | 🏃 +28 Ловкость | 🔥 Поджигание | 💥 +25% Крит"
            },
            {
                "name": "Дыхание Инферно (Inferno Heart)",
                "icon": "☄️",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "legendary",
                "rarity_name": "Легендарный",
                "rarity_color": "#f59e0b",
                "bonus": {"int": 32, "spell_amp": 28, "meteor": 180},
                "bonus_desc": "🔮 +32 Интеллект | ✨ +28% Сила заклинаний | ☄️ Метеор 180 ед."
            }
        ],
        "roshan": [
            {
                "name": "Aegis of the Immortal",
                "icon": "🛡️",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"hp": 150, "def": 15, "revive": 1, "all_stats": 10},
                "bonus_desc": "👑 ВТОРАЯ ЖИЗНЬ: Воскрешение при гибели! | ❤️ +150 HP | 🛡️ +15 Броня"
            },
            {
                "name": "Divine Rapier (Рапира Богов)",
                "icon": "🗡️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 180,
                "base_max": 260,
                "bonus": {"crit": 35, "pure_dmg": 30},
                "bonus_desc": "⚔️ +180..260 Урон | 💥 +35% Крит | 👑 Сила древних богов"
            },
            {
                "name": "Благословение Аганима (Aghanim Blessing)",
                "icon": "👑",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"all_stats": 30, "hp": 400, "mp": 400, "ult_boost": 45, "ult_cd": 20, "spell_amp": 15},
                "bonus_desc": "👑 +30 Все характеристики | 💥 +45% Урон Ульты | ⏱️ -20% КД Ульты | ✨ +15% Сила магии"
            },
            {
                "name": "Сердце Тарраска (Heart of Tarrasque)",
                "icon": "❤️",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 38,
                "hp_bonus": 650,
                "bonus": {"hp": 650, "str": 45, "regen": 40},
                "bonus_desc": "🛡️ +38 Броня | ❤️ +650 HP | 🥩 +45 Сила | 💖 +40 HP/сек Регенерация"
            },
            {
                "name": "Кираса Штурма (Assault Cuirass)",
                "icon": "🦺",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 45,
                "hp_bonus": 350,
                "bonus": {"atk_speed": 40, "def": 45, "armor_reduction": 15},
                "bonus_desc": "🛡️ +45 Броня | ⚡ +40% Скор. атаки | 🔨 Снижает броню врагов на 15"
            }
        ],
        "tidehunter": [
            {
                "name": "Титанический Якорь Кракена",
                "icon": "⚓",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 195,
                "base_max": 275,
                "bonus": {"str": 40, "stun_chance": 25, "weaken": 30},
                "bonus_desc": "⚔️ +195..275 Урон | 🥩 +40 Сила | 💥 25% Оглушение | 🌊 Снижает атаку врага на 30%"
            },
            {
                "name": "Панцирь Морского Левиафана",
                "icon": "🛡️",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 48,
                "hp_bonus": 450,
                "bonus": {"damage_block": 55, "hp": 450},
                "bonus_desc": "🛡️ +48 Броня | ❤️ +450 HP | 🌊 Чешуя Кракена: Блок 55 ед. любого урона"
            },
            {
                "name": "Жемчужина Океанической Бездны",
                "icon": "🔮",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"all_stats": 32, "water_surge": 300},
                "bonus_desc": "👑 +32 Все статы | 🌊 Волна глубин 300 ед. по площади"
            }
        ],
        "sf_boss": [
            {
                "name": "Дезолятор Тьмы (Desolator)",
                "icon": "🪓",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 210,
                "base_max": 290,
                "bonus": {"armor_pierce": 35, "crit": 30, "agi": 35},
                "bonus_desc": "⚔️ +210..290 Урон | 🩸 Пробивание брони 35 | 💥 +30% Крит"
            },
            {
                "name": "Пелерина Черного Реквиема",
                "icon": "👘",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 42,
                "hp_bonus": 400,
                "bonus": {"soul_steal": 20, "spell_amp": 25},
                "bonus_desc": "🛡️ +42 Броня | ❤️ +400 HP | 💀 Крадет души врагов при гибели"
            },
            {
                "name": "Венец Пожирателя Душ",
                "icon": "👑",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"agi": 35, "int": 35, "ult_boost": 50},
                "bonus_desc": "🏃 +35 Ловкость | 🔮 +35 Интеллект | 💥 +50% Урон Ульты"
            }
        ],
        "necrophos": [
            {
                "name": "Коса Жатвы Смерти (Reaper Scythe)",
                "icon": "⛏️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 220,
                "base_max": 300,
                "bonus": {"execute_low_hp": 25, "int": 40},
                "bonus_desc": "⚔️ +220..300 Урон | 🔮 +40 Интеллект | ☠️ Казнь врагов ниже 25% HP"
            },
            {
                "name": "Октариновое Ядро (Octarine Core)",
                "icon": "🔮",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"cooldown_reduct": 25, "spell_lifesteal": 25, "hp": 450, "mp": 450},
                "bonus_desc": "⏱️ -25% КД всех способностей | 🩸 +25% Вампиризм заклинаниями"
            },
            {
                "name": "Саван Чумного Архимага",
                "icon": "🧥",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 46,
                "hp_bonus": 500,
                "bonus": {"rot_aura": 65, "int": 30},
                "bonus_desc": "🛡️ +46 Броня | ❤️ +500 HP | ☣️ Аура чумы выжигает 65 ед./сек вокруг"
            }
        ],
        "invoker_boss": [
            {
                "name": "Посох Арканы Владыки Стихий",
                "icon": "🪄",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 235,
                "base_max": 320,
                "bonus": {"spell_amp": 45, "int": 50, "meteor": 250},
                "bonus_desc": "⚔️ +235..320 Урон | 🔮 +50 Интеллект | ✨ +45% Сила магии | ☄️ Метеор 250"
            },
            {
                "name": "Мантия Высшего Демиурга",
                "icon": "🥻",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 48,
                "hp_bonus": 520,
                "bonus": {"all_stats": 35, "mp_regen": 30},
                "bonus_desc": "🛡️ +48 Броня | ❤️ +520 HP | 👑 +35 Все статы | 🔮 +30 MP/сек"
            },
            {
                "name": "Сфера Солнечного Удара (Sunstrike)",
                "icon": "☀️",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"pure_dmg": 85, "int": 45},
                "bonus_desc": "☀️ +85 Чистый урон ко всем атакам | 🔮 +45 Интеллект"
            }
        ],
        "chaos_knight": [
            {
                "name": "Рассекатель Реальности (Chaos Cleaver)",
                "icon": "⚔️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 250,
                "base_max": 350,
                "bonus": {"crit": 45, "crit_multiplier": 80, "str": 45},
                "bonus_desc": "⚔️ +250..350 Урон | 💥 +45% Крит с множителем x3.2 | 🥩 +45 Сила"
            },
            {
                "name": "Доспех Фантомного Всадника",
                "icon": "🛡️",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 52,
                "hp_bonus": 580,
                "bonus": {"illusion_evade": 30, "str": 35},
                "bonus_desc": "🛡️ +52 Броня | ❤️ +580 HP | 🌀 30% Шанс раствориться при ударе"
            },
            {
                "name": "Око Энтропии Хаоса",
                "icon": "👁️",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"chaos_burst": 350, "all_stats": 38},
                "bonus_desc": "👑 +38 Все характеристики | 💥 Всплеск энтропии 350 ед."
            }
        ],
        "dark_tormentor": [
            {
                "name": "Тёмный Панцирь Сингулярности",
                "icon": "💎",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 56,
                "hp_bonus": 650,
                "bonus": {"reflect": 50, "magic_resist": 35},
                "bonus_desc": "🛡️ +56 Броня | ❤️ +650 HP | 🪞 Отражает 50% ЛЮБОГО входящего урона"
            },
            {
                "name": "Шипованный Кристалл Антиматерии",
                "icon": "🗡️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 265,
                "base_max": 370,
                "bonus": {"pure_dmg": 60, "int": 45, "burst_magic": 320},
                "bonus_desc": "⚔️ +265..370 Урон | ⚡ +60 Чистый урон | 💥 Разрыв материи 320 ед."
            },
            {
                "name": "Призма Зеркального Отражения",
                "icon": "🔮",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"all_stats": 42, "reflect": 25},
                "bonus_desc": "👑 +42 Все характеристики | 🪞 +25% Дополнительное отражение"
            }
        ],
        "doom": [
            {
                "name": "Адский Палаш Рока (Doom Blade)",
                "icon": "🗡️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 280,
                "base_max": 390,
                "bonus": {"burn": 90, "pure_dmg": 75, "str": 50},
                "bonus_desc": "⚔️ +280..390 Урон | 🔥 Горение 90/сек | 🥩 +50 Сила | ⚡ +75 Чистый урон"
            },
            {
                "name": "Нагрудник Инфернальной Ярости",
                "icon": "🦺",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 60,
                "hp_bonus": 720,
                "bonus": {"fire_aura": 80, "str": 40},
                "bonus_desc": "🛡️ +60 Броня | ❤️ +720 HP | 🔥 Адская аура выжигает 80 ед./сек"
            },
            {
                "name": "Венец Люцифера (Crown of Doom)",
                "icon": "👑",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"all_stats": 45, "silence_enemy": 20},
                "bonus_desc": "👑 +45 Все характеристики | 🤐 20% Шанс наложить безмолвие"
            }
        ],
        "primal_beast": [
            {
                "name": "Сокрушитель Материков",
                "icon": "🔨",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 300,
                "base_max": 420,
                "bonus": {"str": 65, "crit": 40, "stun_chance": 35},
                "bonus_desc": "⚔️ +300..420 Урон | 🥩 +65 Сила | 💥 35% Сокрушительный стан"
            },
            {
                "name": "Броня Доисторического Колосса",
                "icon": "🛡️",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 66,
                "hp_bonus": 850,
                "bonus": {"hp": 850, "damage_block": 75},
                "bonus_desc": "🛡️ +66 Броня | ❤️ +850 HP | 🧱 Непробиваемый блок 75 ед. урона"
            },
            {
                "name": "Сатаник Первобытной Крови (Satanic)",
                "icon": "🩸",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"lifesteal": 45, "str": 50, "unholy_rage": 1},
                "bonus_desc": "🩸 +45% Вампиризм | 🥩 +50 Сила | 😈 Нечестивая ярость"
            }
        ],
        "phantom_roshan": [
            {
                "name": "Призрачный Aegis Хаоса",
                "icon": "👻",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"hp": 400, "def": 30, "revive": 1, "all_stats": 30},
                "bonus_desc": "👑 ПРИЗРАЧНОЕ ВОСКРЕШЕНИЕ: Вторая жизнь с 100% HP! | ❤️ +400 HP | 🛡️ +30 Броня"
            },
            {
                "name": "Рапира Призрачного Владыки",
                "icon": "🗡️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 320,
                "base_max": 450,
                "bonus": {"crit": 50, "pure_dmg": 90, "ghost_strike": 200},
                "bonus_desc": "⚔️ +320..450 Урон | 💥 +50% Крит | 👻 Призрачный удар 200 ед."
            },
            {
                "name": "Эктоплазменный Доспех Бессмертия",
                "icon": "🛡️",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 70,
                "hp_bonus": 950,
                "bonus": {"ethereal_evade": 35, "all_stats": 35},
                "bonus_desc": "🛡️ +70 Броня | ❤️ +950 HP | 👻 35% Шанс уклонения сквозь астрал"
            }
        ],
        "enigma": [
            {
                "name": "Сингулярность Энигмы (Black Hole Core)",
                "icon": "🌌",
                "type": "relic",
                "slot": "relic",
                "slot_name": "Реликвия",
                "slot_icon": "💍",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "bonus": {"all_stats": 60, "spell_amp": 60, "ult_boost": 75, "black_hole": 500},
                "bonus_desc": "🌌 СИЛА СИНГУЛЯРНОСТИ: +60 Все статы | 💥 +75% Урон Ульты | 🕳️ Черная Дыра 500"
            },
            {
                "name": "Космический Аннигилятор",
                "icon": "⚔️",
                "type": "weapon",
                "slot": "weapon",
                "slot_name": "Оружие",
                "slot_icon": "⚔️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "base_min": 360,
                "base_max": 500,
                "bonus": {"pure_dmg": 120, "crit": 50, "all_stats": 40},
                "bonus_desc": "⚔️ +360..500 Урон | ⚡ +120 Чистый урон | 💥 +50% Крит | 👑 +40 Статы"
            },
            {
                "name": "Мантия Вселенской Пустоты",
                "icon": "🧥",
                "type": "armor",
                "slot": "armor",
                "slot_name": "Броня",
                "slot_icon": "🛡️",
                "rarity": "immortal",
                "rarity_name": "Бессмертный",
                "rarity_color": "#eab308",
                "defense": 80,
                "hp_bonus": 1200,
                "bonus": {"void_shield": 60, "hp": 1200, "def": 80},
                "bonus_desc": "🛡️ +80 Броня | ❤️ +1200 HP | 🌌 Щит Пустоты поглощает 60% урона"
            }
        ]
    }

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


async def equip_item_for_character(
    session: AsyncSession,
    char: RPGCharacter,
    item_uid: str
) -> Tuple[bool, str]:
    """Equips an item from inventory to character slot."""
    inventory = list(char.inventory)
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

    raw_slot = item.get("slot") or item.get("type") or ""
    slot = str(raw_slot).strip().lower()
    if slot not in ["weapon", "armor", "relic"]:
        return False, "Этот предмет нельзя надеть в слот снаряжения."

    item["slot"] = slot
    item["type"] = slot

    equipment = dict(char.equipment or {})
    old_equipped = equipment.get(slot)
    if old_equipped:
        if not old_equipped.get("slot"):
            old_equipped["slot"] = slot
        if not old_equipped.get("type"):
            old_equipped["type"] = slot
        inventory.append(old_equipped)

    equipment[slot] = item
    char.equipment = equipment
    char.inventory = inventory
    flag_modified(char, "equipment")
    flag_modified(char, "inventory")
    await session.commit()
    await session.refresh(char)
    return True, f"Предмет «{item['name']}» успешно надет!"


async def unequip_item_from_character(
    session: AsyncSession,
    char: RPGCharacter,
    slot_or_uid: str
) -> Tuple[bool, str]:
    """Unequips an item from character equipment slot back into inventory."""
    inventory = list(char.inventory or [])
    if len(inventory) >= 30:
        return False, "Инвентарь полон (максимум 30 слотов). Освободите место перед снятием!"

    equipment = dict(char.equipment or {})
    target_slot = None

    cleaned = slot_or_uid.strip().lower()
    if cleaned in ["weapon", "armor", "relic"]:
        target_slot = cleaned
    else:
        for s in ["weapon", "armor", "relic"]:
            if equipment.get(s) and (equipment[s].get("uid") == slot_or_uid or equipment[s].get("type") == slot_or_uid):
                target_slot = s
                break

    if not target_slot or not equipment.get(target_slot):
        return False, "В этом слоте нет надетого предмета."

    item = equipment.pop(target_slot)
    if not item.get("slot"):
        item["slot"] = target_slot
    if not item.get("type"):
        item["type"] = target_slot
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
    for s in ["weapon", "armor", "relic"]:
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


async def sell_item_from_inventory(
    session: AsyncSession,
    char: RPGCharacter,
    item_uid: str
) -> Tuple[bool, str, int]:
    """Sells an inventory item for gold."""
    inventory = list(char.inventory)
    target_idx = None
    for idx, it in enumerate(inventory):
        if it.get("uid") == item_uid:
            target_idx = idx
            break

    if target_idx is None:
        return False, "Предмет не найден в инвентаре.", 0

    item = inventory.pop(target_idx)
    rarity = item.get("rarity", "common")
    price = RARITY_MULTIPLIERS.get(rarity, {}).get("sell", 40)
    price += item.get("upgrade", 0) * 35

    char.gold += price
    char.inventory = inventory
    flag_modified(char, "inventory")
    await session.commit()
    await session.refresh(char)
    return True, f"Продано «{item['name']}» за +{price} 🪙", price


async def sell_multiple_items_from_inventory(
    session: AsyncSession,
    char: RPGCharacter,
    item_uids: list
) -> tuple[bool, str, int, int]:
    """Sells multiple items from inventory in a single atomic transaction."""
    if not item_uids:
        return False, "Не выбрано ни одного предмета для продажи.", 0, 0

    uid_set = set(str(u) for u in item_uids)
    inventory = list(char.inventory or [])
    sold_items = []
    remaining_inv = []
    total_gold = 0

    for it in inventory:
        it_uid = str(it.get("uid") or it.get("id") or "")
        if it_uid in uid_set:
            rarity = it.get("rarity", "common")
            price = RARITY_MULTIPLIERS.get(rarity, {}).get("sell", 40)
            price += it.get("upgrade", 0) * 35
            total_gold += price
            sold_items.append(it)
        else:
            remaining_inv.append(it)

    if not sold_items:
        return False, "Выбранные предметы не найдены в инвентаре.", 0, 0

    char.gold += total_gold
    char.inventory = remaining_inv
    flag_modified(char, "inventory")
    await session.commit()
    await session.refresh(char)

    return True, f"Продано {len(sold_items)} предметов за +{total_gold} 🪙!", total_gold, len(sold_items)


async def reset_rpg_character(
    session: AsyncSession,
    char: RPGCharacter
) -> tuple[bool, str]:
    """Hardcore Reset: Resets RPG character back to level 1 for a fresh grind!"""
    h_class = char.hero_class or "pudge"
    config = NATAR_HEROES.get(h_class, NATAR_HEROES["pudge"])

    char.level = 1
    char.xp = 0
    char.gold = 50
    char.gems = 5
    char.stat_points = 0
    char.strength = config["str"]
    char.agility = config["agi"]
    char.intelligence = config["int"]
    char.vitality = 10
    char.dungeon_floor = 1
    char.dungeon_cleared = 0
    char.boss_kills = 0

    starter_weapon = dict(config["starter_weapon"])
    starter_armor = dict(config["starter_armor"])
    starter_weapon["uid"] = str(uuid.uuid4())[:8]
    starter_armor["uid"] = str(uuid.uuid4())[:8]

    char.equipment = {
        "weapon": starter_weapon,
        "armor": starter_armor,
        "relic": None
    }
    char.inventory = [
        {
            "uid": str(uuid.uuid4())[:8],
            "name": "Зелье Исцеления",
            "icon": "🧪",
            "type": "potion",
            "slot": "consumable",
            "slot_name": "Зелье",
            "slot_icon": "🧪",
            "rarity": "common",
            "rarity_name": "Обычный",
            "rarity_color": "#94a3b8",
            "heal_hp": 120,
            "heal_mp": 30,
            "count": 2,
            "bonus_desc": "❤️ Восстанавливает 120 HP и 30 MP (2 шт.)"
        }
    ]
    flag_modified(char, "equipment")
    flag_modified(char, "inventory")
    await session.commit()
    await session.refresh(char)
    return True, "Герой успешно сброшен до 1 уровня! Начинается хардкорное приключение!"


# ==============================================================================
# NATARGRP SHOP (ТАЙНАЯ ЛАВКА СНАРЯЖЕНИЯ)
# ==============================================================================

NATAR_SHOP_CATALOG = [
    # --- НОВЫЕ АКТИВНЫЕ И ПАССИВНЫЕ АРТЕФАКТЫ DOTA 2 ---
    {
        "id": "shop_w_abyssal",
        "name": "Клинок Бездны (Abyssal Blade)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "price_gold": 4200,
        "price_gems": 12,
        "base_min": 75,
        "base_max": 110,
        "bonus": {"str": 25, "hp": 450, "dmg": 60, "abyssal_stun": 1, "bash": 25},
        "bonus_desc": "⚔️ +75..110 Урон | 🥩 +25 Сила | ❤️ +450 HP | ⚡ 25% Баш | 🌀 Активка: Стан на 2.5с"
    },
    {
        "id": "shop_r_hex",
        "name": "Коса Вайса (Scythe of Vyse / Хекс)",
        "icon": "🐑",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "price_gold": 4400,
        "price_gems": 14,
        "bonus": {"int": 35, "str": 12, "agi": 12, "mp_regen": 9, "spell_amp": 28, "hex": 1},
        "bonus_desc": "🔮 +35 Интеллект | 🌟 +12 Сила/Ловкость | 💧 +9 MP/сек | 🐑 Активка: Хекс (превращение в свинку на 3.5с)"
    },
    {
        "id": "shop_w_bloodthorn",
        "name": "Кровавый Шип (Bloodthorn)",
        "icon": "🌹",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "price_gold": 4500,
        "price_gems": 15,
        "base_min": 70,
        "base_max": 95,
        "bonus": {"int": 30, "atk_speed": 40, "spell_amp": 25, "bloodthorn_silence": 1},
        "bonus_desc": "⚔️ +70..95 Урон | 🔮 +30 Интеллект | ⚡ +40% Скор. атаки | 🩸 Активка: Безмолвие + 100% криты"
    },
    {
        "id": "shop_r_gleipnir",
        "name": "Глейпнир (Gleipnir)",
        "icon": "⛓️",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "price_gold": 4300,
        "price_gems": 12,
        "bonus": {"int": 24, "str": 14, "agi": 14, "lightning": 160, "gleipnir_root": 1},
        "bonus_desc": "🌟 +14..24 Характеристики | ⚡ Цепная молния 160 | ⛓️ Активка: Корни всей арены на 2.5с"
    },
    {
        "id": "shop_a_blademail",
        "name": "Шипастый Доспех (Blade Mail)",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "rare",
        "price_gold": 1800,
        "price_gems": 0,
        "defense": 16,
        "hp_bonus": 220,
        "bonus": {"atk": 28, "reflect": 100, "active_blademail": 1},
        "bonus_desc": "🛡️ +16 Броня | ❤️ +220 HP | ⚔️ +28 Урон | 🪞 Активка: Возвратка 100% входящего урона"
    },
    {
        "id": "shop_a_crimson",
        "name": "Багровая Защита (Crimson Guard)",
        "icon": "🔴",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "epic",
        "price_gold": 3200,
        "price_gems": 6,
        "defense": 22,
        "hp_bonus": 480,
        "bonus": {"str": 25, "hp_regen": 12, "damage_block": 85, "active_crimson": 1},
        "bonus_desc": "🛡️ +22 Броня | ❤️ +480 HP | 🥩 +25 Сила | 🔴 Активка: Купол блока 85 урона от каждой атаки"
    },
    {
        "id": "shop_r_pipe",
        "name": "Трубка Прозрения (Pipe of Insight)",
        "icon": "📯",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "price_gold": 3100,
        "price_gems": 5,
        "bonus": {"magic_resist": 30, "hp_regen": 10, "magic_shield": 650, "active_pipe": 1},
        "bonus_desc": "🔮 +30% Защита от магии | 💖 +10 HP/сек | 🛡️ Активка: Магический щит на 650 HP"
    },
    {
        "id": "shop_a_armlet",
        "name": "Арматура Мордиггиана (Armlet)",
        "icon": "🧤",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "rare",
        "price_gold": 2200,
        "price_gems": 0,
        "defense": 15,
        "hp_bonus": 280,
        "bonus": {"str": 15, "atk": 35, "unholy_strength": 1},
        "bonus_desc": "🛡️ +15 Броня | 🥩 +15 Сила | ⚔️ +35 Урон | 😈 Активка: Нечестивая сила (+40 Сила, +65 Урон)"
    },
    {
        "id": "shop_w_pike",
        "name": "Пика Урагана (Hurricane Pike)",
        "icon": "🔱",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "price_gold": 3400,
        "price_gems": 8,
        "base_min": 45,
        "base_max": 65,
        "bonus": {"agi": 24, "int": 18, "hp": 300, "active_pike": 1},
        "bonus_desc": "⚔️ +45..65 Урон | 🏃 +24 Ловкость | 🔮 +18 Интеллект | 💨 Активка: Отталкивание врагов на 130px"
    },
    {
        "id": "shop_w_silver",
        "name": "Серебряный Клинок (Silver Edge)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "price_gold": 4600,
        "price_gems": 16,
        "base_min": 68,
        "base_max": 92,
        "bonus": {"agi": 30, "atk_speed": 35, "crit": 25, "active_invis": 1},
        "bonus_desc": "⚔️ +68..92 Урон | 🏃 +30 Ловкость | ⚡ +35% Скорость | 👻 Активка: Теневой шаг + 250% крит из инвиза"
    },
    {
        "id": "shop_w_daedalus",
        "name": "Даэдалус (Daedalus)",
        "icon": "🏹",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "price_gold": 4300,
        "price_gems": 14,
        "base_min": 88,
        "base_max": 120,
        "bonus": {"crit_chance": 30, "crit_multiplier": 2.25},
        "bonus_desc": "⚔️ +88..120 Урон | 🎯 30% Шанс критического удара 225% урона"
    },
    {
        "id": "shop_w_bf",
        "name": "Боевой Топор (Battle Fury)",
        "icon": "🪓",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "legendary",
        "price_gold": 3800,
        "price_gems": 10,
        "base_min": 65,
        "base_max": 90,
        "bonus": {"hp_regen": 8, "mp_regen": 5, "cleave": 65},
        "bonus_desc": "⚔️ +65..90 Урон | 💖 +8 HP/сек | 🪓 65% Клив-урон по всем монстрам в радиусе"
    },
    {
        "id": "shop_w_radiance",
        "name": "Сияние (Radiance)",
        "icon": "☀️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "price_gold": 4800,
        "price_gems": 18,
        "base_min": 65,
        "base_max": 95,
        "bonus": {"radiance_burn": 60, "miss_aura": 17},
        "bonus_desc": "⚔️ +65..95 Урон | 🔥 Пылающая аура: 60 маг. урона/сек всей арене | 💨 Враги мажут на 17%"
    },
    {
        "id": "shop_w_desolator",
        "name": "Опустошитель (Desolator)",
        "icon": "🩸",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "legendary",
        "price_gold": 3500,
        "price_gems": 8,
        "base_min": 60,
        "base_max": 85,
        "bonus": {"minus_armor": 8},
        "bonus_desc": "⚔️ +60..85 Урон | 🩸 Коррозия: -8 брони врагам при ударах"
    },
    {
        "id": "shop_w_mkb",
        "name": "Посох Короля Обезьян (Monkey King Bar)",
        "icon": "🥢",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "price_gold": 4400,
        "price_gems": 14,
        "base_min": 55,
        "base_max": 80,
        "bonus": {"atk_speed": 35, "true_strike": 1, "pure_bonus": 75},
        "bonus_desc": "⚔️ +55..80 Урон | ⚡ +35% Скорость | 🎯 True Strike (удары без промахов) | 💥 +75 Чистый урон"
    },
    {
        "id": "shop_r_skadi",
        "name": "Око Скади (Eye of Skadi)",
        "icon": "❄️",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "price_gold": 4600,
        "price_gems": 15,
        "bonus": {"all_stats": 25, "hp": 550, "mp": 550, "frost_slow": 45},
        "bonus_desc": "🌟 +25 Все характеристики | ❤️ +550 HP | 💧 +550 MP | ❄️ Ледяной удар: -45% скорости врагов"
    },
    {
        "id": "shop_a_tarasque",
        "name": "Сердце Тарраски (Heart of Tarrasque)",
        "icon": "❤️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "immortal",
        "price_gold": 4500,
        "price_gems": 15,
        "defense": 25,
        "hp_bonus": 850,
        "bonus": {"str": 45, "pct_hp_regen": 2.5},
        "bonus_desc": "🛡️ +25 Броня | ❤️ +850 HP | 🥩 +45 Сила | 💖 Регенерация +2.5% от макс. HP в секунду"
    },
    {
        "id": "shop_r_bloodstone",
        "name": "Кровавый Камень (Bloodstone)",
        "icon": "🩸",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "immortal",
        "price_gold": 4400,
        "price_gems": 14,
        "bonus": {"hp": 600, "mp": 600, "spell_amp": 30, "spell_lifesteal": 30},
        "bonus_desc": "❤️ +600 HP | 💧 +600 MP | ✨ +30% Сила заклинаний | 🩸 30% Магический вампиризм от скиллов"
    },
    {
        "id": "shop_w_butterfly",
        "name": "Бабочка (Butterfly)",
        "icon": "🦋",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "price_gold": 4700,
        "price_gems": 16,
        "base_min": 50,
        "base_max": 75,
        "bonus": {"agi": 35, "dodge": 35, "atk_speed": 35},
        "bonus_desc": "⚔️ +50..75 Урон | 🏃 +35 Ловкость | 💨 +35% Уворот от ударов | ⚡ +35% Скорость атаки"
    },
    {
        "id": "shop_w_rapier",
        "name": "Божественная Рапира (Divine Rapier)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "immortal",
        "price_gold": 9000,
        "price_gems": 40,
        "base_min": 400,
        "base_max": 550,
        "bonus": {"true_strike": 1},
        "bonus_desc": "⚔️ +400..550 Колоссальный урон | 🎯 True Strike — абсолютное оружие богов"
    },

    # --- MAGE SHOP ARTIFACTS (ИНТЕЛЛЕКТ И СИЛА ЗАКЛИНАНИЙ) ---
    {
        "id": "shop_w_kaya",
        "name": "Кайя (Kaya)",
        "icon": "🪄",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "price_gold": 1400,
        "price_gems": 0,
        "base_min": 22,
        "base_max": 34,
        "bonus": {"int": 16, "mp": 150, "spell_amp": 12},
        "bonus_desc": "🔮 +16 Интеллект | 💧 +150 MP | ✨ +12% Сила заклинаний"
    },
    {
        "id": "shop_r_aether_lens",
        "name": "Линза Эфира (Aether Lens)",
        "icon": "🔮",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "price_gold": 1600,
        "price_gems": 0,
        "bonus": {"int": 15, "mp": 350, "spell_amp": 14},
        "bonus_desc": "🔮 +15 Интеллект | 💧 +350 MP | ✨ +14% Сила заклинаний"
    },
    {
        "id": "shop_r_dagon",
        "name": "Дагон I (Dagon I)",
        "icon": "⚡",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "price_gold": 1800,
        "price_gems": 0,
        "bonus": {"int": 16, "spell_amp": 15, "burst_magic": 150},
        "bonus_desc": "🔮 +16 Интеллект | ✨ +15% Сила заклинаний | ⚡ Энерго-разряд 150 ед."
    },
    {
        "id": "shop_r_eul",
        "name": "Скипетр Эула (Eul's Scepter)",
        "icon": "🌪️",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "price_gold": 1500,
        "price_gems": 0,
        "bonus": {"int": 18, "mp_regen": 6.0, "dodge": 8},
        "bonus_desc": "🔮 +18 Интеллект | 💧 +6 MP/сек | 💨 +8% Уворот"
    },
    {
        "id": "shop_r_shard",
        "name": "Осколок Аганима (Aghanim Shard)",
        "icon": "🔷",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "price_gold": 2200,
        "price_gems": 10,
        "bonus": {"all_stats": 10, "ult_boost": 25, "ult_cd": 15, "spell_amp": 10},
        "bonus_desc": "👑 +10 Все характеристики | 💥 +25% Урон Ульты | ⏱️ -15% КД Ульты"
    },
    {
        "id": "shop_r_octarine",
        "name": "Октариновое Ядро (Octarine Core)",
        "icon": "💎",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "price_gold": 3200,
        "price_gems": 25,
        "bonus": {"hp": 450, "mp": 750, "cooldown_reduct": 25, "spell_amp": 18, "int": 20},
        "bonus_desc": "❤️ +450 HP | 💧 +750 MP | ⏱️ -25% КД | 🔮 +20 Интеллект"
    },
    {
        "id": "shop_a_shiva",
        "name": "Страж Шивы (Shiva's Guard)",
        "icon": "❄️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "epic",
        "price_gold": 3100,
        "price_gems": 20,
        "base_def": 22,
        "base_hp": 300,
        "bonus": {"int": 35, "slow_aura": 30},
        "bonus_desc": "🛡️ +22 Броня | 🔮 +35 Интеллект | ❄️ Ледяное кольцо замедления"
    },

    # --- AGILITY SHOP ARTIFACTS (ЛОВКОСТЬ И СКОРОСТЬ) ---
    {
        "id": "shop_w_yasha",
        "name": "Яша (Yasha)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "price_gold": 1400,
        "price_gems": 0,
        "base_min": 24,
        "base_max": 36,
        "bonus": {"agi": 18, "atk_speed": 16, "dodge": 8},
        "bonus_desc": "🏃 +18 Ловкость | ⚡ +16% Скор. атаки | 💨 +8% Уворот"
    },
    {
        "id": "shop_w_diffusal",
        "name": "Диффуза (Diffusal Blade)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "price_gold": 1750,
        "price_gems": 0,
        "base_min": 28,
        "base_max": 42,
        "bonus": {"agi": 18, "mana_burn": 35},
        "bonus_desc": "🏃 +18 Ловкость | 💧 Сожжение 35 маны за удар"
    },
    {
        "id": "shop_w_butterfly",
        "name": "Бабочка (Butterfly)",
        "icon": "🦋",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "price_gold": 3400,
        "price_gems": 25,
        "base_min": 48,
        "base_max": 72,
        "bonus": {"agi": 40, "dodge": 35, "atk": 30},
        "bonus_desc": "🏃 +40 Ловкость | 💨 +35% Уворот | ⚔️ +30 Базовый урон"
    },
    {
        "id": "shop_w_manta",
        "name": "Манта Стайл (Manta Style)",
        "icon": "👥",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "price_gold": 3200,
        "price_gems": 20,
        "base_min": 44,
        "base_max": 66,
        "bonus": {"agi": 26, "str": 10, "int": 10, "atk_speed": 25, "dodge": 12},
        "bonus_desc": "🏃 +26 Ловкость | 👑 +10 Сила/Инт | ⚡ +25% Скор. атаки | 👥 Иллюзии"
    },
    {
        "id": "shop_w_daedalus",
        "name": "Дедал (Daedalus)",
        "icon": "🏹",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "epic",
        "price_gold": 3300,
        "price_gems": 20,
        "base_min": 85,
        "base_max": 125,
        "bonus": {"crit": 30},
        "bonus_desc": "⚔️ +85..125 Урон | 💥 +30% Шанс Крита (x2.25)"
    },

    # --- STRENGTH & DEFENSE SHOP ARTIFACTS (СИЛА И БРОНЯ) ---
    {
        "id": "shop_w_sange",
        "name": "Саша (Sange)",
        "icon": "🗡️",
        "type": "weapon",
        "slot": "weapon",
        "slot_name": "Оружие",
        "slot_icon": "⚔️",
        "rarity": "rare",
        "price_gold": 1400,
        "price_gems": 0,
        "base_min": 24,
        "base_max": 36,
        "bonus": {"str": 18, "hp": 200, "lifesteal": 8},
        "bonus_desc": "💪 +18 Сила | ❤️ +200 HP | 🧛 +8% Вампиризм"
    },
    {
        "id": "shop_a_blade_mail",
        "name": "Возвратный Доспех (Blade Mail)",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "rare",
        "price_gold": 1200,
        "price_gems": 0,
        "base_def": 10,
        "base_hp": 130,
        "bonus": {"reflect": 30, "atk": 16},
        "bonus_desc": "🛡️ +10 Броня | ⚔️ +16 Урон | 🦔 Отражение 30%"
    },
    {
        "id": "shop_a_heart_tarrasque",
        "name": "Сердце Тарраска (Heart of Tarrasque)",
        "icon": "❤️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "epic",
        "price_gold": 3300,
        "price_gems": 25,
        "base_def": 12,
        "base_hp": 750,
        "bonus": {"str": 45, "hp_regen_pct": 2},
        "bonus_desc": "💪 +45 Сила | ❤️ +750 HP | 💚 +2% Макс. HP/сек"
    },
    {
        "id": "shop_a_assault_cuirass",
        "name": "Кираса Штурма (Assault Cuirass)",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "epic",
        "price_gold": 2900,
        "price_gems": 20,
        "base_def": 24,
        "base_hp": 200,
        "bonus": {"atk_speed": 35, "aura_armor": 6},
        "bonus_desc": "🛡️ +24 Броня | ⚡ +35% Скор. атаки | 🛡️ +6 Аура брони"
    },
    {
        "id": "shop_a_forged_cuirass",
        "name": "Кованая Кираса Стража",
        "icon": "🛡️",
        "type": "armor",
        "slot": "armor",
        "slot_name": "Броня",
        "slot_icon": "🛡️",
        "rarity": "rare",
        "price_gold": 650,
        "price_gems": 4,
        "base_def": 14,
        "base_hp": 120,
        "bonus": {"defense": 5, "hp": 80},
        "bonus_desc": "🛡️ +14 Броня | ❤️ +120 HP"
    },
    {
        "id": "shop_r_blink_dagger",
        "name": "Кинжал Скачка (Blink Dagger)",
        "icon": "🗡️",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "rare",
        "price_gold": 1100,
        "price_gems": 8,
        "bonus": {"dodge": 12, "atk_speed": 10},
        "bonus_desc": "💨 +12% Уворот | ⚡ +10% Скор. атаки | ⚡ Мгновенный скачок"
    },
    {
        "id": "shop_r_satanic",
        "name": "Сатаник (Satanic)",
        "icon": "🩸",
        "type": "relic",
        "slot": "relic",
        "slot_name": "Реликвия",
        "slot_icon": "💍",
        "rarity": "epic",
        "price_gold": 3100,
        "price_gems": 25,
        "bonus": {"str": 25, "atk": 35, "lifesteal": 28},
        "bonus_desc": "💪 +25 Сила | ⚔️ +35 Урон | 🧛 +28% Вампиризм"
    },

    # --- CONSUMABLES (ЗЕЛЬЯ) ---
    {
        "id": "shop_p_healing",
        "name": "Зелье Исцеления",
        "icon": "🧴",
        "type": "potion",
        "slot": "consumable",
        "slot_name": "Зелье",
        "slot_icon": "🧪",
        "rarity": "common",
        "price_gold": 50,
        "price_gems": 0,
        "heal_amount": 120,
        "count": 3,
        "bonus_desc": "❤️ Восстанавливает 120 HP (3 шт.)"
    },
    {
        "id": "shop_p_mana",
        "name": "Эликсир Маны",
        "icon": "🧪",
        "type": "potion",
        "slot": "consumable",
        "slot_name": "Зелье",
        "slot_icon": "🧪",
        "rarity": "common",
        "price_gold": 40,
        "price_gems": 0,
        "mp_amount": 150,
        "count": 3,
        "bonus_desc": "🔮 Восстанавливает 150 MP (3 шт.)"
    },
    {
        "id": "shop_p_cheese",
        "name": "Сыр Силы Катакомб",
        "icon": "🧀",
        "type": "potion",
        "slot": "consumable",
        "slot_name": "Зелье",
        "slot_icon": "🧪",
        "rarity": "immortal",
        "price_gold": 450,
        "price_gems": 5,
        "heal_amount": 600,
        "mp_amount": 450,
        "count": 1,
        "bonus_desc": "👑 Восстанавливает 600 HP и 450 MP!"
    }
]

# Sync unique shop items into NATAR_ITEMS_CATALOG so reward chests and drops also contain them
_existing_item_names = {it.get("name") for it in NATAR_ITEMS_CATALOG}
for _shop_it in NATAR_SHOP_CATALOG:
    if _shop_it.get("type") in ("weapon", "armor", "relic") and _shop_it.get("name") not in _existing_item_names:
        _existing_item_names.add(_shop_it.get("name"))
        NATAR_ITEMS_CATALOG.append(dict(_shop_it))

def get_rpg_shop_catalog() -> List[Dict[str, Any]]:
    """Returns list of items available in the Secret Shop."""
    return list(NATAR_SHOP_CATALOG)


async def buy_item_from_shop(
    session: AsyncSession,
    char: RPGCharacter,
    item_id: str
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Buys an item or consumable from the Shop."""
    inventory = list(char.inventory or [])
    if len(inventory) >= 30:
        return False, "Инвентарь полон (максимум 30 слотов). Освободите место перед покупкой!", None

    shop_item = next((it for it in NATAR_SHOP_CATALOG if it["id"] == item_id), None)
    if not shop_item:
        return False, "Товар не найден в лавке.", None

    cost_gold = shop_item.get("price_gold", 0)
    cost_gems = shop_item.get("price_gems", 0)

    if char.gold < cost_gold:
        return False, f"Недостаточно золота! Нужно {cost_gold} 🪙 (у вас {char.gold} 🪙).", None
    if char.gems < cost_gems:
        return False, f"Недостаточно самоцветов! Нужно {cost_gems} 💎 (у вас {char.gems} 💎).", None

    char.gold -= cost_gold
    char.gems -= cost_gems

    new_item = dict(shop_item)
    new_item["uid"] = str(uuid.uuid4())[:8]
    new_item["upgrade"] = 0
    if "bonus" in shop_item:
        new_item["bonus"] = dict(shop_item["bonus"])

    rarity = new_item.get("rarity", "common")
    rarity_data = RARITY_MULTIPLIERS.get(rarity, RARITY_MULTIPLIERS["common"])
    new_item["rarity_color"] = rarity_data["color"]
    new_item["rarity_name"] = rarity_data["name"]
    new_item["bonus_desc"] = rebuild_item_description(new_item)

    if new_item.get("type") == "weapon":
        new_item["min_atk"] = new_item.get("base_min", 16)
        new_item["max_atk"] = new_item.get("base_max", 24)
    elif new_item.get("type") == "armor":
        new_item["defense"] = new_item.get("base_def", 10)
        new_item["hp_bonus"] = new_item.get("base_hp", 40)

    inventory.append(new_item)
    char.inventory = inventory
    flag_modified(char, "inventory")

    await session.commit()
    await session.refresh(char)
    return True, f"Куплено «{new_item['name']}» за {cost_gold} 🪙!", new_item


async def upgrade_character_base_stat(
    session: AsyncSession,
    char: RPGCharacter,
    stat_name: str
) -> Tuple[bool, str]:
    """
    Upgrades Strength, Agility or Intelligence.
    Priority: Spends free level-up stat_points first. If none, spends farmed gold.
    """
    STAT_ALIAS = {
        "str": "strength",
        "strength": "strength",
        "сила": "strength",
        "agi": "agility",
        "agility": "agility",
        "ловкость": "agility",
        "int": "intelligence",
        "intelligence": "intelligence",
        "интеллект": "intelligence",
        "vit": "strength",
        "vitality": "strength"
    }
    actual_stat = STAT_ALIAS.get(stat_name.strip().lower())
    if not actual_stat:
        return False, "Неверная характеристика. Выберите: Сила, Ловкость или Интеллект."

    current_val = getattr(char, actual_stat, 10)
    stat_points = getattr(char, "stat_points", 0)

    used_point = False
    if stat_points > 0:
        char.stat_points = stat_points - 1
        used_point = True
    else:
        cost = int(current_val * 20)
        if char.gold < cost:
            return False, f"Недостаточно золота! Нужно {cost} 🪙 (у вас {char.gold} 🪙) или очки характеристик."
        char.gold -= cost

    setattr(char, actual_stat, current_val + 1)
    if actual_stat == "strength":
        char.vitality = char.strength

    await session.commit()
    await session.refresh(char)

    stat_ru = {"strength": "Сила", "agility": "Ловкость", "intelligence": "Интеллект"}
    ru_name = stat_ru.get(actual_stat, actual_stat)
    if used_point:
        return True, f"Очко характеристики использовано! {ru_name} теперь {current_val + 1} (осталось очков: {char.stat_points})!"
    return True, f"Характеристика {ru_name} повышена до {current_val + 1} за золото!"


async def add_xp_and_gold_to_character(
    session: AsyncSession,
    char: RPGCharacter,
    xp_amount: int,
    gold_amount: int
) -> Tuple[bool, int]:
    """Awards gold, XP and handles Level-ups (+1 free stat point per level, steeper XP curve)."""
    char.gold += gold_amount
    char.xp += xp_amount
    leveled_up = False

    while True:
        needed = 120 + (char.level - 1) * 160
        if char.xp >= needed:
            char.xp -= needed
            char.level += 1
            char.stat_points = getattr(char, "stat_points", 0) + 1
            char.gems += 2
            leveled_up = True
        else:
            break

    await session.commit()
    await session.refresh(char)
    return leveled_up, char.level


# ==============================================================================
# LEADERBOARD
# ==============================================================================

async def get_rpg_leaderboard_data(session: AsyncSession) -> List[Dict[str, Any]]:
    """Returns class leaderboard ranked by PvP rating, dungeon floor and gear score."""
    stmt = (
        select(RPGCharacter, User)
        .join(User, RPGCharacter.user_id == User.id)
        .order_by(desc(RPGCharacter.pvp_rating), desc(RPGCharacter.level), desc(RPGCharacter.dungeon_floor))
        .limit(30)
    )
    res = await session.execute(stmt)
    rows = res.all()

    leaderboard = []
    for rank, (char, user) in enumerate(rows, 1):
        stats = calculate_character_effective_stats(char)
        cfg = NATAR_HEROES.get(char.hero_class, NATAR_HEROES["pudge"])
        leaderboard.append({
            "rank": rank,
            "user_id": user.id,
            "tg_id": user.tg_id,
            "name": user.display_name,
            "hero_class": char.hero_class,
            "class_name": cfg["name"],
            "class_icon": cfg["icon"],
            "class_avatar": cfg.get("avatar", "🗡️"),
            "level": char.level,
            "gear_score": stats["gear_score"],
            "pvp_rating": char.pvp_rating,
            "pvp_wins": char.pvp_wins,
            "dungeon_floor": char.dungeon_floor,
            "boss_kills": char.boss_kills
        })
    return leaderboard
