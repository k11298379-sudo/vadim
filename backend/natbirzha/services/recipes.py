from typing import Dict, Any, List

# Production Recipes for all 8 Specializations
# Strictly verified Directed Acyclic Graph (DAG) with zero cycles.
# Tier 0 (Municipal Grid Quota / Water) 
# -> Tier 1 (Primary Extraction: Farm, Mine, Logging, Oil Rig) 
# -> Tier 2 (Energy Generation & Basic Processing: Power Plants, Smelters, Sawmill, Refinery, Chem Plant) 
# -> Tier 3 (Advanced Manufacturing: Polymers, Centrifuge, Machinery, Electronics) 
# -> Tier 4 (Military VPK: Defense Plant)

RECIPES: Dict[str, Dict[str, Any]] = {
    # 1. АГРАРИЙ (Agrarian)
    "farm_grain": {
        "factory_type": "farm",
        "specialization": "agrarian",
        "level_req": 1,
        "name": "Выращивание зерна",
        "inputs": {"water": 1.0, "grid_quota": 1.0},
        "outputs": {"grain": 5.0, "bio_raw": 2.0},
        "base_duration": 60,
    },
    "food_processing": {
        "factory_type": "food_factory",
        "specialization": "agrarian",
        "level_req": 2,
        "name": "Производство продовольствия",
        "inputs": {"grain": 3.0, "water": 1.0, "energy": 1.5},
        "outputs": {"food": 2.0},
        "base_duration": 60,
    },

    # 2. ГОРНОДОБЫТЧИК (Miner)
    "mine_coal_iron": {
        "factory_type": "mine",
        "specialization": "miner",
        "level_req": 1,
        "name": "Добыча угля и железной руды",
        "inputs": {"grid_quota": 2.0, "water": 1.0},
        "outputs": {"coal": 4.0, "iron_ore": 3.0, "minerals": 2.0},
        "base_duration": 60,
    },
    "mine_rare_lithium": {
        "factory_type": "deep_mine",
        "specialization": "miner",
        "level_req": 2,
        "name": "Добыча лития и редкоземов",
        "inputs": {"grid_quota": 2.5, "water": 1.5},
        "outputs": {"lithium_raw": 1.5, "rare_earths": 1.0, "bauxite": 2.0},
        "base_duration": 60,
    },
    "mine_uranium": {
        "factory_type": "uranium_quarry",
        "specialization": "miner",
        "level_req": 3,
        "name": "Добыча урановой руды",
        "inputs": {"grid_quota": 3.0, "water": 2.0},
        "outputs": {"uranium_raw": 1.0},
        "base_duration": 60,
    },

    # 3. ЛЕСОПРОМЫШЛЕННИК (Forester)
    "log_timber": {
        "factory_type": "logging_camp",
        "specialization": "forester",
        "level_req": 1,
        "name": "Лесозаготовка",
        "inputs": {"grid_quota": 1.5},
        "outputs": {"wood_raw": 5.0},
        "base_duration": 60,
    },
    "mill_lumber": {
        "factory_type": "sawmill",
        "specialization": "forester",
        "level_req": 2,
        "name": "Производство пиломатериалов",
        "inputs": {"wood_raw": 3.0, "energy": 1.5},
        "outputs": {"lumber": 2.0, "cellulose": 1.0},
        "base_duration": 60,
    },

    # 4. НЕФТЯНИК (Oilman)
    "pump_oil_gas": {
        "factory_type": "oil_rig",
        "specialization": "oilman",
        "level_req": 1,
        "name": "Добыча сырой нефти и газа",
        "inputs": {"grid_quota": 2.0, "water": 1.0},
        "outputs": {"oil_crude": 3.0, "gas_natural": 2.0},
        "base_duration": 60,
    },
    "refine_fuel": {
        "factory_type": "refinery",
        "specialization": "oilman",
        "level_req": 2,
        "name": "Переработка топлива",
        "inputs": {"oil_crude": 2.0, "energy": 2.0},
        "outputs": {"fuel_diesel": 80.0},
        "base_duration": 60,
    },

    # 5. ЭНЕРГЕТИК (Power Engineer - ключевой поставщик товарной энергии)
    "generate_solar_hydro": {
        "factory_type": "hydro_solar",
        "specialization": "power_engineer",
        "level_req": 1,
        "name": "Бестопливная генерация (ВИЭ/ГЭС)",
        "inputs": {},  # Pure Tier 0 breaker: zero fuel
        "outputs": {"energy": 15.0},
        "base_duration": 60,
    },
    "generate_thermal": {
        "factory_type": "thermal_plant",
        "specialization": "power_engineer",
        "level_req": 1,
        "name": "Угольная ТЭС",
        "inputs": {"coal": 2.0, "water": 1.0},
        "outputs": {"energy": 25.0},
        "base_duration": 60,
    },
    "generate_nuclear": {
        "factory_type": "nuclear_plant",
        "specialization": "power_engineer",
        "level_req": 3,
        "name": "Атомная электростанция (АЭС)",
        "inputs": {"uranium_enriched": 1.0, "water": 3.0},
        "outputs": {"energy": 120.0},
        "base_duration": 60,
    },

    # 6. МЕТАЛЛУРГ (Metallurgist)
    "smelt_steel": {
        "factory_type": "smelter",
        "specialization": "metallurgist",
        "level_req": 1,
        "name": "Выплавка конструкционной стали",
        "inputs": {"iron_ore": 2.0, "coal": 1.0, "energy": 2.0},
        "outputs": {"steel": 1.0},
        "base_duration": 60,
    },
    "smelt_aluminum": {
        "factory_type": "aluminum_plant",
        "specialization": "metallurgist",
        "level_req": 2,
        "name": "Электролиз алюминия",
        "inputs": {"bauxite": 2.0, "minerals": 1.0, "energy": 3.5},
        "outputs": {"aluminum": 1.0},
        "base_duration": 60,
    },

    # 7. ХИМИК (Chemist)
    "synth_chem_fertilizer": {
        "factory_type": "chem_plant",
        "specialization": "chemist",
        "level_req": 1,
        "name": "Синтез кислот и удобрений",
        "inputs": {"minerals": 1.5, "water": 1.5, "energy": 2.0},
        "outputs": {"basic_chem": 2.0, "fertilizer": 2.0},
        "base_duration": 60,
    },
    "polymer_synthesis": {
        "factory_type": "polymer_plant",
        "specialization": "chemist",
        "level_req": 2,
        "name": "Синтез полимеров и катализаторов",
        "inputs": {"gas_natural": 1.5, "basic_chem": 1.0, "energy": 2.5},
        "outputs": {"plastics": 1.5, "catalyst": 0.5},
        "base_duration": 60,
    },

    # 8. ТЕХНОПРОМ (High-Tech / Manufacturing)
    "enrich_uranium": {
        "factory_type": "centrifuge",
        "specialization": "technoprom",
        "level_req": 3,
        "name": "Обогащение урана",
        "inputs": {"uranium_raw": 2.0, "minerals": 1.0, "grid_quota": 3.0},
        "outputs": {"uranium_enriched": 1.0},
        "base_duration": 60,
    },
    "manufacture_machinery": {
        "factory_type": "machinery_plant",
        "specialization": "technoprom",
        "level_req": 1,
        "name": "Производство станков и узлов",
        "inputs": {"steel": 1.5, "energy": 2.0},
        "outputs": {"machinery": 1.0},
        "base_duration": 60,
    },
    "manufacture_electronics": {
        "factory_type": "electronics_fab",
        "specialization": "technoprom",
        "level_req": 2,
        "name": "Производство чипов и батарей",
        "inputs": {"rare_earths": 0.5, "lithium_raw": 1.0, "plastics": 1.0, "energy": 3.0},
        "outputs": {"electronics": 1.0, "batteries": 1.0},
        "base_duration": 60,
    },
    "assemble_military_gear": {
        "factory_type": "defense_plant",
        "specialization": "technoprom",
        "level_req": 2,
        "name": "Производство военной техники и снаряжения",
        "inputs": {"steel": 2.0, "machinery": 1.0, "electronics": 1.0, "energy": 3.0},
        "outputs": {"military_gear": 1.0},
        "base_duration": 60,
    },
}

def validate_recipe_dag() -> bool:
    """
    Verifies that RECIPES form a Directed Acyclic Graph (DAG) with zero cycles.
    Returns True if valid DAG, raises ValueError if any cycle exists.
    """
    graph: Dict[str, set] = {}
    for r_id, r in RECIPES.items():
        inputs = set(r["inputs"].keys())
        for out in r["outputs"].keys():
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
