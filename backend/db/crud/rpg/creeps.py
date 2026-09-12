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

# Backwards compat aliases
DOTA_CREEPS_POOL = NATAR_CREEPS_POOL
DOTA_FLOOR_BOSSES = NATAR_FLOOR_BOSSES
