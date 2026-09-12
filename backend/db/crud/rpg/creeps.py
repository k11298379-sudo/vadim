from typing import Dict, Any, List

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
    {"name": "Мясник Катакомб", "icon": "🪝", "base_hp": 180000, "base_atk": 65, "base_def": 25, "gold": 220, "xp": 260},
    {"name": "Повелитель Теней", "icon": "💀", "base_hp": 260000, "base_atk": 80, "base_def": 30, "gold": 260, "xp": 310},
    {"name": "Древний Терзатель", "icon": "🔮", "base_hp": 380000, "base_atk": 98, "base_def": 35, "gold": 320, "xp": 380},
    {"name": "Дракон Инферно", "icon": "🐉", "base_hp": 540000, "base_atk": 120, "base_def": 42, "gold": 390, "xp": 460},
    {"name": "РОШАН СВИРЕПЫЙ (Roshan)", "icon": "🐲", "base_hp": 750000, "base_atk": 150, "base_def": 50, "gold": 480, "xp": 560},
    {"name": "Левиафан Бездны (Tidehunter)", "icon": "🐙", "base_hp": 1000000, "base_atk": 180, "base_def": 58, "gold": 580, "xp": 680},
    {"name": "Повелитель Душ (Nevermore)", "icon": "💀", "base_hp": 1300000, "base_atk": 220, "base_def": 65, "gold": 700, "xp": 820},
    {"name": "Чумной Владыка (Necrophos)", "icon": "🧟", "base_hp": 1700000, "base_atk": 260, "base_def": 72, "gold": 840, "xp": 980},
    {"name": "Демиург Арсенала (Invoker)", "icon": "🧙‍♂️", "base_hp": 2200000, "base_atk": 310, "base_def": 80, "gold": 1000, "xp": 1180},
    {"name": "Всадник Хаоса (Chaos Knight)", "icon": "🐎", "base_hp": 2800000, "base_atk": 365, "base_def": 90, "gold": 1200, "xp": 1400},
    {"name": "Тёмный Терзатель Бездны", "icon": "💎", "base_hp": 3500000, "base_atk": 425, "base_def": 100, "gold": 1450, "xp": 1680},
    {"name": "Вестник Апокалипсиса (Doom)", "icon": "👹", "base_hp": 4300000, "base_atk": 490, "base_def": 112, "gold": 1750, "xp": 2000},
    {"name": "Первобытный Титан (Primal Beast)", "icon": "🦣", "base_hp": 5200000, "base_atk": 560, "base_def": 125, "gold": 2100, "xp": 2400},
    {"name": "Призрачный Рошан Хаоса", "icon": "👻", "base_hp": 6300000, "base_atk": 640, "base_def": 140, "gold": 2500, "xp": 2850},
    {"name": "Пожиратель Миров (Enigma Cosmic)", "icon": "🌌", "base_hp": 7800000, "base_atk": 740, "base_def": 160, "gold": 3000, "xp": 3400}
]

# Backwards compat aliases
DOTA_CREEPS_POOL = NATAR_CREEPS_POOL
DOTA_FLOOR_BOSSES = NATAR_FLOOR_BOSSES
