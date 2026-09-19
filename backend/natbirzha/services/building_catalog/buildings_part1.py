from typing import Dict, Any

PART1_BUILDINGS: Dict[str, Dict[str, Any]] = {
    # ---------------- 1. АГРАРИЙ (agrarian) ----------------
    'farm_grain': {
        'id': 'farm_grain', 'name': '🌱 Зерновая ферма', 'specialization': 'agrarian',
        'category': 'extraction', 'level_required': 1, 'build_cost': 15000.0,
        'workers_required': 10, 'energy_required': 1, 'cycle_duration': 60,
        'description': 'Базовое аграрное сырьё: выращивание зерна',
        'inputs': {'water': 1.0, 'grid_quota': 1.0}, 'outputs': {'grain': 5.0},
        'recipe_id': 'farm_grain'
    },
    'livestock_complex': {
        'id': 'livestock_complex', 'name': '🐄 Животноводческий комплекс', 'specialization': 'agrarian',
        'category': 'processing', 'level_required': 2, 'build_cost': 30000.0,
        'workers_required': 20, 'energy_required': 2, 'cycle_duration': 90,
        'description': 'Производство мяса и молока на основе комбикорма',
        'inputs': {'feed': 2.0, 'water': 2.0, 'energy': 2.0}, 'outputs': {'meat': 2.0, 'milk': 4.0},
        'recipe_id': 'produce_livestock'
    },
    'feed_mill': {
        'id': 'feed_mill', 'name': '🌽 Комбикормовый завод', 'specialization': 'agrarian',
        'category': 'processing', 'level_required': 2, 'build_cost': 25000.0,
        'workers_required': 15, 'energy_required': 2, 'cycle_duration': 75,
        'description': 'Переработка зерна в питательный комбикорм',
        'inputs': {'grain': 3.0, 'energy': 2.0}, 'outputs': {'feed': 3.0},
        'recipe_id': 'produce_feed'
    },
    'food_factory': {
        'id': 'food_factory', 'name': '🥫 Пищевой комбинат', 'specialization': 'agrarian',
        'category': 'industry', 'level_required': 3, 'build_cost': 55000.0,
        'workers_required': 35, 'energy_required': 4, 'cycle_duration': 120,
        'description': 'Выпуск суточных продовольственных пайков',
        'inputs': {'flour': 2.0, 'meat': 1.5, 'energy': 4.0}, 'outputs': {'food': 3.0},
        'recipe_id': 'produce_rations'
    },
    'bio_farm': {
        'id': 'bio_farm', 'name': '🧬 Биоферма', 'specialization': 'agrarian',
        'category': 'hightech', 'level_required': 3, 'build_cost': 70000.0,
        'workers_required': 30, 'energy_required': 4, 'cycle_duration': 120,
        'description': 'Культивация растительного биосырья',
        'inputs': {'water': 3.0, 'grain': 2.0, 'energy': 4.0}, 'outputs': {'bio_raw': 4.0},
        'recipe_id': 'cultivate_bio'
    },
    'flour_mill': {
        'id': 'flour_mill', 'name': '🍞 Мукомольный завод', 'specialization': 'agrarian',
        'category': 'processing', 'level_required': 2, 'build_cost': 28000.0,
        'workers_required': 18, 'energy_required': 2, 'cycle_duration': 75,
        'description': 'Помол пшеничного зерна в муку высшего сорта',
        'inputs': {'grain': 3.0, 'energy': 2.0}, 'outputs': {'flour': 3.0},
        'recipe_id': 'mill_flour'
    },

    # ---------------- 2. ГОРНОДОБЫТЧИК (miner) ----------------
    'iron_mine': {
        'id': 'iron_mine', 'name': '⛏️ Железный рудник', 'specialization': 'miner',
        'category': 'extraction', 'level_required': 1, 'build_cost': 20000.0,
        'workers_required': 25, 'energy_required': 3, 'cycle_duration': 60,
        'description': 'Добыча товарной железной руды',
        'inputs': {'grid_quota': 1.0, 'water': 1.0}, 'outputs': {'iron_ore': 4.0},
        'recipe_id': 'mine_iron'
    },
    'coal_mine': {
        'id': 'coal_mine', 'name': '🪨 Угольный разрез', 'specialization': 'miner',
        'category': 'extraction', 'level_required': 1, 'build_cost': 22000.0,
        'workers_required': 25, 'energy_required': 3, 'cycle_duration': 60,
        'description': 'Добыча энергетического и коксующегося угля',
        'inputs': {'grid_quota': 1.0, 'water': 1.0}, 'outputs': {'coal': 5.0},
        'recipe_id': 'mine_coal'
    },
    'copper_mine': {
        'id': 'copper_mine', 'name': '🟠 Медный рудник', 'specialization': 'miner',
        'category': 'extraction', 'level_required': 2, 'build_cost': 35000.0,
        'workers_required': 30, 'energy_required': 4, 'cycle_duration': 90,
        'description': 'Добыча медной руды и первичной меди',
        'inputs': {'grid_quota': 1.5, 'water': 1.0}, 'outputs': {'copper': 3.0},
        'recipe_id': 'mine_copper'
    },
    'lithium_mine': {
        'id': 'lithium_mine', 'name': '💎 Глубокий рудник', 'specialization': 'miner',
        'category': 'extraction', 'level_required': 3, 'build_cost': 90000.0,
        'workers_required': 45, 'energy_required': 5, 'cycle_duration': 150,
        'description': 'Глубокая добыча неочищенного лития',
        'inputs': {'grid_quota': 2.0, 'water': 2.0}, 'outputs': {'lithium_raw': 2.0, 'cobalt_raw': 0.35},
        'recipe_id': 'mine_lithium', 'required_license': 'rare_mining'
    },
    'uranium_mine': {
        'id': 'uranium_mine', 'name': '☢️ Урановый рудник', 'specialization': 'miner',
        'category': 'hightech', 'level_required': 4, 'build_cost': 150000.0,
        'workers_required': 60, 'energy_required': 7, 'cycle_duration': 180,
        'description': 'Добыча природной урановой руды',
        'inputs': {'grid_quota': 2.0, 'water': 2.0}, 'outputs': {'uranium_raw': 1.5},
        'recipe_id': 'mine_uranium_raw'
    },
    'rare_earth_mine': {
        'id': 'rare_earth_mine', 'name': '✨ Редкоземельный рудник', 'specialization': 'miner',
        'category': 'hightech', 'level_required': 4, 'build_cost': 180000.0,
        'workers_required': 60, 'energy_required': 7, 'cycle_duration': 180,
        'description': 'Добыча редкоземельных металлов',
        'inputs': {'grid_quota': 2.0, 'water': 2.0}, 'outputs': {'rare_earths': 1.5, 'gallium_raw': 0.25},
        'recipe_id': 'mine_rare_earths', 'required_license': 'rare_mining'
    },

    # ---------------- 3. МЕТАЛЛУРГ (metallurgist) ----------------
    'steel_mill': {
        'id': 'steel_mill', 'name': '🔥 Металлургический комбинат', 'specialization': 'metallurgist',
        'category': 'processing', 'level_required': 1, 'build_cost': 20000.0,
        'workers_required': 35, 'energy_required': 4, 'cycle_duration': 60,
        'description': 'Выплавка стали из руды и угля',
        'inputs': {'iron_ore': 2.0, 'coal': 1.0, 'energy': 4.0}, 'outputs': {'steel': 1.5},
        'recipe_id': 'smelt_steel_mill'
    },
    'rolling_mill': {
        'id': 'rolling_mill', 'name': '🏗️ Прокатный завод', 'specialization': 'metallurgist',
        'category': 'industry', 'level_required': 2, 'build_cost': 40000.0,
        'workers_required': 30, 'energy_required': 4, 'cycle_duration': 90,
        'description': 'Горячий и холодный прокат стального листа',
        'inputs': {'steel': 2.0, 'energy': 4.0}, 'outputs': {'rolled_metal': 2.0},
        'recipe_id': 'roll_metal'
    },
    'metal_structures_factory': {
        'id': 'metal_structures_factory', 'name': '🔩 Завод металлоконструкций', 'specialization': 'metallurgist',
        'category': 'industry', 'level_required': 2, 'build_cost': 50000.0,
        'workers_required': 35, 'energy_required': 5, 'cycle_duration': 105,
        'description': 'Производство несущих строительных конструкций',
        'inputs': {'steel': 1.5, 'rolled_metal': 1.5, 'energy': 5.0}, 'outputs': {'metal_structures': 2.0},
        'recipe_id': 'produce_metal_structures'
    },
    'machine_factory': {
        'id': 'machine_factory', 'name': '⚙️ Машиностроительный цех', 'specialization': 'metallurgist',
        'category': 'industry', 'level_required': 3, 'build_cost': 90000.0,
        'workers_required': 45, 'energy_required': 6, 'cycle_duration': 150,
        'description': 'Сборка станков, узлов и оборудования',
        'inputs': {'components': 2.0, 'steel': 1.0, 'energy': 6.0}, 'outputs': {'machinery': 1.5},
        'recipe_id': 'assemble_machinery'
    },
    'auto_components_factory': {
        'id': 'auto_components_factory', 'name': '🚗 Завод автокомпонентов', 'specialization': 'metallurgist',
        'category': 'hightech', 'level_required': 3, 'build_cost': 110000.0,
        'workers_required': 50, 'energy_required': 6, 'cycle_duration': 150,
        'description': 'Изготовление автомобильных узлов и деталей',
        'inputs': {'steel': 1.5, 'plastics': 1.5, 'energy': 6.0}, 'outputs': {'auto_components': 2.0},
        'recipe_id': 'produce_auto_components'
    },
    'superalloy_factory': {
        'id': 'superalloy_factory', 'name': '🧪 Завод спецсплавов', 'specialization': 'metallurgist',
        'category': 'endgame', 'level_required': 4, 'build_cost': 220000.0,
        'workers_required': 65, 'energy_required': 8, 'cycle_duration': 210,
        'description': 'Сверхпрочные жаропрочные сплавы',
        'inputs': {'rare_earths': 1.0, 'steel': 1.0, 'energy': 8.0}, 'outputs': {'superalloy': 1.0},
        'recipe_id': 'smelt_superalloy'
    },

    # ---------------- 4. НЕФТЯНИК (oilman) ----------------
    'oil_rig': {
        'id': 'oil_rig', 'name': '🛢️ Нефтяная вышка', 'specialization': 'oilman',
        'category': 'extraction', 'level_required': 1, 'build_cost': 20000.0,
        'workers_required': 20, 'energy_required': 2, 'cycle_duration': 60,
        'description': 'Добыча сырой товарной нефти',
        'inputs': {'grid_quota': 1.0, 'water': 1.0}, 'outputs': {'oil_crude': 4.0},
        'recipe_id': 'pump_oil_crude'
    },
    'gas_field': {
        'id': 'gas_field', 'name': '🔥 Газовый промысел', 'specialization': 'oilman',
        'category': 'extraction', 'level_required': 2, 'build_cost': 40000.0,
        'workers_required': 30, 'energy_required': 3, 'cycle_duration': 90,
        'description': 'Добыча природного газа на промысле',
        'inputs': {'grid_quota': 1.5, 'water': 1.0}, 'outputs': {'gas_natural': 3.5},
        'recipe_id': 'pump_gas_field'
    },
    'refinery': {
        'id': 'refinery', 'name': '🏭 НПЗ', 'specialization': 'oilman',
        'category': 'processing', 'level_required': 2, 'build_cost': 60000.0,
        'workers_required': 40, 'energy_required': 5, 'cycle_duration': 120,
        'description': 'Глубокая переработка нефти в бензин и дизель',
        'inputs': {'oil_crude': 3.0, 'energy': 5.0}, 'outputs': {'gasoline': 50.0, 'fuel_diesel': 60.0},
        'recipe_id': 'refine_fuels'
    },
    'petrochemical_plant': {
        'id': 'petrochemical_plant', 'name': '🧪 Нефтехимический завод', 'specialization': 'oilman',
        'category': 'industry', 'level_required': 3, 'build_cost': 85000.0,
        'workers_required': 45, 'energy_required': 5, 'cycle_duration': 150,
        'description': 'Синтез полимеров из углеводородов',
        'inputs': {'oil_crude': 2.0, 'basic_chem': 1.5, 'energy': 5.0}, 'outputs': {'plastics': 2.5},
        'recipe_id': 'petrochem_polymers'
    },
    'jet_fuel_plant': {
        'id': 'jet_fuel_plant', 'name': '✈️ Завод авиакеросина', 'specialization': 'oilman',
        'category': 'hightech', 'level_required': 3, 'build_cost': 100000.0,
        'workers_required': 45, 'energy_required': 6, 'cycle_duration': 150,
        'description': 'Высокооктановое авиационное топливо',
        'inputs': {'oil_crude': 3.0, 'gas_natural': 1.0, 'energy': 6.0}, 'outputs': {'jet_fuel': 50.0},
        'recipe_id': 'produce_jet_fuel'
    },
    'plastics_factory': {
        'id': 'plastics_factory', 'name': '🧴 Завод пластмасс', 'specialization': 'oilman',
        'category': 'industry', 'level_required': 3, 'build_cost': 75000.0,
        'workers_required': 40, 'energy_required': 5, 'cycle_duration': 120,
        'description': 'Выпуск термопластов и изделий из пластмасс',
        'inputs': {'oil_crude': 2.5, 'energy': 5.0}, 'outputs': {'plastics': 2.0},
        'recipe_id': 'produce_plastics'
    },
}
