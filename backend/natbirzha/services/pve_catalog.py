"""Versioned PvE corporation catalog for corporate territory wars."""

from types import MappingProxyType
from typing import Any, Mapping


PVE_CATALOG_VERSION = "p2-v1"


def _target(
    code: str,
    name: str,
    industry: str,
    tier: int,
    units: dict[str, int],
    *,
    prerequisite: str | None = None,
    territory: int = 1,
    cash: float = 0.0,
    xp: int = 0,
    resources: dict[str, float] | None = None,
    premium: dict[str, float] | None = None,
) -> Mapping[str, Any]:
    return MappingProxyType(
        {
            "code": code,
            "name": name,
            "industry": industry,
            "tier": tier,
            "min_company_level": tier,
            "prerequisite_code": prerequisite,
            "unit_snapshot": units,
            "premium_modifiers": premium or {},
            "territory_reward": territory,
            "cash_reward": cash,
            "xp_reward": xp,
            "resource_rewards": resources or {},
        }
    )


PVE_CORPORATIONS: tuple[Mapping[str, Any], ...] = (
    _target("local_logistics", "Локальная логистика", "logistics", 1,
            {"infantry": 25, "border_guards": 5}, cash=2_500, xp=60,
            resources={"military_gear": 1}),
    _target("forest_contractor", "Лесной подрядчик", "forestry", 1,
            {"infantry": 32, "drones": 1}, cash=3_000, xp=70,
            resources={"wood_raw": 15}),
    _target("municipal_depot", "Муниципальная база", "construction", 1,
            {"infantry": 28, "border_guards": 12}, cash=3_500, xp=80,
            resources={"steel": 3}),
    _target("coal_combine", "Угольный комбинат", "mining", 2,
            {"infantry": 70, "border_guards": 20, "tanks": 2},
            prerequisite="local_logistics", cash=7_500, xp=160, resources={"coal": 25}),
    _target("river_port", "Речной грузовой порт", "logistics", 2,
            {"infantry": 85, "tanks": 2, "drones": 3},
            prerequisite="forest_contractor", cash=8_000, xp=170, resources={"fuel_diesel": 30}),
    _target("steel_syndicate", "Стальной синдикат", "metallurgy", 2,
            {"infantry": 60, "border_guards": 35, "tanks": 3},
            prerequisite="municipal_depot", cash=9_000, xp=180, resources={"steel": 12}),
    _target("energy_concern", "Энергетический концерн", "energy", 3,
            {"infantry": 130, "tanks": 7, "drones": 6, "air_defense": 2},
            prerequisite="coal_combine", territory=2, cash=18_000, xp=320,
            resources={"energy": 120}),
    _target("petrochemical_group", "Нефтехимическая группа", "oil_gas", 3,
            {"infantry": 150, "border_guards": 45, "tanks": 6, "aircraft": 1},
            prerequisite="river_port", territory=2, cash=20_000, xp=340,
            resources={"jet_fuel": 40}),
    _target("electronics_holding", "Электронный холдинг", "technology", 3,
            {"infantry": 110, "tanks": 5, "drones": 12, "air_defense": 4},
            prerequisite="steel_syndicate", territory=2, cash=22_000, xp=360,
            resources={"electronics": 8}),
    _target("continental_defense", "Континентальная оборона", "defense", 4,
            {"infantry": 260, "border_guards": 100, "tanks": 16, "drones": 15,
             "aircraft": 5, "air_defense": 8}, prerequisite="energy_concern",
            territory=3, cash=45_000, xp=650, resources={"military_gear": 25},
            premium={"defense": 0.05}),
    _target("aerospace_union", "Аэрокосмический союз", "aerospace", 4,
            {"infantry": 220, "tanks": 14, "drones": 25, "aircraft": 9,
             "air_defense": 6}, prerequisite="petrochemical_group",
            territory=3, cash=50_000, xp=700, resources={"aerospace_system": 2},
            premium={"air": 0.08}),
    _target("quantum_industries", "Квантовые индустрии", "technology", 4,
            {"infantry": 210, "border_guards": 80, "tanks": 12, "drones": 30,
             "aircraft": 7, "air_defense": 10}, prerequisite="electronics_holding",
            territory=3, cash=55_000, xp=750, resources={"ai_accelerator": 2},
            premium={"recon": 0.08, "defense": 0.05}),
)

