from typing import Dict, Any

PART2_BUILDINGS: Dict[str, Dict[str, Any]] = {
    # ---------------- 5. ЭНЕРГЕТИК (power_engineer) ----------------
    'solar_plant': {
        'id': 'solar_plant', 'name': '☀️ Солнечная электростанция', 'specialization': 'power_engineer',
        'category': 'extraction', 'level_required': 1, 'build_cost': 25000.0,
        'workers_required': 10, 'energy_required': 0, 'cycle_duration': 60,
        'description': 'Бестопливная фотоэлектрическая генерация',
        'inputs': {'grid_quota': 1.0}, 'outputs': {'energy': 15.0},
        'recipe_id': 'generate_solar'
    },
    'hydro_plant': {
        'id': 'hydro_plant', 'name': '🌊 ГЭС', 'specialization': 'power_engineer',
        'category': 'extraction', 'level_required': 1, 'build_cost': 40000.0,
        'workers_required': 15, 'energy_required': 0, 'cycle_duration': 60,
        'description': 'Стабильная гидрогенерация на водном потоке',
        'inputs': {'water': 3.0, 'grid_quota': 1.0}, 'outputs': {'energy': 22.0},
        'recipe_id': 'generate_hydro'
    },
    'thermal_power_plant': {
        'id': 'thermal_power_plant', 'name': '🔥 ТЭЦ', 'specialization': 'power_engineer',
        'category': 'processing', 'level_required': 2, 'build_cost': 60000.0,
        'workers_required': 35, 'energy_required': 0, 'cycle_duration': 90,
        'description': 'Тепловая электростанция на угле и воде',
        'inputs': {'coal': 2.0, 'water': 2.0}, 'outputs': {'energy': 35.0},
        'recipe_id': 'generate_thermal_plant'
    },
    'wind_farm': {
        'id': 'wind_farm', 'name': '💨 Ветропарк', 'specialization': 'power_engineer',
        'category': 'extraction', 'level_required': 2, 'build_cost': 45000.0,
        'workers_required': 12, 'energy_required': 0, 'cycle_duration': 60,
        'description': 'Ветропарк с низкими эксплуатационными затратами',
        'inputs': {'grid_quota': 1.5}, 'outputs': {'energy': 20.0},
        'recipe_id': 'generate_wind'
    },
    'nuclear_plant': {
        'id': 'nuclear_plant', 'name': '☢️ Атомная электростанция', 'specialization': 'power_engineer',
        'category': 'hightech', 'level_required': 4, 'build_cost': 250000.0,
        'workers_required': 80, 'energy_required': 0, 'cycle_duration': 180,
        'description': 'Огромная мощность на обогащённом уране',
        'inputs': {'uranium_raw': 1.5, 'water': 3.0}, 'outputs': {'energy': 150.0},
        'recipe_id': 'generate_nuclear_plant'
    },
    'fusion_plant': {
        'id': 'fusion_plant', 'name': '⚛️ Термоядерный комплекс', 'specialization': 'power_engineer',
        'category': 'endgame', 'level_required': 5, 'build_cost': 500000.0,
        'workers_required': 100, 'energy_required': 0, 'cycle_duration': 240,
        'description': 'Эндгейм-энергетика на термоядерном синтезе',
        'inputs': {'rare_earths': 1.5, 'water': 5.0, 'grid_quota': 3.0}, 'outputs': {'energy': 400.0},
        'recipe_id': 'generate_fusion'
    },

    # ---------------- 6. ЛЕСОПРОМЫШЛЕННИК (forester) ----------------
    'logging_camp': {
        'id': 'logging_camp', 'name': '🌲 Лесозаготовка', 'specialization': 'forester',
        'category': 'extraction', 'level_required': 1, 'build_cost': 18000.0,
        'workers_required': 20, 'energy_required': 0, 'cycle_duration': 60,
        'description': 'Заготовка деловой древесины по лесной квоте',
        'inputs': {'grid_quota': 1.0, 'water': 1.0}, 'outputs': {'wood_raw': 6.0},
        'recipe_id': 'log_timber_camp'
    },
    'sawmill': {
        'id': 'sawmill', 'name': '🪵 Лесопилка', 'specialization': 'forester',
        'category': 'processing', 'level_required': 2, 'build_cost': 30000.0,
        'workers_required': 25, 'energy_required': 3, 'cycle_duration': 90,
        'description': 'Распиловка круглого леса на обрезные пиломатериалы',
        'inputs': {'wood_raw': 4.0, 'energy': 3.0}, 'outputs': {'lumber': 3.0},
        'recipe_id': 'saw_lumber'
    },
    'pulp_mill': {
        'id': 'pulp_mill', 'name': '📄 Целлюлозный завод', 'specialization': 'forester',
        'category': 'processing', 'level_required': 2, 'build_cost': 45000.0,
        'workers_required': 30, 'energy_required': 4, 'cycle_duration': 105,
        'description': 'Варка древесной сульфатной целлюлозы',
        'inputs': {'wood_raw': 3.0, 'water': 2.0, 'energy': 4.0}, 'outputs': {'cellulose': 2.5},
        'recipe_id': 'produce_pulp'
    },
    'cardboard_factory': {
        'id': 'cardboard_factory', 'name': '📦 Картонный комбинат', 'specialization': 'forester',
        'category': 'industry', 'level_required': 3, 'build_cost': 55000.0,
        'workers_required': 35, 'energy_required': 4, 'cycle_duration': 120,
        'description': 'Производство упаковочного гофрокартона',
        'inputs': {'cellulose': 2.0, 'energy': 4.0}, 'outputs': {'cardboard': 3.0},
        'recipe_id': 'produce_cardboard'
    },
    'furniture_factory': {
        'id': 'furniture_factory', 'name': '🪑 Мебельная фабрика', 'specialization': 'forester',
        'category': 'industry', 'level_required': 3, 'build_cost': 75000.0,
        'workers_required': 45, 'energy_required': 5, 'cycle_duration': 150,
        'description': 'Сборка корпусной мебели из массива и полимеров',
        'inputs': {'lumber': 2.0, 'plastics': 1.0, 'energy': 5.0}, 'outputs': {'furniture': 2.0},
        'recipe_id': 'assemble_furniture'
    },
    'composite_factory': {
        'id': 'composite_factory', 'name': '🧱 Завод композитов', 'specialization': 'forester',
        'category': 'hightech', 'level_required': 4, 'build_cost': 120000.0,
        'workers_required': 55, 'energy_required': 6, 'cycle_duration': 180,
        'description': 'Древесно-полимерные сверхпрочные композиты',
        'inputs': {'wood_raw': 3.0, 'plastics': 2.0, 'energy': 6.0}, 'outputs': {'composite': 2.0},
        'recipe_id': 'produce_composite'
    },

    # ---------------- 7. ХИМИК (chemist) ----------------
    'chemical_plant': {
        'id': 'chemical_plant', 'name': '⚗️ Химзавод', 'specialization': 'chemist',
        'category': 'extraction', 'level_required': 1, 'build_cost': 25000.0,
        'workers_required': 30, 'energy_required': 4, 'cycle_duration': 60,
        'description': 'Базовый синтез кислот, щелочей и реагентов',
        'inputs': {'oil_crude': 1.5, 'water': 2.0, 'energy': 4.0}, 'outputs': {'basic_chem': 3.0},
        'recipe_id': 'chem_synth_base'
    },
    'fertilizer_plant': {
        'id': 'fertilizer_plant', 'name': '🌱 Завод удобрений', 'specialization': 'chemist',
        'category': 'processing', 'level_required': 2, 'build_cost': 40000.0,
        'workers_required': 30, 'energy_required': 4, 'cycle_duration': 90,
        'description': 'Азотные и комплексные удобрения для агрокомплекса',
        'inputs': {'basic_chem': 1.5, 'water': 2.0, 'energy': 4.0}, 'outputs': {'fertilizer': 3.0},
        'recipe_id': 'chem_fertilizers'
    },
    'polymer_factory': {
        'id': 'polymer_factory', 'name': '🧴 Полимерный завод', 'specialization': 'chemist',
        'category': 'processing', 'level_required': 2, 'build_cost': 55000.0,
        'workers_required': 35, 'energy_required': 4, 'cycle_duration': 105,
        'description': 'Каталитический синтез конструкционных полимеров',
        'inputs': {'oil_crude': 2.0, 'basic_chem': 1.0, 'energy': 4.0}, 'outputs': {'plastics': 3.0},
        'recipe_id': 'chem_polymers'
    },
    'electrolyte_factory': {
        'id': 'electrolyte_factory', 'name': '🔋 Завод электролитов', 'specialization': 'chemist',
        'category': 'industry', 'level_required': 3, 'build_cost': 70000.0,
        'workers_required': 35, 'energy_required': 5, 'cycle_duration': 120,
        'description': 'Электролиты высокой чистоты для тяговых батарей',
        'inputs': {'lithium_raw': 2.0, 'basic_chem': 1.0, 'energy': 5.0}, 'outputs': {'electrolyte': 2.0},
        'recipe_id': 'chem_electrolyte'
    },
    'biochem_factory': {
        'id': 'biochem_factory', 'name': '🧬 Биохимический комплекс', 'specialization': 'chemist',
        'category': 'hightech', 'level_required': 3, 'build_cost': 100000.0,
        'workers_required': 45, 'energy_required': 6, 'cycle_duration': 150,
        'description': 'Ферментные биореактивы высокой степени очистки',
        'inputs': {'bio_raw': 3.0, 'basic_chem': 1.0, 'energy': 6.0}, 'outputs': {'bioreagent': 2.0},
        'recipe_id': 'chem_bioreagents'
    },
    'catalyst_factory': {
        'id': 'catalyst_factory', 'name': '🧪 Завод катализаторов', 'specialization': 'chemist',
        'category': 'hightech', 'level_required': 4, 'build_cost': 140000.0,
        'workers_required': 55, 'energy_required': 7, 'cycle_duration': 180,
        'description': 'Специальные промышленные катализаторы',
        'inputs': {'rare_earths': 1.0, 'basic_chem': 2.0, 'energy': 7.0}, 'outputs': {'catalyst': 1.5},
        'recipe_id': 'chem_catalysts'
    },

    # ---------------- 8. ТЕХНОПРОМ (technoprom) ----------------
    'component_factory': {
        'id': 'component_factory', 'name': '🔧 Завод компонентов', 'specialization': 'technoprom',
        'category': 'extraction', 'level_required': 1, 'build_cost': 30000.0,
        'workers_required': 25, 'energy_required': 3, 'cycle_duration': 60,
        'description': 'Производство медных контактов и деталей',
        'inputs': {'copper': 1.5, 'plastics': 1.0, 'energy': 3.0}, 'outputs': {'components': 3.0},
        'recipe_id': 'tech_components'
    },
    'chip_factory': {
        'id': 'chip_factory', 'name': '💻 Микроэлектронный завод', 'specialization': 'technoprom',
        'category': 'processing', 'level_required': 2, 'build_cost': 80000.0,
        'workers_required': 40, 'energy_required': 5, 'cycle_duration': 120,
        'description': 'Литография кремниевых микрочипов',
        'inputs': {'components': 2.0, 'rare_earths': 0.5, 'energy': 5.0}, 'outputs': {'electronics': 2.0},
        'recipe_id': 'tech_chips'
    },
    'server_factory': {
        'id': 'server_factory', 'name': '🖥️ Серверный комплекс', 'specialization': 'technoprom',
        'category': 'industry', 'level_required': 3, 'build_cost': 120000.0,
        'workers_required': 50, 'energy_required': 7, 'cycle_duration': 150,
        'description': 'Высокопроизводительные серверные стойки',
        'inputs': {'electronics': 2.0, 'steel': 1.5, 'energy': 7.0}, 'outputs': {'servers': 1.5},
        'recipe_id': 'tech_servers'
    },
    'robot_factory': {
        'id': 'robot_factory', 'name': '🤖 Робототехнический завод', 'specialization': 'technoprom',
        'category': 'industry', 'level_required': 3, 'build_cost': 160000.0,
        'workers_required': 60, 'energy_required': 8, 'cycle_duration': 180,
        'description': 'Промышленные манипуляторы и роботы',
        'inputs': {'electronics': 1.5, 'machinery': 1.5, 'energy': 8.0}, 'outputs': {'robots': 1.0},
        'recipe_id': 'tech_robots'
    },
    'ai_factory': {
        'id': 'ai_factory', 'name': '🧠 AI-фабрика', 'specialization': 'technoprom',
        'category': 'hightech', 'level_required': 4, 'build_cost': 250000.0,
        'workers_required': 70, 'energy_required': 10, 'cycle_duration': 210,
        'description': 'Тензорные нейроускорители для ИИ',
        'inputs': {'electronics': 2.5, 'rare_earths': 1.0, 'energy': 10.0}, 'outputs': {'ai_accelerator': 1.0},
        'recipe_id': 'tech_ai'
    },
    'aerospace_complex': {
        'id': 'aerospace_complex', 'name': '🛰️ Аэрокосмический комплекс', 'specialization': 'technoprom',
        'category': 'endgame', 'level_required': 5, 'build_cost': 500000.0,
        'workers_required': 100, 'energy_required': 12, 'cycle_duration': 240,
        'description': 'Сборка спутников и аэрокосмических систем',
        'inputs': {'electronics': 2.0, 'superalloy': 1.0, 'machinery': 1.5, 'energy': 12.0},
        'outputs': {'aerospace_system': 1.0},
        'recipe_id': 'tech_aerospace'
    },
}
