from typing import Dict, Any, Optional
from backend.natbirzha.services.building_catalog import CANONICAL_BUILDINGS

# Production Recipes for all 8 Specializations and 48 Enterprises
# Strictly verified Directed Acyclic Graph (DAG) with zero cycles.

LEGACY_RECIPES: Dict[str, Dict[str, Any]] = {
    'food_processing': {
        'recipe_id': 'food_processing', 'factory_type': 'food_factory', 'specialization': 'agrarian', 'level_req': 2,
        'name': 'Производство продовольствия (legacy)',
        'inputs': {'grain': 3.0, 'water': 1.0, 'energy': 1.5}, 'outputs': {'food': 2.0}, 'base_duration': 60
    },
    'mine_coal_iron': {
        'recipe_id': 'mine_coal_iron', 'factory_type': 'iron_mine', 'specialization': 'miner', 'level_req': 1,
        'name': 'Добыча угля и железной руды (legacy)',
        'inputs': {'grid_quota': 2.0, 'water': 1.0}, 'outputs': {'coal': 4.0, 'iron_ore': 3.0}, 'base_duration': 60
    },
    'mine_rare_lithium': {
        'recipe_id': 'mine_rare_lithium', 'factory_type': 'lithium_mine', 'specialization': 'miner', 'level_req': 2,
        'name': 'Добыча лития и редкоземов (legacy)',
        'inputs': {'grid_quota': 2.5, 'water': 1.5}, 'outputs': {'lithium_raw': 1.5, 'rare_earths': 1.0}, 'base_duration': 60
    },
    'mine_uranium': {
        'recipe_id': 'mine_uranium', 'factory_type': 'uranium_mine', 'specialization': 'miner', 'level_req': 3,
        'name': 'Добыча урановой руды (legacy)',
        'inputs': {'grid_quota': 3.0, 'water': 2.0}, 'outputs': {'uranium_raw': 1.0}, 'base_duration': 60
    },
    'log_timber': {
        'recipe_id': 'log_timber', 'factory_type': 'logging_camp', 'specialization': 'forester', 'level_req': 1,
        'name': 'Лесозаготовка (legacy)',
        'inputs': {'grid_quota': 1.5}, 'outputs': {'wood_raw': 5.0}, 'base_duration': 60
    },
    'mill_lumber': {
        'recipe_id': 'mill_lumber', 'factory_type': 'sawmill', 'specialization': 'forester', 'level_req': 2,
        'name': 'Производство пиломатериалов (legacy)',
        'inputs': {'wood_raw': 3.0, 'energy': 1.5}, 'outputs': {'lumber': 2.0, 'cellulose': 1.0}, 'base_duration': 60
    },
    'pump_oil_gas': {
        'recipe_id': 'pump_oil_gas', 'factory_type': 'oil_rig', 'specialization': 'oilman', 'level_req': 1,
        'name': 'Добыча сырой нефти и газа (legacy)',
        'inputs': {'grid_quota': 2.0, 'water': 1.0}, 'outputs': {'oil_crude': 3.0, 'gas_natural': 2.0}, 'base_duration': 60
    },
    'refine_fuel': {
        'recipe_id': 'refine_fuel', 'factory_type': 'refinery', 'specialization': 'oilman', 'level_req': 2,
        'name': 'Переработка топлива (legacy)',
        'inputs': {'oil_crude': 2.0, 'energy': 2.0}, 'outputs': {'fuel_diesel': 80.0}, 'base_duration': 60
    },
    'generate_solar_hydro': {
        'recipe_id': 'generate_solar_hydro', 'factory_type': 'solar_plant', 'specialization': 'power_engineer', 'level_req': 1,
        'name': 'Бестопливная генерация (legacy)',
        'inputs': {'grid_quota': 1.0}, 'outputs': {'energy': 15.0}, 'base_duration': 60
    },
    'generate_thermal': {
        'recipe_id': 'generate_thermal', 'factory_type': 'thermal_power_plant', 'specialization': 'power_engineer', 'level_req': 1,
        'name': 'Угольная ТЭС (legacy)',
        'inputs': {'coal': 2.0, 'water': 1.0}, 'outputs': {'energy': 25.0}, 'base_duration': 60
    },
    'generate_nuclear': {
        'recipe_id': 'generate_nuclear', 'factory_type': 'nuclear_plant', 'specialization': 'power_engineer', 'level_req': 3,
        'name': 'Атомная электростанция (legacy)',
        'inputs': {'uranium_raw': 1.0, 'water': 3.0}, 'outputs': {'energy': 120.0}, 'base_duration': 60
    },
    'smelt_steel': {
        'recipe_id': 'smelt_steel', 'factory_type': 'steel_mill', 'specialization': 'metallurgist', 'level_req': 1,
        'name': 'Выплавка стали (legacy)',
        'inputs': {'iron_ore': 2.0, 'coal': 1.0, 'energy': 2.0}, 'outputs': {'steel': 1.0}, 'base_duration': 60
    },
    'smelt_aluminum': {
        'recipe_id': 'smelt_aluminum', 'factory_type': 'steel_mill', 'specialization': 'metallurgist', 'level_req': 2,
        'name': 'Электролиз алюминия (legacy)',
        'inputs': {'rare_earths': 1.0, 'energy': 3.5}, 'outputs': {'rolled_metal': 1.0}, 'base_duration': 60
    },
    'synth_chem_fertilizer': {
        'recipe_id': 'synth_chem_fertilizer', 'factory_type': 'chemical_plant', 'specialization': 'chemist', 'level_req': 1,
        'name': 'Синтез кислот и удобрений (legacy)',
        'inputs': {'water': 1.5, 'oil_crude': 1.0, 'energy': 2.0}, 'outputs': {'basic_chem': 2.0, 'fertilizer': 2.0}, 'base_duration': 60
    },
    'polymer_synthesis': {
        'recipe_id': 'polymer_synthesis', 'factory_type': 'polymer_factory', 'specialization': 'chemist', 'level_req': 2,
        'name': 'Синтез полимеров (legacy)',
        'inputs': {'gas_natural': 1.5, 'basic_chem': 1.0, 'energy': 2.5}, 'outputs': {'plastics': 1.5}, 'base_duration': 60
    },
    'enrich_uranium': {
        'recipe_id': 'enrich_uranium', 'factory_type': 'nuclear_plant', 'specialization': 'technoprom', 'level_req': 3,
        'name': 'Обогащение урана (legacy)',
        'inputs': {'uranium_raw': 2.0, 'grid_quota': 3.0}, 'outputs': {'uranium_enriched': 1.0}, 'base_duration': 60
    },
    'manufacture_machinery': {
        'recipe_id': 'manufacture_machinery', 'factory_type': 'machine_factory', 'specialization': 'technoprom', 'level_req': 1,
        'name': 'Производство станков (legacy)',
        'inputs': {'steel': 1.5, 'energy': 2.0}, 'outputs': {'machinery': 1.0}, 'base_duration': 60
    },
    'manufacture_electronics': {
        'recipe_id': 'manufacture_electronics', 'factory_type': 'chip_factory', 'specialization': 'technoprom', 'level_req': 2,
        'name': 'Производство чипов (legacy)',
        'inputs': {'rare_earths': 0.5, 'lithium_raw': 1.0, 'plastics': 1.0, 'energy': 3.0}, 'outputs': {'electronics': 1.0}, 'base_duration': 60
    },
    'assemble_military_gear': {
        'recipe_id': 'assemble_military_gear', 'factory_type': 'machine_factory', 'specialization': 'technoprom', 'level_req': 2,
        'name': 'Производство военной техники (legacy)',
        'inputs': {'steel': 2.0, 'machinery': 1.0, 'electronics': 1.0, 'energy': 3.0}, 'outputs': {'superalloy': 1.0}, 'base_duration': 60
    },
}

def _build_recipes() -> Dict[str, Dict[str, Any]]:
    recipes: Dict[str, Dict[str, Any]] = dict(LEGACY_RECIPES)
    for b_id, b in CANONICAL_BUILDINGS.items():
        r_id = b.get('recipe_id', b_id)
        spec = {
            'recipe_id': r_id,
            'factory_type': b['id'],
            'specialization': b['specialization'],
            'level_req': b['level_required'],
            'name': b['name'],
            'inputs': dict(b['inputs']),
            'outputs': dict(b['outputs']),
            'base_duration': b['cycle_duration'],
            'duration': b['cycle_duration'],
            'energy_cost': b['energy_required'],
            'labor_demand': b['workers_required'],
            'unlock_level': b['level_required'],
        }
        recipes[r_id] = spec
        if b_id not in recipes:
            recipes[b_id] = spec
    return recipes

RECIPES: Dict[str, Dict[str, Any]] = _build_recipes()

def get_recipe(recipe_id: str) -> Optional[Dict[str, Any]]:
    return RECIPES.get(recipe_id)

def validate_recipe_dag() -> bool:
    """
    Verifies that RECIPES form a Directed Acyclic Graph (DAG) with zero cycles.
    Returns True if valid DAG, raises ValueError if any cycle exists.
    """
    graph: Dict[str, set] = {}
    for r_id, r in RECIPES.items():
        inputs = set(r.get("inputs", {}).keys())
        for out in r.get("outputs", {}).keys():
            if out not in graph:
                graph[out] = set()
            graph[out].update(inputs)

    visited = set()
    rec_stack = set()

    def has_cycle(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if has_cycle(node):
                raise ValueError(f"Cycle detected in production graph around node {node}!")

    return True

__all__ = [
    'RECIPES',
    'LEGACY_RECIPES',
    'get_recipe',
    'validate_recipe_dag'
]
